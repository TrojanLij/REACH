# reach/cli/server/start.py
from __future__ import annotations

import typer
import uvicorn

from . import app


@app.command("start")
def start_server(
    host: str = typer.Option("127.0.0.1", "--host", "-h", help="Server host"),
    port: int = typer.Option(
        8000,
        "--port",
        "-p",
        help="Base server port (used when --port-public/--port-admin are not set)",
    ),
    port_public: int | None = typer.Option(
        None,
        "--port-public",
        help="Public server port (overrides --port for role=public/both)",
    ),
    port_admin: int | None = typer.Option(
        None,
        "--port-admin",
        help="Admin server port (overrides --port for role=admin/both)",
    ),
    reload: bool = typer.Option(False, "--reload/--no-reload", help="Auto-reload on file change"),
    log_level: str = typer.Option("info", "--log-level", help="Log level (debug, info, warning, error)"),
    role: str = typer.Option(
        "public",
        "--role",
        "-r",
        help=(
            "Server role: 'public' (dynamic routes / payloads), "
            "'admin' (manage routes/logs), or 'both' (public/admin on separate ports)"
        ),
    ),
):
    """
    Start the REACH Core server (FastAPI + Uvicorn).

    - role=public (default): dynamic routes / payloads on --port
    - role=admin: admin API on --port
    - role=both: public on --port, admin on --port+1
    """
    import uvicorn
    from multiprocessing import Process

    if role not in {"public", "admin", "both"}:
        raise typer.BadParameter("role must be 'public', 'admin', or 'both'")

    # Resolve effective ports
    public_port = port_public if port_public is not None else port
    admin_port = port_admin if port_admin is not None else port

    # Preserve old behavior for role=both when no explicit admin port:
    # admin port defaults to public+1
    if role == "both" and port_admin is None:
        admin_port = public_port + 1

    if role in {"public", "admin"}:
        target = "reach.core.server:public_app" if role == "public" else "reach.core.server:admin_app"
        effective_port = public_port if role == "public" else admin_port

        typer.echo(f"🚀 Starting REACH Core {role} server on http://{host}:{effective_port} ...")
        typer.echo(f"📡 App: {target}")

        uvicorn.run(
            target,
            host=host,
            port=effective_port,
            reload=reload,
            log_level=log_level,
        )
    else:
        public_target = "reach.core.server:public_app"
        admin_target = "reach.core.server:admin_app"

        typer.echo(f"🚀 Starting REACH Core public server on http://{host}:{public_port} ...")
        typer.echo(f"📡 Public app: {public_target}")
        typer.echo(f"🚀 Starting REACH Core admin server on http://{host}:{admin_port} ...")
        typer.echo(f"📡 Admin app: {admin_target}")

        def run_server(target: str, port_: int) -> None:
            uvicorn.run(
                target,
                host=host,
                port=port_,
                reload=reload,
                log_level=log_level,
            )

        public_proc = Process(target=run_server, args=(public_target, public_port))
        admin_proc = Process(target=run_server, args=(admin_target, admin_port))

        public_proc.start()
        admin_proc.start()

        try:
            public_proc.join()
            admin_proc.join()
        except KeyboardInterrupt:
            typer.echo("🛑 Shutting down both servers...")
            for proc in (public_proc, admin_proc):
                if proc.is_alive():
                    proc.terminate()
