"""Rule filter registry and loader."""
from __future__ import annotations

import importlib
import importlib.util
import os
from pathlib import Path
import pkgutil
from typing import Callable

FILTERS: dict[str, Callable[..., str]] = {}


def _register_filter(name: str, fn: Callable[..., str]) -> None:
    if callable(fn):
        FILTERS[name] = fn


def _register_from_module(module: object) -> None:
    filters = getattr(module, "FILTERS", None)
    if isinstance(filters, dict):
        for name, fn in filters.items():
            _register_filter(str(name), fn)
        return
    fn = getattr(module, "filter", None)
    if callable(fn):
        name = getattr(module, "NAME", module.__name__.split(".")[-1])
        _register_filter(str(name), fn)


def _load_builtin_filters() -> None:
    pkg = __name__
    pkg_paths = __path__
    for mod in pkgutil.iter_modules(pkg_paths):
        if mod.name.startswith("_"):
            continue
        module = importlib.import_module(f"{pkg}.{mod.name}")
        _register_from_module(module)


def _load_external_filters() -> None:
    roots: list[Path] = []
    env_paths = os.getenv("REACH_RULE_FILTER_PATHS")
    if env_paths:
        roots.extend([Path(p) for p in env_paths.split(os.pathsep) if p])
    roots.append(Path.cwd() / "plugins" / "IFTTT" / "filters")
    roots.append(Path.home() / ".reach" / "plugins" / "IFTTT" / "filters")

    for root in roots:
        if not root.exists() or not root.is_dir():
            continue
        for pyfile in root.glob("*.py"):
            if pyfile.name.startswith("_"):
                continue
            try:
                spec = importlib.util.spec_from_file_location(
                    f"reach.rule_filters.{pyfile.stem}", pyfile
                )
                if spec and spec.loader:
                    module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(module)  # type: ignore[attr-defined]
                    _register_from_module(module)
            except Exception:
                continue


_load_builtin_filters()
_load_external_filters()

__all__ = ["FILTERS"]
