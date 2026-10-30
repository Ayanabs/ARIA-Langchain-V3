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

from aria.catalog.config import CatalogConfig
from aria.prompts import PromptsConfig

DEFAULT_ENV_FILE = Path(".env")

# Deployment sections that may be kept in a file of their own (`<section>_file`).
INCLUDABLE_SECTIONS = ("catalog", "prompts")

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
    # Bearer credential for reading the backend contract (OpenAPI, entity metadata) where the
    # backend requires one, as its local-test profile does. Tool calls use the caller's own token.
    spring_boot_contract_token: SecretStr | None = None

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

    # Only hosts whose real per-request context ARIA can set or verify are supported, so prompts are
    # never silently truncated:
    # - "ollama": the native API takes the context length per request (`num_ctx`).
    # - "llama_cpp": llama-server fixes the context per slot at startup; preflight reads it from
    #   `/props` and the configured context must fit inside it.
    provider: Literal["ollama", "llama_cpp"]
    context_tokens: int = Field(gt=0)
    input_budget_tokens: int = Field(gt=0)
    max_output_tokens: int = Field(gt=0)
    tool_calling: bool
    structured_output: bool
    output_tokens_per_second: float = Field(gt=0)
    max_tools_per_call: int = Field(gt=0)
    shortlist_k: int = Field(gt=0)
    timeout_seconds: float = Field(gt=0)
    # Whether the model may spend output on hidden reasoning before answering. Off by default:
    # output is the slow part, and each call asks for one narrow decision.
    thinking: bool = False

    @model_validator(mode="after")
    def _budget_fits_context(self) -> ModelProfile:
        if self.input_budget_tokens + self.max_output_tokens > self.context_tokens:
            raise ValueError("input_budget_tokens + max_output_tokens must fit within context_tokens")
        return self


class ServiceConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = "aria"
    preflight_on_startup: bool = True
    load_catalog_on_startup: bool = True


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
    catalog: CatalogConfig = CatalogConfig()
    prompts: PromptsConfig = PromptsConfig()
    # The catalog and the prompts may each live in their own file, relative to this one.
    catalog_file: Path | None = None
    prompts_file: Path | None = None


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

    def contract_headers(self) -> dict[str, str]:
        """Headers for reading the backend contract."""
        token = self.env.spring_boot_contract_token
        if token is None or not token.get_secret_value():
            return {}
        return {"Authorization": f"Bearer {token.get_secret_value()}"}

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


def merge_binding_files(catalog: dict, catalog_path: Path) -> dict:
    """Merge the per-module binding files named by `bindings_dir` into the catalog's tools."""
    if not catalog.get("bindings_dir"):
        return catalog
    directory = catalog_path.parent / catalog["bindings_dir"]
    if not directory.is_dir():
        raise ConfigError([f"bindings directory not found: {directory}"])
    tools = dict(catalog.get("tools") or {})
    problems = []
    for path in sorted(directory.glob("*.yaml")):
        for name, binding in _read_yaml(path).items():
            if name in tools:
                problems.append(f"{path}: tool {name} is bound more than once")
            tools[name] = binding
    if problems:
        raise ConfigError(problems)
    return {**catalog, "tools": tools}


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
    content = _read_yaml(yaml_path)
    sources = {}
    for section in INCLUDABLE_SECTIONS:
        file_key = f"{section}_file"
        if not content.get(file_key):
            continue
        if section in content:
            raise ConfigError([f"{yaml_path}: give either {section} or {file_key}, not both"])
        sources[section] = yaml_path.parent / content[file_key]
        content[section] = _read_yaml(sources[section])
    if "catalog" in content:
        content["catalog"] = merge_binding_files(content["catalog"], sources.get("catalog", yaml_path))
    try:
        deployment = DeploymentConfig.model_validate(content)
    except ValidationError as error:
        # Name the file each failing section came from.
        problems = []
        for problem in _describe_validation_error(str(yaml_path), error):
            section = problem.split(": ", 2)[1].split(".", 1)[0]
            if section in sources:
                problem = problem.replace(str(yaml_path), str(sources[section]), 1)
            problems.append(problem)
        raise ConfigError(problems) from error

    models = _build_model_roles(env, deployment)
    return Settings(env=env, deployment=deployment, models=models)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """The process-wide settings, loaded once from `.env` and the deployment file."""
    return load_settings()
