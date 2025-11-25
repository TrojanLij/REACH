# reach/cli/routes/__init__.py
"""
[ CLI ]
REACH ROUTES

The main importer for the core routing. 


--DEV NOTE--\nBeen staring at this functionality for so long, my throughts are being routed through this now... ~Trojan
"""
from __future__ import annotations

import typer

from ..importer import auto_discover

app = typer.Typer(help="Inspect and manage routes")
auto_discover(__name__)