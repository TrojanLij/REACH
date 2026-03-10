from __future__ import annotations

import shutil
from pathlib import Path

import typer
from rich.console import Console

from . import app
from reach.forge.manifests import TYPE_DIRS


def _derive_kind(category: str | None, name: str) -> str:
    normalized_name = name.strip().lower().replace("-", "_").replace(" ", "_")
    if category:
        normalized_category = category.strip().lower().replace("-", "_").replace(" ", "_")
        return f"{normalized_category}_{normalized_name}"
    return normalized_name


def _entrypoint_for(item_type: str) -> str:
    return "run" if item_type == "exploit" else "generate"


def _manifest_text(
    *,
    item_id: str,
    item_type: str,
    name: str,
    version: str,
    api_version: str,
    category: str | None,
    kind: str,
    entrypoint: str,
    required_env: list[str],
    optional_env: list[str],
    asset_dirs: list[str],
    include_requirements: bool,
    include_system_requirements: bool,
) -> str:
    lines = [
        f"id: {item_id}",
        f"type: {item_type}",
        f"name: {name}",
        f"version: {version}",
        f'forge_api_version: "{api_version}"',
    ]
    if category:
        lines.append(f"category: {category}")
    if include_requirements:
        lines.append("requirements_file: requirements.txt")
    if include_system_requirements:
        lines.append("system_requirements_file: system-requirements.txt")
    lines.extend(
        [
            f"kind: {kind}",
            "entry: src/entry.py",
            f"entrypoint: {entrypoint}",
            f"summary: {name}",
            "required_env: []" if not required_env else "required_env:",
        ]
    )
    for env_name in required_env:
        lines.append(f"  - {env_name}")

    if not optional_env:
        lines.append("optional_env: []")
    else:
        lines.append("optional_env:")
        for env_name in optional_env:
            lines.append(f"  - {env_name}")

    if asset_dirs:
        lines.append("asset_dirs:")
        for asset_dir in asset_dirs:
            lines.append(f"  - {asset_dir}")
    return "\n".join(lines) + "\n"


def _entry_text(item_type: str, entrypoint: str) -> str:
    export_name = "PLUGIN"
    return (
        '"""Scaffolded Forge item entrypoint."""\n\n'
        "from __future__ import annotations\n\n"
        f'__all__ = ["{export_name}", "{entrypoint}"]\n\n'
        f"{export_name} = {{\n"
        '    "api_version": "1",\n'
        f'    "type": "{item_type}",\n'
        '    "kind": "",\n'
        f'    "entrypoint": "{entrypoint}",\n'
        '    "summary": "",\n'
        '    "requires_python": [],\n'
        '    "requires_system": [],\n'
        "}\n\n"
        f"def {entrypoint}(**kwargs):\n"
        '    """Implement plugin logic."""\n'
        "    raise NotImplementedError('implement this scaffolded entrypoint')\n"
    )


@app.command("scaffold")
def scaffold_forge_item(
    item_type: str = typer.Argument(..., help="Item type: exploit|generator|plugin"),
    item_name: str = typer.Argument(..., help="Folder-safe item name (e.g. local_storage_replay)"),
    item_id: str = typer.Option(..., "--id", help="Unique item id (e.g. web.local_storage_replay)."),
    category: str | None = typer.Option(
        None,
        "--category",
        help="Optional category/family (e.g. web, xss, xxe).",
    ),
    kind: str | None = typer.Option(
        None,
        "--kind",
        help="Optional explicit kind. Defaults to <category>_<item_name> or <item_name>.",
    ),
    root: Path = typer.Option(
        Path("plugins/forge"),
        "--root",
        help="Base forge root where scaffold will be created.",
    ),
    version: str = typer.Option("0.1.0", "--version", help="Initial semantic version."),
    api_version: str = typer.Option("1", "--api-version", help="Forge API version."),
    required_env: list[str] = typer.Option(
        None,
        "--required-env",
        help="Required environment variable name. Repeat for multiple.",
    ),
    optional_env: list[str] = typer.Option(
        None,
        "--optional-env",
        help="Optional environment variable name. Repeat for multiple.",
    ),
    asset_dir: list[str] = typer.Option(
        None,
        "--asset-dir",
        help="Optional asset directory name. Repeat for multiple.",
    ),
    include_requirements: bool = typer.Option(
        True,
        "--with-requirements/--no-requirements",
        help="Create requirements.txt and set requirements_file in manifest.",
    ),
    include_system_requirements: bool = typer.Option(
        False,
        "--with-system-requirements",
        help="Create system-requirements.txt and set system_requirements_file in manifest.",
    ),
    force: bool = typer.Option(False, "--force", help="Overwrite an existing scaffold folder."),
) -> None:
    """Generate the minimal Forge plugin package skeleton from user inputs."""
    console = Console()
    normalized_type = item_type.strip().lower()
    if normalized_type not in TYPE_DIRS:
        console.print(f"[red]Invalid item type:[/red] {item_type}. Use exploit|generator|plugin.")
        raise typer.Exit(code=1)

    normalized_name = item_name.strip().lower().replace(" ", "_").replace("-", "_")
    normalized_category = (
        category.strip().lower().replace(" ", "_").replace("-", "_") if category else None
    )
    normalized_kind = (kind.strip().lower() if kind else _derive_kind(normalized_category, normalized_name))
    entrypoint = _entrypoint_for(normalized_type)
    normalized_asset_dirs = [
        p.strip().strip("/").strip("\\")
        for p in (asset_dir or [])
        if p and p.strip().strip("/").strip("\\")
    ]

    target_dir = root.resolve() / TYPE_DIRS[normalized_type] / (
        f"{normalized_category}/{normalized_name}" if normalized_category else normalized_name
    )
    if target_dir.exists():
        if not force:
            console.print(f"[red]Target already exists:[/red] {target_dir} (use --force to overwrite)")
            raise typer.Exit(code=1)
        shutil.rmtree(target_dir)
    target_dir.mkdir(parents=True, exist_ok=True)

    src_dir = target_dir / "src"
    src_dir.mkdir(parents=True, exist_ok=True)
    for rel_dir in normalized_asset_dirs:
        (target_dir / rel_dir).mkdir(parents=True, exist_ok=True)

    manifest_text = _manifest_text(
        item_id=item_id.strip(),
        item_type=normalized_type,
        name=item_name.strip(),
        version=version.strip(),
        api_version=api_version.strip(),
        category=normalized_category,
        kind=normalized_kind,
        entrypoint=entrypoint,
        required_env=required_env or [],
        optional_env=optional_env or [],
        asset_dirs=normalized_asset_dirs,
        include_requirements=include_requirements,
        include_system_requirements=include_system_requirements,
    )

    (target_dir / "manifest.yaml").write_text(manifest_text, encoding="utf-8")
    (target_dir / "README.md").write_text(
        f"# {item_name.strip()}\n\nScaffolded Forge {normalized_type} package.\n",
        encoding="utf-8",
    )
    (src_dir / "entry.py").write_text(_entry_text(normalized_type, entrypoint), encoding="utf-8")
    if include_requirements:
        (target_dir / "requirements.txt").write_text("# add python dependencies\n", encoding="utf-8")
    if include_system_requirements:
        (target_dir / "system-requirements.txt").write_text(
            "# add system requirements\n", encoding="utf-8"
        )

    console.print(f"[green]Created scaffold:[/green] {target_dir}")
    console.print(f"  - {target_dir / 'manifest.yaml'}")
    console.print(f"  - {src_dir / 'entry.py'}")
    console.print(f"  - {target_dir / 'README.md'}")
