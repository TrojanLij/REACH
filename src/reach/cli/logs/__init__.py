# reach/cli/logs/__init__.py
"""
[ CLI ]
REACH LOGGING

this is the main logging function importer for all loging related to the CLI

--DEV NOTE--\n
"""

from __future__ import annotations

import typer

from ..importer import auto_discover

app = typer.Typer(help="Stream and inspect request logs")
auto_discover(__name__)