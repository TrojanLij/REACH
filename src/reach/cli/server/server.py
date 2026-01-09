# reach/cli/server/start.py
from __future__ import annotations

import io
import json
import os
import tarfile
from pathlib import Path
from pathlib import PurePosixPath
from typing import Any, Dict, Optional

import typer
import uvicorn

from . import app

# Defaults for detecting user overrides vs. preset
DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8000
DEFAULT_ROLE = "public"
DEFAULT_RELOAD = False
DEFAULT_LOG_LEVEL = "info"
DOTENV_PATH = Path(".env")


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


def _load_dotenv(path: Path = DOTENV_PATH) -> None:
    """
    Minimal .env loader.

    Only sets variables that are not already defined in the environment,
    so real env vars still take precedence.
    """
    if not path.exists():
        return

    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


def _get_preset_data(preset: Optional[Path]) -> Dict[str, Any]:
    if not preset:
        return {}
    preset_data = _load_preset(preset)
    typer.echo(f"Using preset: {preset}")
    return preset_data


def _apply_db_config(db_cfg: Dict[str, Any]) -> None:
    if "url" in db_cfg:
        os.environ["REACH_DB_URL"] = str(db_cfg["url"])
    elif "file" in db_cfg:
        os.environ["REACH_DB_FILE"] = str(db_cfg["file"])
    if "echo" in db_cfg:
        os.environ["REACH_DB_ECHO"] = "1" if db_cfg["echo"] else "0"


def _resolve_server_config(
    preset_data: Dict[str, Any],
    host: str,
    port: int,
    port_public: int | None,
    port_admin: int | None,
    reload: bool,
    log_level: str,
    role: str,
) -> Dict[str, Any]:
    server_cfg = preset_data.get("server", {}) if isinstance(preset_data.get("server", {}), dict) else {}
    public_cfg = server_cfg.get("public", {}) if isinstance(server_cfg.get("public", {}), dict) else {}
    admin_cfg = server_cfg.get("admin", {}) if isinstance(server_cfg.get("admin", {}), dict) else {}
    db_cfg = preset_data.get("db", {}) if isinstance(preset_data.get("db", {}), dict) else {}

    effective_public_host = public_cfg.get("host", server_cfg.get("host", DEFAULT_HOST))
    effective_admin_host = admin_cfg.get("host", server_cfg.get("host", DEFAULT_HOST))
    base_port = server_cfg.get("port", DEFAULT_PORT)
    preset_public_port = public_cfg.get("port")
    preset_admin_port = admin_cfg.get("port")
    effective_role = server_cfg.get("role", DEFAULT_ROLE)
    effective_reload = server_cfg.get("reload", DEFAULT_RELOAD)
    effective_log_level = server_cfg.get("log_level", DEFAULT_LOG_LEVEL)

    if host != DEFAULT_HOST:
        effective_public_host = host
        effective_admin_host = host
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
    reload = effective_reload
    log_level = effective_log_level

    if role not in {"public", "admin", "both"}:
        raise typer.BadParameter("role must be 'public', 'admin', or 'both'")

    _apply_db_config(db_cfg)

    public_port = preset_public_port if preset_public_port is not None else base_port
    admin_port = preset_admin_port if preset_admin_port is not None else base_port

    if role == "both" and preset_admin_port is None and port_admin is None:
        admin_port = public_port + 1

    return {
        "role": role,
        "reload": reload,
        "log_level": log_level,
        "public_host": effective_public_host,
        "admin_host": effective_admin_host,
        "public_port": public_port,
        "admin_port": admin_port,
    }


def _container_host(host: str) -> str:
    if host in {"127.0.0.1", "localhost"}:
        return "0.0.0.0"
    return host


def _ensure_dockerfile(path: Path) -> None:
    if path.exists():
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "\n".join(
            [
                "FROM python:3.12-slim",
                "",
                "WORKDIR /app",
                "ENV PYTHONUNBUFFERED=1",
                "",
                "COPY pyproject.toml /app/",
                "COPY src /app/src",
                "",
                "RUN python -m pip install --no-cache-dir .",
            ]
        )
        + "\n"
    )


def _dockerfile_for_context(dockerfile: Path, context: Path) -> str:
    try:
        return str(dockerfile.relative_to(context))
    except ValueError:
        return str(dockerfile)


