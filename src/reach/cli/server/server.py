# reach/cli/server/start.py
from __future__ import annotations

import typer
import uvicorn

from . import app

@app.command("start")
def start_server(
    host: str = typer.Option("127.0.0.1", "--host", "-h", help="Server host"),
    port: int = typer.Option(8000, "--port", "-p", help="Server port"),
    reload: bool = typer.Option(True, "--reload/--no-reload", help="Auto-reload on file change"),
    log_level: str = typer.Option("info", "--log-level", help="Log level (debug, info, warning, error)"),
):
    """
    Start the REACH Core server (FastAPI + Uvicorn).
    """
    import uvicorn

    typer.echo(f"🚀 Starting REACH Core server on http://{host}:{port} ...")
    typer.echo("📡 App: reach.core.server:app")

    uvicorn.run(
        "reach.core.server:app",
        host=host,
        port=port,
        reload=reload,
        log_level=log_level,
    )
