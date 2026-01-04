# reach/cli/server/start.py
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Optional

import typer
import uvicorn

from . import app
from reach.core.server import init_db

# Defaults for detecting user overrides vs. preset
DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8000
DEFAULT_ROLE = "public"
DEFAULT_RELOAD = False
DEFAULT_LOG_LEVEL = "info"


def _load_preset(path: Path) -> Dict[str, Any]:
    """Load and minimally validate a JSON preset file."""
    try:
        data = json.loads(path.read_text())
    except Exception as e:
        raise typer.BadParameter(f"Failed to read preset: {e}") from e

    if not isinstance(data, dict):
        raise typer.BadParameter("Preset must be a JSON object")

    server_cfg = data.get("server", {})
    if server_cfg is not None and not isinstance(server_cfg, dict):
        raise typer.BadParameter("Preset 'server' must be an object")

    return data


@app.command("start")
def start_server(
    preset: Optional[Path] = typer.Option(
        None,
        "--preset",
        help="Path to JSON preset for server config (host/ports/role/reload/log level).",
    ),
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

    preset_data: Dict[str, Any] = {}
    if preset:
        preset_data = _load_preset(preset)
        typer.echo(f"Using preset: {preset}")

    server_cfg = preset_data.get("server", {}) if isinstance(preset_data.get("server", {}), dict) else {}
    public_cfg = server_cfg.get("public", {}) if isinstance(server_cfg.get("public", {}), dict) else {}
    admin_cfg = server_cfg.get("admin", {}) if isinstance(server_cfg.get("admin", {}), dict) else {}

    # Start with defaults
    effective_host = server_cfg.get("host", public_cfg.get("host", DEFAULT_HOST))
    base_port = server_cfg.get("port", DEFAULT_PORT)
    preset_public_port = public_cfg.get("port")
    preset_admin_port = admin_cfg.get("port")
    effective_role = server_cfg.get("role", DEFAULT_ROLE)
    effective_reload = server_cfg.get("reload", DEFAULT_RELOAD)
    effective_log_level = server_cfg.get("log_level", DEFAULT_LOG_LEVEL)

    # CLI overrides take priority when they differ from defaults
    if host != DEFAULT_HOST:
        effective_host = host
    if port != DEFAULT_PORT:
        base_port = port
    if port_public is not None:
        preset_public_port = port_public
    if port_admin is not None:
        preset_admin_port = port_admin
    if role != DEFAULT_ROLE:
        effective_role = role
    if reload != DEFAULT_RELOAD:
        effective_reload = reload
    if log_level != DEFAULT_LOG_LEVEL:
        effective_log_level = log_level

    role = effective_role
    host = effective_host
    reload = effective_reload
    log_level = effective_log_level

    if role not in {"public", "admin", "both"}:
        raise typer.BadParameter("role must be 'public', 'admin', or 'both'")

    # Explicit DB init so app import has no side effects
    init_db()

    # Resolve effective ports
    public_port = preset_public_port if preset_public_port is not None else base_port
    admin_port = preset_admin_port if preset_admin_port is not None else base_port

    # Preserve old behavior for role=both when no explicit admin port:
    # admin port defaults to public+1
    if role == "both" and port_admin is None:
        admin_port = public_port + 1

    if role in {"public", "admin"}:
        target = "reach.core.server:create_public_app" if role == "public" else "reach.core.server:create_admin_app"
        effective_port = public_port if role == "public" else admin_port

        typer.echo(f"🚀 Starting REACH Core {role} server on http://{host}:{effective_port} ...")
        typer.echo(f"📡 App: {target}")

        uvicorn.run(
            target,
            host=host,
            port=effective_port,
            reload=reload,
            log_level=log_level,
            factory=True,
        )
    else:
        public_target = "reach.core.server:create_public_app"
        admin_target = "reach.core.server:create_admin_app"

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
                factory=True,
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
