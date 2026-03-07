"""
[ CLI ]
REACH FORGE

CLI entrypoint for generators/exploits and route creation via Forge.
"""
from __future__ import annotations

import typer

from ..importer import auto_discover

app = typer.Typer(help="Generate outputs and create routes via Forge")


@app.callback(invoke_without_command=True)
def forge_callback(
    ctx: typer.Context,
    list_all: bool = typer.Option(
        False,
        "--list",
        help="List forge kinds across generators/exploits/payload-aliases.",
    ),
    kind: str | None = typer.Option(
        None,
        "--kind",
        "--generator-kind",
        "--exploit-kind",
        help="Kind to describe (works with --list, --list-generators, or --list-exploits).",
    ),
    list_generators: bool = typer.Option(
        False,
        "--list-generators",
        help="List generator kinds only (optionally with --kind for details).",
    ),
    list_exploits: bool = typer.Option(
        False,
        "--list-exploits",
        help="List exploit kinds (optionally with --exploit-kind for details).",
    ),
) -> None:
    if list_all:
        from .help import forge_list_catalog

        forge_list_catalog(kind=kind)
        raise typer.Exit()
    if list_generators:
        from .help import forge_list_generators

        forge_list_generators(kind=kind)
        raise typer.Exit()
    if list_exploits:
        from .help import forge_list_exploits

        forge_list_exploits(kind=kind)
        raise typer.Exit()

    if ctx.invoked_subcommand is None:
        typer.echo(ctx.get_help())
        raise typer.Exit()


auto_discover(__name__)
