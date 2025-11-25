# reach/cli/dev/__init__.py
"""
[ CLI ]
REACH DEV

Main importer for all "dev" commands and test commands used while developing this mess of a project.

--DEV NOTE--\nFor refference. if you do not know what you are seeing or where to start? good luck. ~Trojan
"""
from __future__ import annotations

import typer

from ..importer import auto_discover

app = typer.Typer(help="Developer utilities (dangerous in prod... but we all know it's not making it that far!)")
auto_discover(__name__)