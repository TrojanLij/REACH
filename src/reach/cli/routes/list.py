# reach/cli/routes/list.py
from __future__ import annotations

import typer
from rich.console import Console
from rich.table import Table

from . import app

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
    from base64 import b64decode
    from reach.core.server import app as fastapi_app
    from reach.core.db import SessionLocal, models

    console = Console()

    table = Table(title="REACH Routes", show_lines=True)
    table.add_column("Type", style="cyan", no_wrap=True)
    table.add_column("Method", style="green")
    table.add_column("Path", style="magenta")
    table.add_column("Status", style="yellow")
    table.add_column("ContentType", style="white")

    if show_body or full_body:
        table.add_column("Body", style="white")

    # Static FastAPI routes
    for route in fastapi_app.routes:
        methods = ", ".join(route.methods) if route.methods else ""
        base_row = [
            "STATIC",
            methods,
            route.path,
            "-",
            "-",
        ]
        if show_body or full_body:
            base_row.append("-")
        table.add_row(*base_row)

    # Dynamic DB routes (user-defined payloads)
    db = SessionLocal()
    try:
        db_routes = db.query(models.Route).all()
        for r in db_routes:
            base_row = [
                "DYNAMIC",
                r.method,
                "/" + r.path,
                str(r.status_code),
                r.content_type,
            ]

            if show_body or full_body:
                body = r.response_body or ""
                if decode and getattr(r, "body_encoding", "none") == "base64":
                    from base64 import b64decode
                    try:
                        body = b64decode(body).decode("utf-8", errors="replace")
                    except Exception:
                        body = f"[INVALID BASE64] {body[:40]}…"

                if not full_body and len(body) > 80:
                    body = body[:80] + "…"
                base_row.append(body)

            table.add_row(*base_row)
    finally:
        db.close()

    console.print(table)
