from __future__ import annotations

import shutil
from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

from . import app
from reach.forge.manifests import (
    TYPE_DIRS,
    discover_manifest_files,
    load_manifest,
    validate_manifest_package,
)


def _infer_category(kind: str) -> str:
    normalized = kind.strip().lower()
    if "_" in normalized:
        family = normalized.split("_", 1)[0]
        if family:
            return family
    return "misc"


@app.command("cleanup")
def cleanup_forge_items(
    source_root: Path = typer.Option(
        Path("plugins/forge"),
        "--source-root",
        help="Folder containing plug-and-play forge item folders.",
    ),
    destination_root: Path = typer.Option(
        Path("plugins/forge"),
        "--destination-root",
        help="Target forge plugins root where items are organized by type/category.",
    ),
    apply_changes: bool = typer.Option(
        False,
        "--apply/--dry-run",
        help="Apply file moves. Default is dry-run.",
    ),
    force: bool = typer.Option(
        False,
        "--force",
        help="Overwrite existing destination folders by deleting them first.",
    ),
    check_internal: bool = typer.Option(
        True,
        "--check-internal/--no-check-internal",
        help="Validate internal built-in forge packages under src/reach/forge.",
    ),
    internal_root: Path = typer.Option(
        Path("src/reach/forge"),
        "--internal-root",
        help="Internal built-in forge package root to validate when --check-internal is enabled.",
    ),
) -> None:
    """Rebuild plug-and-play forge items into canonical type/category folders."""
    console = Console()
    source_root = source_root.resolve()
    destination_root = destination_root.resolve()

    if not source_root.exists() or not source_root.is_dir():
        console.print(f"[red]Source root does not exist:[/red] {source_root}")
        raise typer.Exit(code=1)

    manifest_files = discover_manifest_files(source_root)
    if not manifest_files:
        console.print(f"[yellow]No manifest files found under {source_root}[/yellow]")

    table = Table(title="Forge Cleanup Plan")
    table.add_column("Item", style="cyan")
    table.add_column("Type", style="white")
    table.add_column("From", style="white")
    table.add_column("To", style="white")
    table.add_column("Action", style="magenta")

    moved = 0
    skipped = 0
    errors = 0

    for manifest_file in manifest_files:
        try:
            manifest = load_manifest(manifest_file)
        except Exception as exc:
            errors += 1
            table.add_row(
                manifest_file.parent.name,
                "unknown",
                str(manifest_file.parent),
                "-",
                f"invalid manifest: {exc}",
            )
            continue

        type_dir = TYPE_DIRS.get(manifest.item_type)
        if not type_dir:
            errors += 1
            table.add_row(
                manifest.package_dir.name,
                manifest.item_type,
                str(manifest.package_dir),
                "-",
                "unsupported type",
            )
            continue

        category = manifest.category or _infer_category(manifest.kind)
        destination = destination_root / type_dir / category / manifest.package_dir.name

        if manifest.package_dir.resolve() == destination.resolve():
            skipped += 1
            table.add_row(
                manifest.package_dir.name,
                manifest.item_type,
                str(manifest.package_dir),
                str(destination),
                "already organized",
            )
            continue

        if destination.exists():
            if not force:
                skipped += 1
                table.add_row(
                    manifest.package_dir.name,
                    manifest.item_type,
                    str(manifest.package_dir),
                    str(destination),
                    "exists (use --force)",
                )
                continue
            if apply_changes:
                shutil.rmtree(destination)

        action = "move"
        if not apply_changes:
            action = "plan move"
        else:
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(manifest.package_dir), str(destination))
            moved += 1

        table.add_row(
            manifest.package_dir.name,
            manifest.item_type,
            str(manifest.package_dir),
            str(destination),
            action,
        )

    if manifest_files:
        console.print(table)
    console.print(
        f"[bold]Summary:[/bold] moved={moved} skipped={skipped} invalid={errors} "
        f"mode={'apply' if apply_changes else 'dry-run'}"
    )

    internal_invalid = 0
    if check_internal:
        internal_path = internal_root.resolve()
        internal_files = discover_manifest_files(internal_path) if internal_path.is_dir() else []
        internal_table = Table(title="Internal Forge Validation")
        internal_table.add_column("Item", style="cyan")
        internal_table.add_column("Manifest", style="white")
        internal_table.add_column("Status", style="magenta")
        internal_table.add_column("Detail", style="white")

        for manifest_file in internal_files:
            try:
                manifest = load_manifest(manifest_file)
            except Exception as exc:
                internal_invalid += 1
                internal_table.add_row(manifest_file.parent.name, str(manifest_file), "invalid", str(exc))
                continue

            validation_errors = validate_manifest_package(manifest, check_entrypoint_import=False)
            if validation_errors:
                internal_invalid += 1
                internal_table.add_row(
                    manifest.package_dir.name,
                    str(manifest.path),
                    "invalid",
                    "; ".join(validation_errors),
                )
            else:
                internal_table.add_row(
                    manifest.package_dir.name,
                    str(manifest.path),
                    "ok",
                    f"kind={manifest.kind}",
                )

        if not internal_files:
            console.print(f"[yellow]No internal manifest files found under {internal_path}[/yellow]")
        else:
            console.print(internal_table)
            console.print(
                f"[bold]Internal Summary:[/bold] checked={len(internal_files)} invalid={internal_invalid}"
            )

    errors += internal_invalid
    if errors > 0:
        raise typer.Exit(code=1)
