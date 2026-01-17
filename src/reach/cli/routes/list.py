# reach/cli/routes/list.py
from __future__ import annotations

import typer
from rich.console import Console
from rich.table import Table

from . import app
from reach.core.db.session import with_session


def build_routes_table(
    *,
    include_static: bool,
    include_dynamic: bool,
    show_body: bool,
    full_body: bool,
    decode: bool,
) -> Table:
    """
    Build a Rich table for static and/or dynamic routes.

    The caller controls which types to include so that different CLI
    subcommands can expose static-only, dynamic-only, or combined views.
    """
    from base64 import b64decode
    from reach.core.server import create_admin_app
    from reach.core.db import models

    table = Table(title="REACH Routes", show_lines=True)
    table.add_column("Type", style="cyan", no_wrap=True)
    table.add_column("Route ID", style="yellow")
    table.add_column("Method", style="green")
    table.add_column("Path", style="magenta")
    table.add_column("Status", style="yellow")
    table.add_column("ContentType", style="white")

    if show_body or full_body:
        table.add_column("Body", style="white")

    # Static FastAPI routes
    if include_static:
        # Build a fresh admin app to inspect its static routes
        fastapi_app = create_admin_app()
        for route in fastapi_app.routes:
            methods = ", ".join(route.methods) if route.methods else ""
            base_row = [
                "STATIC",
                "-",
                methods,
                route.path,
                "-",
                "-",
            ]
            if show_body or full_body:
                base_row.append("-")
            table.add_row(*base_row)

    # Dynamic DB routes (user-defined payloads)
    if include_dynamic:
        @with_session
        def _load_routes(*, db=None):
            return db.query(models.Route).all()

        db_routes = _load_routes()
        for r in db_routes:
            base_row = [
                "DYNAMIC",
                str(r.id),
                r.method,
                "/" + r.path,
                str(r.status_code),
                r.content_type,
            ]

            if show_body or full_body:
                body = r.response_body or ""
                if decode and getattr(r, "body_encoding", "none") == "base64":
                    try:
                        body = b64decode(body).decode("utf-8", errors="replace")
                    except Exception:
                        body = f"[INVALID BASE64] {body[:40]}…"

                if not full_body and len(body) > 80:
                    body = body[:80] + "…"
                base_row.append(body)

            table.add_row(*base_row)

    return table


@app.command("list")
def list_routes(
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
    List static (FastAPI) and dynamic (DB) routes.

    Dynamic routes include the payload stored in response_body.
    """
    console = Console()
    table = build_routes_table(
        include_static=True,
        include_dynamic=True,
        show_body=show_body or full_body,
        full_body=full_body,
        decode=decode,
    )
    console.print(table)
