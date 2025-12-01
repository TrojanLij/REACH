from __future__ import annotations

import typer
from rich.console import Console

from . import app
from .list import build_routes_table


@app.command("static")
def list_static_routes(
    show_body: bool = typer.Option(
        False,
        "--show-body",
        help="Include response_body/payload in the output (may be long).",
    ),
    full_body: bool = typer.Option(
        False,
        "--full-body",
        help="Show full body instead of a truncated preview (implies --show-body).",
    ),
) -> None:
    """
    List only static FastAPI routes registered on the core app.
    """
    console = Console()
    table = build_routes_table(
        include_static=True,
        include_dynamic=False,
        show_body=show_body or full_body,
        full_body=full_body,
        decode=False,
    )
    console.print(table)

