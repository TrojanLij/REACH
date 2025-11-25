# reach/cli/server/__init__.py
"""
[ CLI ]
REACH SERVER

main reach server importer. look at file for list of commands 

*hint: --help in the console :)
"""
from __future__ import annotations

import typer

from ..importer import auto_discover

app = typer.Typer(help="Start and manage the REACH Core server")
auto_discover(__name__)