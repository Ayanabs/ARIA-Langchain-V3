"""Load the registered tool modules from the tools folder.

Only modules named in configuration are imported. Any other file in the folder is not a tool, even
if it uses `@tool`, so a stray or half-finished module can never be advertised.
"""

from __future__ import annotations

import importlib.util
import logging
import sys
from dataclasses import dataclass, field
from pathlib import Path

from aria.catalog.declaration import DECLARATION_ATTRIBUTE, ToolDeclaration

logger = logging.getLogger(__name__)

# Tool modules are imported under this package name so they never collide with application modules.
TOOL_PACKAGE = "aria_registered_tools"


@dataclass
class LoadedTools:
    declarations: dict[str, ToolDeclaration] = field(default_factory=dict)
    # Tool or module name -> reasons it could not be loaded.
    problems: dict[str, list[str]] = field(default_factory=dict)

    def add_problem(self, subject: str, reason: str) -> None:
        self.problems.setdefault(subject, []).append(reason)


def load_registered_tools(tools_dir: Path, modules: list[str]) -> LoadedTools:
    loaded = LoadedTools()
    duplicates: set[str] = set()
    for module_name in modules:
        try:
            module = _import_tool_module(tools_dir, module_name)
        except Exception as error:
            # A broken module only takes its own tools down.
            logger.warning("tool module failed to load", extra={"tool_module": module_name})
            loaded.add_problem(module_name, f"module failed to load: {type(error).__name__}: {error}")
            continue
        for declaration in _declarations_in(module):
            if declaration.name in loaded.declarations:
                duplicates.add(declaration.name)
                continue
            loaded.declarations[declaration.name] = declaration

    # A name declared twice is ambiguous, so neither declaration is used.
    for name in duplicates:
        loaded.declarations.pop(name, None)
        loaded.add_problem(name, "tool name is declared by more than one registered module")
    return loaded


def _import_tool_module(tools_dir: Path, module_name: str):
    path = tools_dir / f"{module_name}.py"
    if not path.is_file():
        raise FileNotFoundError(f"no file {path.name} in the tools folder")
    qualified_name = f"{TOOL_PACKAGE}.{module_name}"
    spec = importlib.util.spec_from_file_location(qualified_name, path)
    module = importlib.util.module_from_spec(spec)
    # Re-executing on every load picks up edited modules on a schema reload.
    sys.modules[qualified_name] = module
    try:
        spec.loader.exec_module(module)
    except Exception:
        sys.modules.pop(qualified_name, None)
        raise
    return module


def _declarations_in(module) -> list[ToolDeclaration]:
    declarations = []
    for value in vars(module).values():
        declaration = getattr(value, DECLARATION_ATTRIBUTE, None)
        # Only functions defined in this module: an imported tool belongs to its own module.
        if isinstance(declaration, ToolDeclaration) and getattr(value, "__module__", None) == module.__name__:
            declarations.append(declaration)
    return declarations
