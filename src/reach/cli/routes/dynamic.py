from __future__ import annotations

import typer
from rich.console import Console

from . import app
from .list import build_routes_table


@app.command("dynamic")
def list_dynamic_routes(
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
    decode: bool = typer.Option(
        True,
        "--decode/--raw",
        help="Decode base64 bodies before displaying (default: decode).",
    ),
) -> None:
    """
    List only dynamic (DB-backed) routes.

    Dynamic routes include the payload stored in response_body.
    """
    console = Console()
    table = build_routes_table(
        include_static=False,
        include_dynamic=True,
        show_body=show_body or full_body,
        full_body=full_body,
        decode=decode,
    )
    console.print(table)

