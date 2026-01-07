"""
[ CLI ]
REACH FORGE

CLI entrypoint for generating payloads and creating routes via Forge.
"""
from __future__ import annotations

import typer

from ..importer import auto_discover

app = typer.Typer(help="Generate payloads and create routes via Forge")


@app.callback(invoke_without_command=True)
def forge_callback(
    ctx: typer.Context,
    list_payloads: bool = typer.Option(
        False,
        "--list",
        help="List payload kinds (optionally with --kind for details).",
    ),
    kind: str | None = typer.Option(
        None,
        "--kind",
        help="Payload kind to describe (use with --list).",
    ),
) -> None:
    if list_payloads:
        from .help import forge_list_payloads

        forge_list_payloads(kind=kind)
        raise typer.Exit()

    if ctx.invoked_subcommand is None:
        typer.echo(ctx.get_help())
        raise typer.Exit()


auto_discover(__name__)
