"""
Registry for forge generators.

Plugin contract (module-level):
- PLUGIN: dict metadata
- entrypoint function (default: generate)
"""

from __future__ import annotations

import importlib
import importlib.util
import hashlib
import os
import pkgutil
from pathlib import Path
from typing import Any, Callable

from ..manifests import discover_manifests

PLUGIN_API_VERSION = "1"

# kind -> callable
REGISTRY: dict[str, Callable[..., str]] = {}
# kind -> normalized plugin metadata
PLUGIN_REGISTRY: dict[str, dict[str, Any]] = {}


def _normalize_plugin(module: Any, *, kind: str, source: str) -> tuple[Callable[..., str], dict[str, Any]]:
    raw_meta = getattr(module, "PLUGIN", None)
    if not isinstance(raw_meta, dict):
        raise ValueError(f"{source}: missing required PLUGIN metadata dict")

    api_version = str(raw_meta.get("api_version", "")).strip()
    if api_version != PLUGIN_API_VERSION:
        raise ValueError(
            f"{source}: unsupported plugin api_version {api_version!r}, expected {PLUGIN_API_VERSION!r}"
        )

    plugin_type = str(raw_meta.get("type", "")).strip().lower()
    if plugin_type not in {"generator", "payload"}:
        raise ValueError(f"{source}: plugin type must be 'generator' or 'payload'")

    plugin_kind = str(raw_meta.get("kind", "")).strip().lower() or kind
    entrypoint = str(raw_meta.get("entrypoint", "generate")).strip() or "generate"
    fn = getattr(module, entrypoint, None)
    if not callable(fn):
        raise ValueError(f"{source}: entrypoint {entrypoint!r} is not callable")

    requires_python = raw_meta.get("requires_python", [])
    requires_system = raw_meta.get("requires_system", [])
    if not isinstance(requires_python, list) or not all(
        isinstance(item, str) for item in requires_python
    ):
        raise ValueError(f"{source}: requires_python must be a list[str]")
    if not isinstance(requires_system, list) or not all(
        isinstance(item, str) for item in requires_system
    ):
        raise ValueError(f"{source}: requires_system must be a list[str]")

    summary = raw_meta.get("summary", "")
    if not isinstance(summary, str):
        raise ValueError(f"{source}: summary must be a string")

    meta = {
        "api_version": PLUGIN_API_VERSION,
        "type": plugin_type,
        "kind": plugin_kind,
        "entrypoint": entrypoint,
        "summary": summary.strip(),
        "requires_python": requires_python,
        "requires_system": requires_system,
    }
    return fn, meta


def _register_module(module: Any, *, default_kind: str, source: str) -> None:
    fn, meta = _normalize_plugin(module, kind=default_kind, source=source)
    kind = str(meta["kind"]).lower()
    REGISTRY[kind] = fn
    PLUGIN_REGISTRY[kind] = meta


def _register_from_package(package_name: str, kind_prefix: str) -> None:
    try:
        pkg = importlib.import_module(package_name)
    except Exception:
        return

    pkg_paths = getattr(pkg, "__path__", [])
    for mod in pkgutil.iter_modules(pkg_paths):
        if mod.name.startswith("_"):
            continue
        try:
            module = importlib.import_module(f"{package_name}.{mod.name}")
            default_kind = f"{kind_prefix}_{mod.name}".lower()
            _register_module(module, default_kind=default_kind, source=f"{package_name}.{mod.name}")
        except Exception:
            continue


def _discover_internal() -> None:
    base_pkg = __name__
    base_path = Path(__file__).resolve().parent
    for mod in pkgutil.iter_modules([str(base_path)]):
        if not mod.ispkg or mod.name.startswith("_"):
            continue
        package_name = f"{base_pkg}.{mod.name}"
        _register_from_package(package_name, mod.name)


def _load_external_plugins() -> None:
    """
    Load generators from external paths:
      - $PWD/plugins/forge/generators/<family>/<name>.py
      - $HOME/.reach/plugins/forge/generators/<family>/<name>.py
      - any path in REACH_FORGE_PLUGIN_PATHS (os.pathsep-separated)
    """
    manifest_packages = discover_manifests(
        item_type="generator",
        legacy_env_var="REACH_FORGE_PLUGIN_PATHS",
    )
    for manifest in manifest_packages:
        if manifest.api_version != PLUGIN_API_VERSION:
            continue
        entry_file = manifest.entry_file
        if not entry_file.exists() or not entry_file.is_file():
            continue
        try:
            unique = hashlib.sha1(str(entry_file).encode("utf-8")).hexdigest()[:10]
            module_name = f"reach.forge.generator_manifest.{manifest.kind}.{unique}"
            spec = importlib.util.spec_from_file_location(module_name, entry_file)
            if not spec or not spec.loader:
                continue
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)  # type: ignore[attr-defined]
            fn = getattr(module, manifest.entrypoint, None)
            if not callable(fn):
                continue
            REGISTRY[manifest.kind] = fn
            PLUGIN_REGISTRY[manifest.kind] = {
                "api_version": PLUGIN_API_VERSION,
                "type": "generator",
                "name": manifest.name,
                "version": manifest.version,
                "description": manifest.description,
                "kind": manifest.kind,
                "category": manifest.category,
                "entrypoint": manifest.entrypoint,
                "summary": manifest.summary,
                "author": manifest.author,
                "license": manifest.license,
                "tags": manifest.tags,
                "requires_python": manifest.requires_python,
                "requires_system": manifest.requires_system,
                "requirements_file": manifest.requirements_file,
                "system_requirements_file": manifest.system_requirements_file,
                "required_env": manifest.required_env,
                "optional_env": manifest.optional_env,
                "asset_dirs": manifest.asset_dirs,
                "min_core_version": manifest.min_core_version,
                "max_core_version": manifest.max_core_version,
                "id": manifest.item_id,
                "manifest": str(manifest.path),
            }
        except Exception:
            continue

    roots: list[Path] = []
    env_paths = os.getenv("REACH_FORGE_PLUGIN_PATHS")
    if env_paths:
        roots.extend([Path(p) for p in env_paths.split(os.pathsep) if p])
    roots.append(Path.cwd() / "plugins" / "forge" / "generators")
    roots.append(Path.home() / ".reach" / "plugins" / "forge" / "generators")

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
                default_kind = f"{family}_{pyfile.stem}".lower()
                try:
                    spec = importlib.util.spec_from_file_location(
                        f"reach.forge.plugins.{family}.{pyfile.stem}", pyfile
                    )
                    if spec and spec.loader:
                        module = importlib.util.module_from_spec(spec)
                        spec.loader.exec_module(module)  # type: ignore[attr-defined]
                        _register_module(module, default_kind=default_kind, source=str(pyfile))
                except Exception:
                    continue


_discover_internal()
_load_external_plugins()

__all__ = ["REGISTRY", "PLUGIN_REGISTRY", "PLUGIN_API_VERSION"]
