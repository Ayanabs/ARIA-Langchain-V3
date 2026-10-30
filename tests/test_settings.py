from pathlib import Path

import pytest

from aria.settings import ConfigError, load_settings
from tests.conftest import TEST_ENV, deployment_config, profile

REPO_ROOT = Path(__file__).resolve().parents[1]


def test_roles_take_their_profile_from_configuration(settings):
    assert settings.tool_model.name == "router-model"
    assert settings.tool_model.profile.max_output_tokens == 512
    assert settings.synthesis_model.name == "writer-model"
    assert settings.synthesis_model.profile.max_output_tokens == 768


def test_a_model_without_a_profile_is_a_config_error(make_settings):
    env = {**TEST_ENV, "GENERAL_MODEL_NAME": "unprofiled-model"}
    with pytest.raises(ConfigError) as caught:
        make_settings(env=env)
    assert caught.value.problems == ["models.profiles: no capability profile for the synthesis model"]


def test_missing_required_environment_is_listed_by_key(make_settings):
    env = {key: value for key, value in TEST_ENV.items() if key != "SPRING_BOOT_BASE_URL"}
    with pytest.raises(ConfigError) as caught:
        make_settings(env=env)
    assert any("spring_boot_base_url" in problem for problem in caught.value.problems)


def test_config_errors_never_include_configured_values(make_settings):
    env = {**TEST_ENV, "PORT": "not-a-port-tool-secret-value"}
    with pytest.raises(ConfigError) as caught:
        make_settings(env=env)
    assert "tool-secret-value" not in str(caught.value)


def test_a_profile_whose_budget_exceeds_its_context_is_rejected(make_settings):
    oversized = profile(context_tokens=4096, input_budget_tokens=4096, max_output_tokens=512)
    config = deployment_config(models={"profiles": {"router-model": oversized, "writer-model": profile()}})
    with pytest.raises(ConfigError) as caught:
        make_settings(config=config)
    assert any("must fit within context_tokens" in problem for problem in caught.value.problems)


def test_unknown_config_sections_are_rejected(make_settings):
    with pytest.raises(ConfigError) as caught:
        make_settings(config=deployment_config(unexpected={"value": 1}))
    assert any("unexpected" in problem for problem in caught.value.problems)


def test_missing_config_file_is_reported(write_config, tmp_path):
    env_path, _ = write_config()
    with pytest.raises(ConfigError, match="not found"):
        load_settings(env_file=env_path, config_file=tmp_path / "absent.yaml")


def test_secret_values_are_collected_for_masking(settings):
    assert settings.secret_values() == ["tool-secret-value"]


def test_shipped_example_environment_and_deployment_config_load_together():
    settings = load_settings(
        env_file=REPO_ROOT / ".env.example", config_file=REPO_ROOT / "config" / "aria.yaml"
    )
    for role in settings.models.values():
        assert (
            role.profile.input_budget_tokens + role.profile.max_output_tokens <= role.profile.context_tokens
        )