def _build_image(client: Any, image: str, dockerfile: Path, context: Path) -> None:
    dockerfile_ref = _dockerfile_for_context(dockerfile, context)
    def _consume_build_output(chunks: Any, show_logs: bool) -> None:
        for chunk in chunks:
            if "stream" in chunk:
                line = chunk["stream"].strip()
                if show_logs and line:
                    typer.echo(line)
            if "error" in chunk:
                raise typer.BadParameter(f"Docker build failed: {chunk['error']}")
            if "errorDetail" in chunk and chunk["errorDetail"].get("message"):
                raise typer.BadParameter(f"Docker build failed: {chunk['errorDetail']['message']}")

    try:
        chunks = client.api.build(
            path=str(context),
            dockerfile=dockerfile_ref,
            tag=image,
            rm=True,
            forcerm=True,
            decode=True,
        )
        _consume_build_output(chunks, show_logs=True)
    except Exception as e:
        message = str(e)
        if "configured logging driver does not support reading" in message:
            typer.echo("⚠️  Docker logging driver doesn't support build logs; retrying build quietly.")
            chunks = client.api.build(
                path=str(context),
                dockerfile=dockerfile_ref,
                tag=image,
                rm=True,
                forcerm=True,
                quiet=True,
                decode=True,
            )
            _consume_build_output(chunks, show_logs=False)
            return
        raise typer.BadParameter(f"Docker build failed: {e}") from e


