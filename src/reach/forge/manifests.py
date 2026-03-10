"""Forge manifest loading and discovery helpers."""

from __future__ import annotations

import hashlib
import importlib.util
import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any


MANIFEST_FILENAME = "manifest.yaml"
LEGACY_MANIFEST_FILENAME = "forge.yaml"
ITEM_TYPES = {"exploit", "generator", "plugin"}
TYPE_DIRS = {
    "exploit": "exploits",
    "generator": "generators",
    "plugin": "plugins",
}
TYPE_DIR_ALIASES = {
    "exploit": ("exploit",),
    "generator": (),
    "plugin": (),
}


@dataclass(frozen=True)
class ForgeManifest:
    path: Path
    item_id: str
    item_type: str
    name: str
    version: str
    description: str
    entry: str
    kind: str
    entrypoint: str
    summary: str
    category: str
    author: str
    license: str
    tags: list[str]
    requires_python: list[str]
    requires_system: list[str]
    requirements_file: str
    system_requirements_file: str
    required_env: list[str]
    optional_env: list[str]
    asset_dirs: list[str]
    min_core_version: str
    max_core_version: str
    api_version: str

    @property
    def package_dir(self) -> Path:
        return self.path.parent

    @property
    def entry_file(self) -> Path:
        return (self.package_dir / self.entry).resolve()


def _strip_inline_comment(value: str) -> str:
    if "#" not in value:
        return value.strip()
    out: list[str] = []
    in_quote: str | None = None
    for char in value:
        if char in {"'", '"'}:
            if in_quote == char:
                in_quote = None
            elif in_quote is None:
                in_quote = char
        if char == "#" and in_quote is None:
            break
        out.append(char)
    return "".join(out).strip()


def _parse_scalar(value: str) -> Any:
    value = _strip_inline_comment(value)
    if not value:
        return ""
    if (value.startswith('"') and value.endswith('"')) or (
        value.startswith("'") and value.endswith("'")
    ):
        return value[1:-1]
    if value.startswith("[") and value.endswith("]"):
        inner = value[1:-1].strip()
        if not inner:
            return []
        return [str(_parse_scalar(chunk.strip())) for chunk in inner.split(",") if chunk.strip()]
    if value.lower() in {"true", "false"}:
        return value.lower() == "true"
    return value


def _parse_minimal_yaml(text: str) -> dict[str, Any]:
    """
    Parse a minimal subset of YAML used by forge manifests.
    Supported:
    - top-level key: value
    - top-level key: [a, b]
    - top-level key: then indented list items (- value)
    """
    data: dict[str, Any] = {}
    current_list_key: str | None = None

    for raw_line in text.splitlines():
        line = raw_line.rstrip()
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue

        if stripped.startswith("- "):
            if not current_list_key:
                raise ValueError("invalid manifest list item with no list key")
            item = _parse_scalar(stripped[2:].strip())
            if not isinstance(data.get(current_list_key), list):
                data[current_list_key] = []
            data[current_list_key].append(str(item))
            continue

        if ":" not in line:
            raise ValueError(f"invalid manifest line: {raw_line!r}")

        key, raw_value = line.split(":", 1)
        key = key.strip()
        if not key:
            raise ValueError("manifest key cannot be empty")

        value = _strip_inline_comment(raw_value)
        if value == "":
            data[key] = []
            current_list_key = key
            continue

        parsed = _parse_scalar(value)
        if isinstance(parsed, list):
            data[key] = [str(item) for item in parsed]
        else:
            data[key] = parsed
        current_list_key = None

    return data


