from __future__ import annotations

from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

from . import app
from reach.forge.manifests import (
    discover_manifest_files,
    load_manifest,
    validate_manifest_package,
)


@app.command("validate")
def validate_forge_items(
    root: Path = typer.Option(
        Path("plugins/forge"),
        "--root",
        help="Root directory to scan recursively for manifest.yaml files.",
    ),
    check_import: bool = typer.Option(
        True,
        "--check-import/--no-check-import",
        help="Import entry file and verify entrypoint is callable.",
    ),
) -> None:
    """Validate forge manifest packages under a root directory."""
    console = Console()
    root = root.resolve()

    if not root.exists() or not root.is_dir():
        console.print(f"[red]Validation root does not exist:[/red] {root}")
        raise typer.Exit(code=1)

    manifest_files = discover_manifest_files(root)
    if not manifest_files:
        console.print(f"[yellow]No manifest files found under {root}[/yellow]")
        return

    table = Table(title="Forge Validation Results")
    table.add_column("Item", style="cyan")
    table.add_column("Type", style="white")
    table.add_column("Manifest", style="white")
    table.add_column("Status", style="magenta")
    table.add_column("Detail", style="white")

    valid = 0
    invalid = 0

    for manifest_file in manifest_files:
        try:
            manifest = load_manifest(manifest_file)
        except Exception as exc:
            invalid += 1
            table.add_row(
                manifest_file.parent.name,
                "unknown",
                str(manifest_file),
                "invalid",
                str(exc),
            )
            continue

        errors = validate_manifest_package(
            manifest,
            check_entrypoint_import=check_import,
        )
        if errors:
            invalid += 1
            for index, error in enumerate(errors):
                table.add_row(
                    manifest.package_dir.name if index == 0 else "",
                    manifest.item_type if index == 0 else "",
                    str(manifest.path) if index == 0 else "",
                    "invalid" if index == 0 else "",
                    error,
                )
            continue

        valid += 1
        table.add_row(
            manifest.package_dir.name,
            manifest.item_type,
            str(manifest.path),
            "ok",
            f"kind={manifest.kind} entrypoint={manifest.entrypoint}",
        )

    console.print(table)
    console.print(f"[bold]Summary:[/bold] valid={valid} invalid={invalid}")

    if invalid:
        raise typer.Exit(code=1)
