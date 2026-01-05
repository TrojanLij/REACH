"""
Registry for forge payload generators.

Add a new generator module under this package. For families (xss, xxe), drop a
module under the corresponding subpackage with a `generate` function and it
will be auto-registered as `<family>_<module>`.
"""

from __future__ import annotations

import importlib.util
import os
from pathlib import Path
from typing import Callable, Dict

from .xxe import XXE_REGISTRY
from .xss import XSS_REGISTRY

# base registry
REGISTRY: Dict[str, Callable[..., str]] = {}

# include dynamically discovered generators
REGISTRY.update(XSS_REGISTRY)
REGISTRY.update(XXE_REGISTRY)

# --- External plugin loader -------------------------------------------------
# You can drop custom generators under:
#   - $PWD/forge_plugins/<family>/<name>.py
#   - $HOME/.reach/forge_plugins/<family>/<name>.py
#   - any path in REACH_FORGE_PLUGIN_PATHS (os.pathsep-separated)


def _load_external_plugins() -> None:
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


_load_external_plugins()

__all__ = ["REGISTRY"]
