# reach/cli/server/protocols.py
from __future__ import annotations

import importlib

import typer
from rich.console import Console
from rich.table import Table

from . import app
from reach.core.protocols import list_protocols


def _load_protocol_modules() -> None:
    for name in ("http", "ftp"):
        importlib.import_module(f"reach.core.protocols.{name}.server")


@app.command("protocols")
def list_protocols_cmd() -> None:
    """
    List registered protocol servers.
    """
    _load_protocol_modules()
    protocols = list_protocols()

    table = Table(title="REACH Protocols")
    table.add_column("Name", style="cyan")
    table.add_column("Type", style="green")
    table.add_column("Public App", style="magenta")
    table.add_column("Description", style="white")

    for name, entry in sorted(protocols.items()):
        table.add_row(
            name,
            entry.server_type,
            entry.public_app,
            entry.description or "-",
        )

    Console().print(table)
