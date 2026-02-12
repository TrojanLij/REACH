# reach/cli/dev/reset_db.py
from __future__ import annotations

import typer

from . import app

@app.command("reset-db")
def reset_db(
    yes: bool = typer.Option(
        False,
        "--yes",
        "-y",
        help="Skip confirmation prompt",
    )
) -> None:
    """
    Drop all tables and recreate them.

    This wipes all data. Intended for local/dev use.
    """
    from reach.core.db import Base, engine
    from reach.core.db.init import init_db

    if not yes:
        typer.confirm(
            "This will DROP ALL TABLES and recreate them. Continue?",
            abort=True,
        )

    Base.metadata.drop_all(bind=engine)
    init_db(force=True)

    typer.echo("✅ Database schema reset (all tables dropped and recreated).")