def _load_yaml(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    try:
        import yaml  # type: ignore[import-not-found]

        loaded = yaml.safe_load(text)
        if isinstance(loaded, dict):
            return loaded
    except Exception:
        pass

    loaded = _parse_minimal_yaml(text)
    if not isinstance(loaded, dict):
        raise ValueError(f"{path}: manifest must be a mapping")
    return loaded


def _list_str(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list) and all(isinstance(item, str) for item in value):
        return list(value)
    raise ValueError("expected list[str]")


def _normalize_kind(data: dict[str, Any], package_dir: Path) -> str:
    kind = str(data.get("kind", "")).strip().lower()
    if kind:
        return kind

    category = str(data.get("category", "")).strip().lower()
    item_name = package_dir.name.lower()
    if category:
        return f"{category}_{item_name}"
    return item_name


def _manifest_files_under(root: Path) -> list[Path]:
    """
    Discover manifests under a root.
    Canonical file is manifest.yaml; forge.yaml is fallback only.
    """
    primary = sorted(root.rglob(MANIFEST_FILENAME))
    with_primary = {path.parent.resolve() for path in primary}
    legacy: list[Path] = []
    for candidate in sorted(root.rglob(LEGACY_MANIFEST_FILENAME)):
        if candidate.parent.resolve() in with_primary:
            continue
        legacy.append(candidate)
    return [*primary, *legacy]


def discover_manifest_files(root: Path) -> list[Path]:
    return _manifest_files_under(root)


def load_manifest(path: Path) -> ForgeManifest:
    data = _load_yaml(path)

    item_id = str(data.get("id", "")).strip()
    if not item_id:
        raise ValueError(f"{path}: missing required key 'id'")

    item_type = str(data.get("type", "")).strip().lower()
    if item_type not in ITEM_TYPES:
        raise ValueError(f"{path}: invalid type {item_type!r}")

    name = str(data.get("name", "")).strip()
    if not name:
        raise ValueError(f"{path}: missing required key 'name'")

    version = str(data.get("version", "")).strip()
    if not version:
        raise ValueError(f"{path}: missing required key 'version'")

    api_version = str(data.get("forge_api_version", data.get("api_version", ""))).strip()
    if not api_version:
        raise ValueError(f"{path}: missing required key 'forge_api_version'")

    entry = str(data.get("entry", "")).strip()
    if not entry:
        raise ValueError(f"{path}: missing required key 'entry'")

    kind = _normalize_kind(data, path.parent)
    entrypoint = str(data.get("entrypoint", "")).strip()
    if not entrypoint:
        raise ValueError(f"{path}: missing required key 'entrypoint'")

    summary = str(data.get("summary", "")).strip()
    description = str(data.get("description", "")).strip()
    category = str(data.get("category", "")).strip().lower()
    author = str(data.get("author", "")).strip()
    license_name = str(data.get("license", "")).strip()
    min_core_version = str(data.get("min_core_version", "")).strip()
    max_core_version = str(data.get("max_core_version", "")).strip()

    try:
        tags = _list_str(data.get("tags", []))
        requires_python = _list_str(data.get("requires_python", []))
        requires_system = _list_str(data.get("requires_system", []))
        required_env = _list_str(
            data.get("required_env", data.get("required_environment", []))
        )
        optional_env = _list_str(
            data.get("optional_env", data.get("optional_environment", []))
        )
        asset_dirs = _list_str(data.get("asset_dirs", []))
    except ValueError as exc:
        raise ValueError(f"{path}: {exc}") from exc

    legacy_asset_dir = str(data.get("assets_dir", "")).strip()
    if legacy_asset_dir and not asset_dirs:
        asset_dirs = [legacy_asset_dir]

    requirements_file = str(
        data.get("requirements_file", data.get("dependencies_file", ""))
    ).strip()
    if not requirements_file and (path.parent / "requirements.txt").is_file():
        requirements_file = "requirements.txt"

    system_requirements_file = str(
        data.get(
            "system_requirements_file",
            data.get("system_dependencies_file", ""),
        )
    ).strip()
    if not system_requirements_file and (path.parent / "system-requirements.txt").is_file():
        system_requirements_file = "system-requirements.txt"

    if set(required_env) & set(optional_env):
        raise ValueError(
            f"{path}: environment variable names cannot appear in both required_env and optional_env"
        )
    env_name_pattern = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
    for env_name in [*required_env, *optional_env]:
        if not env_name_pattern.fullmatch(env_name):
            raise ValueError(f"{path}: invalid environment variable name {env_name!r}")

    return ForgeManifest(
        path=path.resolve(),
        item_id=item_id,
        item_type=item_type,
        name=name,
        version=version,
        description=description,
        entry=entry,
        kind=kind,
        entrypoint=entrypoint,
        summary=summary,
        category=category,
        author=author,
        license=license_name,
        tags=tags,
        requires_python=requires_python,
        requires_system=requires_system,
        requirements_file=requirements_file,
        system_requirements_file=system_requirements_file,
        required_env=required_env,
        optional_env=optional_env,
        asset_dirs=asset_dirs,
        min_core_version=min_core_version,
        max_core_version=max_core_version,
        api_version=api_version,
    )


def resolve_type_roots(*, item_type: str, legacy_env_var: str | None = None) -> list[Path]:
    """
    Resolve allowlisted roots for a forge type directory.
    """
    type_dir = TYPE_DIRS[item_type]
    aliases = TYPE_DIR_ALIASES.get(item_type, ())
    roots: list[Path] = []
    builtin_root = Path(__file__).resolve().parent / type_dir
    roots.append(builtin_root)
    for alias in aliases:
        roots.append(Path(__file__).resolve().parent / alias)

    if legacy_env_var:
        env_paths = os.getenv(legacy_env_var)
        if env_paths:
            roots.extend([Path(p) for p in env_paths.split(os.pathsep) if p.strip()])

    shared_env = os.getenv("REACH_FORGE_PATHS")
    if shared_env:
        for raw in [p for p in shared_env.split(os.pathsep) if p.strip()]:
            base = Path(raw)
            roots.append(base / type_dir)
            roots.append(base / "forge" / type_dir)
            for alias in aliases:
                roots.append(base / alias)
                roots.append(base / "forge" / alias)

    roots.append(Path.cwd() / "plugins" / "forge" / type_dir)
    roots.append(Path.home() / ".reach" / "plugins" / "forge" / type_dir)
    for alias in aliases:
        roots.append(Path.cwd() / "plugins" / "forge" / alias)
        roots.append(Path.home() / ".reach" / "plugins" / "forge" / alias)

    resolved: list[Path] = []
    seen: set[Path] = set()
    for root in roots:
        normalized = root.resolve()
        if normalized in seen:
            continue
        seen.add(normalized)
        resolved.append(normalized)
    return resolved


def discover_manifests(*, item_type: str, legacy_env_var: str | None = None) -> list[ForgeManifest]:
    manifests: list[ForgeManifest] = []
    for root in resolve_type_roots(item_type=item_type, legacy_env_var=legacy_env_var):
        if not root.exists() or not root.is_dir():
            continue
        for manifest_file in _manifest_files_under(root):
            try:
                manifest = load_manifest(manifest_file)
            except Exception:
                continue
            if manifest.item_type != item_type:
                continue
            manifests.append(manifest)
    return manifests


def validate_manifest_package(
    manifest: ForgeManifest,
    *,
    api_version: str = "1",
    check_entrypoint_import: bool = True,
) -> list[str]:
    errors: list[str] = []

    if manifest.api_version != api_version:
        errors.append(
            f"unsupported forge api version {manifest.api_version!r}; expected {api_version!r}"
        )

    package_dir = manifest.package_dir.resolve()
    entry_file = manifest.entry_file
    if not entry_file.exists() or not entry_file.is_file():
        errors.append(f"entry file does not exist: {entry_file}")
        return errors

    try:
        entry_file.relative_to(package_dir)
    except ValueError:
        errors.append("entry path escapes package root")
        return errors

    if not check_entrypoint_import:
        check_entrypoint_import = False

    rel_file_fields = [
        ("requirements_file", manifest.requirements_file),
        ("system_requirements_file", manifest.system_requirements_file),
    ]
    for field_name, rel_path in rel_file_fields:
        if not rel_path:
            continue
        abs_path = (package_dir / rel_path).resolve()
        try:
            abs_path.relative_to(package_dir)
        except ValueError:
            errors.append(f"{field_name} escapes package root")
            continue
        if not abs_path.is_file():
            errors.append(f"{field_name} does not exist: {abs_path}")

    for rel_dir in manifest.asset_dirs:
        abs_dir = (package_dir / rel_dir).resolve()
        try:
            abs_dir.relative_to(package_dir)
        except ValueError:
            errors.append(f"asset_dirs entry escapes package root: {rel_dir}")
            continue
        if not abs_dir.exists() or not abs_dir.is_dir():
            errors.append(f"asset dir does not exist: {abs_dir}")

    if not check_entrypoint_import:
        return errors

    try:
        unique = hashlib.sha1(str(entry_file).encode("utf-8")).hexdigest()[:10]
        module_name = f"reach.forge.validate.{manifest.kind}.{unique}"
        spec = importlib.util.spec_from_file_location(module_name, entry_file)
        if not spec or not spec.loader:
            errors.append("unable to create import spec for entry file")
            return errors
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)  # type: ignore[attr-defined]
    except Exception as exc:
        errors.append(f"entry import failed: {exc}")
        return errors

    fn = getattr(module, manifest.entrypoint, None)
    if not callable(fn):
        errors.append(f"entrypoint {manifest.entrypoint!r} is not callable")
        return errors

    return errors
