"""Offline checks of the real tool set. Validation against the backend contract runs at reload."""

from pathlib import Path

import yaml

from aria.catalog.config import CatalogConfig
from aria.catalog.loader import load_registered_tools
from aria.settings import merge_binding_files

REPO_ROOT = Path(__file__).resolve().parents[1]


def load_repository_catalog() -> CatalogConfig:
    catalog_path = REPO_ROOT / "config" / "tools.yaml"
    content = yaml.safe_load(catalog_path.read_text(encoding="utf-8"))
    return CatalogConfig.model_validate(merge_binding_files(content, catalog_path))


def test_every_registered_module_loads_and_every_binding_has_a_tool():
    config = load_repository_catalog()

    loaded = load_registered_tools(REPO_ROOT / config.tools_dir, config.modules)

    assert loaded.problems == {}
    assert set(loaded.declarations) == set(config.tools)


def test_registered_tools_carry_descriptions_and_no_endpoints():
    config = load_repository_catalog()
    loaded = load_registered_tools(REPO_ROOT / config.tools_dir, config.modules)

    for declaration in loaded.declarations.values():
        assert declaration.description, declaration.name
        assert "/api/" not in declaration.description, declaration.name


def test_tool_modules_import_nothing_but_the_declaration_api():
    for path in (REPO_ROOT / "tools").glob("*.py"):
        imports = [line for line in path.read_text(encoding="utf-8").splitlines() if "import" in line]
        assert imports == ["from aria.catalog import tool"], path.name
