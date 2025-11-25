# reach/cli/importer.py
from __future__ import annotations

import importlib
import pkgutil
from pathlib import Path


def auto_discover(package_name: str) -> None:
    """
    Import all modules in the given package so that any @app.command
    decorators in those modules are executed and register commands.

    Example usage (in reach/cli/dev/__init__.py):

        app = typer.Typer(help="Developer utilities")
        auto_discover(__name__)
    """
    package = importlib.import_module(package_name)
    package_path = Path(package.__file__).resolve().parent

    for module_info in pkgutil.iter_modules([str(package_path)]):
        name = module_info.name
        if name.startswith("_"):
            continue
        importlib.import_module(f"{package_name}.{name}")