def _put_file_in_container(container: Any, src: Path, dest_path: str) -> None:
    data = src.read_bytes()
    tar_buffer = io.BytesIO()
    dest_posix = PurePosixPath(dest_path)
    base_dir = PurePosixPath("/app")
    if dest_posix.is_absolute() and dest_posix.parts[:2] == base_dir.parts:
        archive_root = str(base_dir)
        archive_name = str(dest_posix.relative_to(base_dir))
    else:
        archive_root = "/"
        archive_name = dest_posix.name
    tar_info = tarfile.TarInfo(name=archive_name)
    tar_info.size = len(data)
    tar_info.mtime = int(src.stat().st_mtime)
    with tarfile.open(fileobj=tar_buffer, mode="w") as tar:
        tar.addfile(tar_info, io.BytesIO(data))
    tar_buffer.seek(0)
    container.put_archive(path=archive_root, data=tar_buffer.read())


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
    protocol: str = typer.Option(
        "http",
        "--protocol",
        help="Public protocol to serve (e.g. http). Ignored for role=admin.",
    ),
    role: str = typer.Option(
        "public",
        "--role",
        "-r",
        help=(
            "Server role: 'public' (dynamic routes / payloads), "
            "'admin' (manage routes/logs), or 'both' (public/admin on separate ports)"
        ),
    ),
    docker: bool = typer.Option(False, "--docker", help="Run the server inside Docker"),
    image: str = typer.Option("reach:local", "--image", help="Docker image tag"),
    name: Optional[str] = typer.Option(None, "--name", help="Container name"),
    dockerfile: Path = typer.Option(Path("Dockerfile"), "--dockerfile", help="Path to Dockerfile"),
    context: Path = typer.Option(Path("."), "--context", help="Build context directory"),
    rebuild: bool = typer.Option(False, "--rebuild/--no-rebuild", help="Rebuild image before running"),
    detach: bool = typer.Option(True, "--detach/--no-detach", help="Run container in background"),
):
    """
    Start the REACH Core server (FastAPI + Uvicorn).

    - role=public (default): dynamic routes / payloads on --port
    - role=admin: admin API on --port
    - role=both: public on --port, admin on --port+1
    """
    import uvicorn
    import importlib
    from multiprocessing import Process

    # Load .env first (highest priority after real env vars)
    _load_dotenv()

    preset_data = _get_preset_data(preset)
    config = _resolve_server_config(
        preset_data,
        host=host,
        port=port,
        port_public=port_public,
        port_admin=port_admin,
        reload=reload,
        log_level=log_level,
        role=role,
    )

    if docker:
        try:
            import docker as docker_sdk
        except Exception as e:
            raise typer.BadParameter("Docker SDK not installed. Add `docker` to dependencies.") from e

        role = config["role"]
        public_port = config["public_port"]
        admin_port = config["admin_port"]

        selected_host = config["public_host"] if role != "admin" else config["admin_host"]
        docker_host = _container_host(selected_host)
        cmd = [
            "reach",
            "server",
            "start",
            "--host",
            docker_host,
            "--role",
            role,
            "--log-level",
            config["log_level"],
            "--protocol",
            protocol,
        ]
        if config["reload"]:
            cmd.append("--reload")
        if role in {"public", "admin"}:
            effective_port = public_port if role == "public" else admin_port
            cmd.extend(["--port", str(effective_port)])
        else:
            cmd.extend(["--port-public", str(public_port), "--port-admin", str(admin_port)])

        preset_path = None
        preset_container_path = None
        if preset:
            preset_path = str(preset.resolve())
            preset_container_path = f"/app/presets/{Path(preset_path).name}"
            cmd.extend(["--preset", preset_container_path])

        ports: Dict[str, int] = {}
        if role == "public":
            ports = {f"{public_port}/tcp": public_port}
        elif role == "admin":
            ports = {f"{admin_port}/tcp": admin_port}
        else:
            ports = {f"{public_port}/tcp": public_port, f"{admin_port}/tcp": admin_port}

        _ensure_dockerfile(dockerfile)
        if not context.exists():
            raise typer.BadParameter(f"Build context not found: {context}")

        env = {key: value for key, value in os.environ.items() if key.startswith("REACH_")}
        client = docker_sdk.from_env()
        image_exists = True
        try:
            client.images.get(image)
        except Exception:
            image_exists = False

        if rebuild or not image_exists:
            typer.echo(f"🐳 Building Docker image {image} ...")
            _build_image(client, image=image, dockerfile=dockerfile, context=context)

        typer.echo(f"🚢 Running REACH Core ({role}) in Docker...")
        container = client.containers.create(
            image,
            command=cmd,
            name=name,
            ports=ports,
            environment=env,
        )

        if preset_path and preset_container_path:
            _put_file_in_container(container, Path(preset_path), preset_container_path)

        container.start()

        if detach:
            typer.echo(f"✅ Container started: {container.name}")
            typer.echo(f"🔎 View logs: docker logs -f {container.name}")
        else:
            try:
                for line in container.logs(stream=True, follow=True):
                    typer.echo(line.decode(errors="ignore").rstrip())
            finally:
                container.wait()
        return

    # Import after applying DB env overrides so engine uses the updated settings
    from reach.core.protocols import get_protocol
    from reach.core.server import init_db as core_init_db

    # Explicit DB init so app import has no side effects
    protocol_entry = None
    # Always ensure core tables exist before starting any protocol.
    core_init_db()
    if role != "admin":
        importlib.import_module(f"reach.core.protocols.{protocol}.server")
        protocol_entry = get_protocol(protocol)
        if protocol_entry.init_db:
            protocol_entry.init_db()

    role = config["role"]
    reload = config["reload"]
    log_level = config["log_level"]
    effective_public_host = config["public_host"]
    effective_admin_host = config["admin_host"]
    public_port = config["public_port"]
    admin_port = config["admin_port"]

    if role in {"public", "admin"}:
        if role == "public":
            if protocol_entry is None:
                importlib.import_module(f"reach.core.protocols.{protocol}.server")
                protocol_entry = get_protocol(protocol)
            target = protocol_entry.public_app
        else:
            target = "reach.core.server:create_admin_app"
        effective_port = public_port if role == "public" else admin_port
        effective_host = effective_public_host if role == "public" else effective_admin_host

        scheme = "http"
        if role == "public" and protocol_entry:
            scheme = protocol_entry.name
        typer.echo(f"🚀 Starting REACH Core {role} server on {scheme}://{effective_host}:{effective_port} ...")
        typer.echo(f"📡 App: {target}")

        if role == "public" and protocol_entry and protocol_entry.server_type != "asgi":
            protocol_entry.run(effective_host, effective_port)
        else:
            uvicorn.run(
                target,
                host=effective_host,
                port=effective_port,
                reload=reload,
                log_level=log_level,
                factory=True,
            )
    else:
        importlib.import_module(f"reach.core.protocols.{protocol}.server")
        protocol_entry = get_protocol(protocol)
        public_target = protocol_entry.public_app
        admin_target = "reach.core.server:create_admin_app"

        public_scheme = protocol_entry.name
        typer.echo(f"🚀 Starting REACH Core public server on {public_scheme}://{effective_public_host}:{public_port} ...")
        typer.echo(f"📡 Public app: {public_target}")
        typer.echo(f"🚀 Starting REACH Core admin server on http://{effective_admin_host}:{admin_port} ...")
        typer.echo(f"📡 Admin app: {admin_target}")

        def run_server(target: str, port_: int) -> None:
            if target == public_target and protocol_entry.server_type != "asgi":
                protocol_entry.run(effective_public_host, port_)
                return
            uvicorn.run(
                target,
                host=effective_public_host if target == public_target else effective_admin_host,
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
