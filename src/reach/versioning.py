from __future__ import annotations

from importlib.metadata import PackageNotFoundError, version as pkg_version
from pathlib import Path
import tomllib


def _find_repo_versions_file() -> Path | None:
    start = Path(__file__).resolve()
    for parent in start.parents:
        candidate = parent / "versions.toml"
        if candidate.exists():
            return candidate
    return None


def _find_repo_pyproject_file() -> Path | None:
    start = Path(__file__).resolve()
    for parent in start.parents:
        candidate = parent / "pyproject.toml"
        if candidate.exists():
            return candidate
    return None


def get_component_versions() -> dict[str, str]:
    versions_file = _find_repo_versions_file()
    if versions_file is None:
        return {}

    with versions_file.open("rb") as f:
        data = tomllib.load(f)

    components = data.get("components", {})
    return {
        str(name): str(version)
        for name, version in components.items()
    }


def get_component_version(component: str) -> str | None:
    versions = get_component_versions()
    return versions.get(component)


def get_runtime_version() -> str:
    try:
        return pkg_version("reach")
    except PackageNotFoundError:
        pyproject = _find_repo_pyproject_file()
        if pyproject is None:
            return "0.0.0+dev"

        with pyproject.open("rb") as f:
            data = tomllib.load(f)

        return str(data.get("project", {}).get("version", "0.0.0+dev"))
