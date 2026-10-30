"""Deployment settings.

Addresses and credentials come from the environment (`.env`); behaviour that varies per deployment
(model capability profiles, limits, backend contract paths, timeouts) comes from the YAML file named
by `ARIA_CONFIG_FILE`. Nothing deployment-specific is written in code.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field, SecretStr, ValidationError, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

DEFAULT_ENV_FILE = Path(".env")

ModelRoleName = Literal["tool", "synthesis"]


class ConfigError(Exception):
    """Configuration is missing or inconsistent. Messages never include configured values."""

    def __init__(self, problems: list[str]):
        self.problems = problems
        super().__init__("; ".join(problems))


class EnvSettings(BaseSettings):
    """Values read from the environment and `.env`."""

    # `model_name` is a deployment key, not a pydantic internal.
    model_config = SettingsConfigDict(extra="ignore", protected_namespaces=())

    host: str = "0.0.0.0"
    port: int = 8002
    log_level: str = "INFO"
    aria_config_file: Path = Path("config/aria.yaml")

    spring_boot_base_url: str

    openai_api_base: str
    openai_api_key: SecretStr | None = None
    model_name: str
    model_native_api_base: str | None = None

    general_openai_api_base: str
    general_openai_api_key: SecretStr | None = None
    general_model_name: str
    general_model_native_api_base: str | None = None

    embedding_api_base: str | None = None
    embedding_api_key: SecretStr | None = None
    embedding_model_name: str | None = None

    rag_service_url: str | None = None
    ner_service_url: str | None = None
    cross_encoder_host: str | None = None
    cross_encoder_port: int | None = None

    redis_host: str | None = None
    redis_port: int | None = None
    redis_password: SecretStr | None = None

    chats_db_host: str | None = None
    chats_db_port: int | None = None
    chats_db_name: str | None = None
    chats_db_user: str | None = None
    chats_db_password: SecretStr | None = None

    prompts_db_host: str | None = None
    prompts_db_port: int | None = None
    prompts_db_name: str | None = None
    prompts_db_user: str | None = None
    prompts_db_password: SecretStr | None = None

    aria_response_validation_enabled: bool = False


class ModelProfile(BaseModel):
    """What one deployed model can do. Code adapts to these numbers instead of to model names."""

    model_config = ConfigDict(extra="forbid")

    # Only providers whose API accepts a per-request context length are supported, so that prompts
    # are never silently truncated by the host.
    provider: Literal["ollama"]
    context_tokens: int = Field(gt=0)
    input_budget_tokens: int = Field(gt=0)
    max_output_tokens: int = Field(gt=0)
    tool_calling: bool
    structured_output: bool
    output_tokens_per_second: float = Field(gt=0)
    max_tools_per_call: int = Field(gt=0)
    shortlist_k: int = Field(gt=0)
    timeout_seconds: float = Field(gt=0)

    @model_validator(mode="after")
    def _budget_fits_context(self) -> ModelProfile:
        if self.input_budget_tokens + self.max_output_tokens > self.context_tokens:
            raise ValueError("input_budget_tokens + max_output_tokens must fit within context_tokens")
        return self


class ServiceConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = "aria"
    preflight_on_startup: bool = True


class BackendConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    openapi_path: str
    metadata_schema_path: str


class HttpConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    connect_timeout_seconds: float = Field(gt=0)
    read_timeout_seconds: float = Field(gt=0)
    retries: int = Field(ge=0)


class PreflightConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    timeout_seconds: float = Field(gt=0)


class ModelsConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    profiles: dict[str, ModelProfile]


class DeploymentConfig(BaseModel):
    """The YAML deployment file. Unknown sections are rejected so typos surface at startup."""

    model_config = ConfigDict(extra="forbid")

    service: ServiceConfig = ServiceConfig()
    backend: BackendConfig
    http: HttpConfig
    preflight: PreflightConfig
    models: ModelsConfig


class ModelRole(BaseModel):
    """A configured model together with its endpoint and capability profile."""

    role: ModelRoleName
    name: str
    api_base: str
    native_api_base: str | None
    api_key: SecretStr | None
    profile: ModelProfile


class Settings(BaseModel):
    env: EnvSettings
    deployment: DeploymentConfig
    models: dict[ModelRoleName, ModelRole]

    @property
    def tool_model(self) -> ModelRole:
        return self.models["tool"]

    @property
    def synthesis_model(self) -> ModelRole:
        return self.models["synthesis"]

    def secret_values(self) -> list[str]:
        """Every configured secret, so that logging can mask them wherever they appear."""
        values = []
        for field_name in type(self.env).model_fields:
            value = getattr(self.env, field_name)
            if isinstance(value, SecretStr) and value.get_secret_value():
                values.append(value.get_secret_value())
        return values


def _describe_validation_error(source: str, error: ValidationError) -> list[str]:
    # include_input=False keeps configured values (possibly secrets) out of the messages.
    problems = []
    for item in error.errors(include_input=False, include_url=False):
        location = ".".join(str(part) for part in item["loc"]) or "(root)"
        problems.append(f"{source}: {location}: {item['msg']}")
    return problems


def _read_yaml(path: Path) -> dict:
    if not path.is_file():
        raise ConfigError([f"deployment config file not found: {path}"])
    try:
        content = yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as error:
        raise ConfigError([f"deployment config is not valid YAML: {path}: {error}"]) from error
    if not isinstance(content, dict):
        raise ConfigError([f"deployment config must be a mapping: {path}"])
    return content


def _build_model_roles(env: EnvSettings, deployment: DeploymentConfig) -> dict[ModelRoleName, ModelRole]:
    declared = {
        "tool": (env.model_name, env.openai_api_base, env.model_native_api_base, env.openai_api_key),
        "synthesis": (
            env.general_model_name,
            env.general_openai_api_base,
            env.general_model_native_api_base,
            env.general_openai_api_key,
        ),
    }
    roles: dict[ModelRoleName, ModelRole] = {}
    problems = []
    for role, (name, api_base, native_api_base, api_key) in declared.items():
        profile = deployment.models.profiles.get(name)
        if profile is None:
            problems.append(f"models.profiles: no capability profile for the {role} model")
            continue
        roles[role] = ModelRole(
            role=role,
            name=name,
            api_base=api_base,
            native_api_base=native_api_base,
            api_key=api_key,
            profile=profile,
        )
    if problems:
        raise ConfigError(problems)
    return roles


def load_settings(env_file: Path | None = DEFAULT_ENV_FILE, config_file: Path | None = None) -> Settings:
    """Load and cross-check all configuration. Raises ConfigError listing every problem found."""
    try:
        env = EnvSettings(_env_file=env_file, _env_file_encoding="utf-8")
    except ValidationError as error:
        raise ConfigError(_describe_validation_error("environment", error)) from error

    yaml_path = config_file or env.aria_config_file
    try:
        deployment = DeploymentConfig.model_validate(_read_yaml(yaml_path))
    except ValidationError as error:
        raise ConfigError(_describe_validation_error(str(yaml_path), error)) from error

    models = _build_model_roles(env, deployment)
    return Settings(env=env, deployment=deployment, models=models)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """The process-wide settings, loaded once from `.env` and the deployment file."""
    return load_settings()
