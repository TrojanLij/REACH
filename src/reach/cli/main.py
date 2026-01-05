# reach/cli/main.py
from __future__ import annotations

import typer

from . import dev, server, routes, logs, forge

app = typer.Typer(help="REACH command-line interface")

# Attach sub-apps
app.add_typer(server.app, name="server")
app.add_typer(routes.app, name="routes")
app.add_typer(logs.app, name="logs")
app.add_typer(forge.app, name="forge")
app.add_typer(dev.app, name="dev", help="Developer utilities (dangerous in prod... but we all know it's not making it that far!)")


def main() -> None:
    app()


if __name__ == "__main__":
    main()
