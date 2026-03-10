# reach/cli/main.py
from __future__ import annotations

import typer
import pyfiglet

from . import dev, server, routes, logs, forge, dns
from reach.versioning import get_runtime_version

app = typer.Typer(help="REACH command-line interface")

# Attach sub-apps
app.add_typer(server.app, name="server")
app.add_typer(routes.app, name="routes")
app.add_typer(logs.app, name="logs")
app.add_typer(forge.app, name="forge")
app.add_typer(dns.app, name="dns")
app.add_typer(dev.app, name="dev", help="Developer utilities (dangerous in prod... but we all know it's not making it that far!)")


@app.command("version")
def version() -> None:
    """Show the single package version for REACH."""
    typer.echo(f"reach: {get_runtime_version()}")


def main() -> None:
    print(r"""
         ____    _____      _      ____   _   _ 
        |  _ \  | ____|    / \    / ___| | | | |
        | |_) | |  _|     / _ \  | |     | |_| |
        |  _ < _| |___ _ / ___ \ | |___ _|  _  |
        |_| \_(_)_____(_)_/   \_(_)____(_)_| |_|
        
        Request Engine for Attacks, Callbacks & Handling
        --@TrojanLij
        --@th3_ch1ld
    """)
    app()


if __name__ == "__main__":
    main()
