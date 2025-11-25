# reach/cli/dev/clear_logs.py
from __future__ import annotations

import typer

from . import app

@app.command("clear-logs")
def clear_logs_cmd() -> None:
    """
    Clear in-memory request logs in REACH Core.
    """
    from reach.core import logging as reach_logging

    reach_logging.clear_logs()
    typer.echo("🧹 In-memory request logs cleared.")
