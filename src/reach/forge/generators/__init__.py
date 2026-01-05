"""
Registry for forge payload generators.

Add a new generator module under this package (or under forge_plugins) with a
`generate(**kwargs)` function and it will be auto-registered as
`<family>_<module>`.
"""

from __future__ import annotations

import importlib
import importlib.util
import os
import pkgutil
from pathlib import Path
from typing import Callable, Dict

# kind -> callable
REGISTRY: Dict[str, Callable[..., str]] = {}


def _register_from_package(package_name: str, kind_prefix: str) -> None:
    """Discover modules in a package and register generate() as kind_prefix_<name>."""
    try:
        pkg = importlib.import_module(package_name)
    except Exception:
        return

    pkg_paths = getattr(pkg, "__path__", [])
    for mod in pkgutil.iter_modules(pkg_paths):
        if mod.name.startswith("_"):
            continue
        module = importlib.import_module(f"{package_name}.{mod.name}")
        fn = getattr(module, "generate", None)
        if callable(fn):
            kind = f"{kind_prefix}_{mod.name}"
            REGISTRY[kind] = fn


def _discover_internal() -> None:
    """Auto-discover families under reach.forge.generators.*"""
    base_pkg = __name__  # reach.forge.generators
    base_path = Path(__file__).resolve().parent
    for mod in pkgutil.iter_modules([str(base_path)]):
        if not mod.ispkg or mod.name.startswith("_"):
            continue
        package_name = f"{base_pkg}.{mod.name}"
        _register_from_package(package_name, mod.name)


def _load_external_plugins() -> None:
    """
    Load generators from external plugin paths:
      - $PWD/forge_plugins/<family>/<name>.py
      - $HOME/.reach/forge_plugins/<family>/<name>.py
      - any path in REACH_FORGE_PLUGIN_PATHS (os.pathsep-separated)
    """
    roots = []
    env_paths = os.getenv("REACH_FORGE_PLUGIN_PATHS")
    if env_paths:
        roots.extend([Path(p) for p in env_paths.split(os.pathsep) if p])
    roots.append(Path.cwd() / "forge_plugins")
    roots.append(Path.home() / ".reach" / "forge_plugins")

    for root in roots:
        if not root.exists() or not root.is_dir():
            continue
        for family_dir in root.iterdir():
            if not family_dir.is_dir():
                continue
            family = family_dir.name
            for pyfile in family_dir.glob("*.py"):
                if pyfile.name.startswith("_"):
                    continue
                kind = f"{family}_{pyfile.stem}"
                try:
                    spec = importlib.util.spec_from_file_location(
                        f"reach.forge.plugins.{family}.{pyfile.stem}", pyfile
                    )
                    if spec and spec.loader:
                        module = importlib.util.module_from_spec(spec)
                        spec.loader.exec_module(module)  # type: ignore[attr-defined]
                        fn = getattr(module, "generate", None)
                        if callable(fn):
                            REGISTRY[kind] = fn
                except Exception:
                    # Best-effort: skip broken plugins
                    continue


_discover_internal()
_load_external_plugins()

__all__ = ["REGISTRY"]
