from __future__ import annotations

from pathlib import Path
import random

import typer
from rich.console import Console

from . import app
from reach.core.client import CoreClient
from reach.forge.api import ForgeController, generate_generator
from .deps import (
    build_dependency_reports,
    install_missing_python_dependencies,
    print_dependency_reports,
)
from .help import forge_list_generators


def _parse_generator_kwargs(items: list[str]) -> dict[str, str]:
    parsed: dict[str, str] = {}
    for item in items:
        if "=" not in item:
            raise typer.BadParameter(
                f"Invalid generator kwarg {item!r}; expected KEY=VALUE."
            )
        key, value = item.split("=", 1)
        key = key.strip()
        if not key:
            raise typer.BadParameter(
                f"Invalid generator kwarg {item!r}; expected non-empty KEY."
            )
        parsed[key] = value
    return parsed


def _parse_headers(items: list[str]) -> dict[str, str]:
    parsed: dict[str, str] = {}
    for item in items:
        if "=" not in item:
            raise typer.BadParameter(
                f"Invalid header {item!r}; expected KEY=VALUE."
            )
        key, value = item.split("=", 1)
        key = key.strip()
        if not key:
            raise typer.BadParameter(
                f"Invalid header {item!r}; expected non-empty KEY."
            )
        parsed[key] = value
    return parsed


def _has_header(headers: dict[str, str], name: str) -> bool:
    name_lower = name.lower()
    return any(k.lower() == name_lower for k in headers)


def _load_server_header_value(path: Path) -> str:
    if not path.exists():
        raise typer.BadParameter(f"Header file not found: {path}")

    values: list[str] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        raw = line.strip()
        if not raw or raw.startswith("#"):
            continue
        if ":" in raw:
            key, value = raw.split(":", 1)
            if key.strip().lower() == "server":
                raw = value.strip()
        elif "=" in raw:
            key, value = raw.split("=", 1)
            if key.strip().lower() == "server":
                raw = value.strip()
        if raw:
            values.append(raw)

    if not values:
        raise typer.BadParameter(f"No usable Server header values in {path}")

    return random.choice(values)


generator_app = typer.Typer(help="Forge generator management")
app.add_typer(generator_app, name="generator")
# Backward-compatible alias.
app.add_typer(generator_app, name="payload")


@generator_app.callback(invoke_without_command=True)
def generator_callback(
    ctx: typer.Context,
    list_kinds: bool = typer.Option(
        False,
        "--list",
        help="List generator kinds (optionally with --kind for details).",
    ),
    kind: str | None = typer.Option(
        None,
        "--kind",
        help="Generator kind to describe (use with --list).",
    ),
) -> None:
    if list_kinds:
        forge_list_generators(kind=kind)
        raise typer.Exit()

    if ctx.invoked_subcommand is None:
        typer.echo(ctx.get_help())
        raise typer.Exit()


@generator_app.command("new")
def create_generated_route(
    kind: str = typer.Argument(..., help="Generator kind (e.g., xss_basic, xxe_external_entity)"),
    endpoint: str | None = typer.Option(
        None,
        "--endpoint",
        "-e",
        help="Route path to create (e.g., /test/endpoint). Required unless --dry-run.",
    ),
    method: str = typer.Option("GET", "--method", "-m", help="HTTP method for the route"),
    status: int = typer.Option(200, "--status", "-s", help="HTTP status code for the route"),
    content_type: str = typer.Option("text/html", "--content-type", "-c", help="Content-Type for the response"),
    header: list[str] = typer.Option(
        None,
        "--header",
        "-H",
        help="Response header as KEY=VALUE (repeatable).",
    ),
    server_header_file: Path | None = typer.Option(
        None,
        "--server-header-file",
        help="Path to a file of Server header values (one per line).",
    ),
    core_url: str = typer.Option("http://127.0.0.1:8001", "--core-url", help="Admin API base URL"),
    token: str | None = typer.Option(None, "--token", help="Bearer token for admin API (if configured) [not yet working]"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Generate output only; do not create a route"),
    generator_kwarg: list[str] = typer.Option(
        None,
        "--generator-kwarg",
        "--gk",
        help="Generator-specific args as KEY=VALUE.",
    ),
) -> None:
    """
    Generate output and (optionally) create a dynamic route serving it.

    Example:
      reach forge generator new xss_gh0st --endpoint /xss --generator-kwarg command=id
    """
    console = Console()

    if not dry_run and endpoint is None:
        raise typer.BadParameter("Missing --endpoint. Provide a route path or use --dry-run.")

    generator_kwargs = _parse_generator_kwargs(generator_kwarg or [])
    headers = _parse_headers(header or [])
    if server_header_file and not _has_header(headers, "server"):
        headers["Server"] = _load_server_header_value(server_header_file)

    norm_endpoint = None
    if endpoint is not None:
        norm_endpoint = endpoint if endpoint.startswith("/") else f"/{endpoint}"
        if len(norm_endpoint) > 1 and norm_endpoint.endswith("/"):
            norm_endpoint = norm_endpoint.rstrip("/")

    try:
        output = generate_generator(kind, **generator_kwargs)
    except Exception as e:
        console.print(f"[red]Error generating output:[/red] {e}")
        raise typer.Exit(code=1)

    if dry_run:
        console.print(f"[green]Generator Output ({kind}):[/green]\n{output.value}")
        return

    try:
        client = CoreClient(core_url, token=token)
        controller = ForgeController(client)
        result = controller.create_route_with_generator(
            kind=kind,
            path=norm_endpoint or "",
            method=method,
            status_code=status,
            content_type=content_type,
            headers=headers,
            **generator_kwargs,
        )
    except Exception as e:
        console.print(f"[red]Error creating route:[/red] {e}")
        raise typer.Exit(code=1)

    route = result["route"]
    generated = result["generator"]
    console.print("[green]Route created[/green]")
    console.print(f"\tID: {route.get('id')}")
    console.print(f"\tMethod: {route.get('method')}")
    console.print(f"\tPath: /{route.get('path')}")
    console.print(f"\tStatus: {route.get('status_code')}")
    console.print(f"\tContent-Type: {route.get('content_type')}")
    console.print(f"\tHeaders: {route.get('headers')}")

    if len(generated.value) < 100:
        console.print(f"[green]Generator Output ({kind}):[/green]")
        console.print(generated.value)
    else:
        console.print(
            f"[green]Generated output is '{len(generated.value)}' characters long; omitted here.[/green]"
        )


@generator_app.command("check")
def check_generator_dependencies(
    kind: str | None = typer.Option(
        None,
        "--kind",
        help="Generator kind to check.",
    ),
    all_kinds: bool = typer.Option(
        False,
        "--all",
        help="Check dependency status for all generator plugins.",
    ),
) -> None:
    """Check dependency status for generator plugins."""
    console = Console()
    try:
        reports = build_dependency_reports(
            plugin_type="generator",
            kind=kind,
            all_kinds=all_kinds,
        )
    except ValueError as e:
        console.print(f"[red]Dependency check error:[/red] {e}")
        raise typer.Exit(code=1)

    all_ok = print_dependency_reports(console, reports)
    if not all_ok:
        raise typer.Exit(code=1)


@generator_app.command("install")
def install_generator_dependencies(
    kind: str | None = typer.Option(
        None,
        "--kind",
        help="Generator kind to install deps for.",
    ),
    all_kinds: bool = typer.Option(
        False,
        "--all",
        help="Install deps for all generator plugins.",
    ),
    python_bin: str = typer.Option(
        "python3",
        "--python-bin",
        help="Python executable used for pip install.",
    ),
    upgrade: bool = typer.Option(
        False,
        "--upgrade",
        help="Pass --upgrade to pip install.",
    ),
    dry_run: bool = typer.Option(
        False,
        "--dry-run",
        help="Show install command without executing.",
    ),
) -> None:
    """Install missing Python dependencies for generator plugins."""
    console = Console()
    try:
        reports = build_dependency_reports(
            plugin_type="generator",
            kind=kind,
            all_kinds=all_kinds,
        )
    except ValueError as e:
        console.print(f"[red]Dependency install error:[/red] {e}")
        raise typer.Exit(code=1)

    print_dependency_reports(console, reports)
    cmd, code = install_missing_python_dependencies(
        reports=reports,
        python_bin=python_bin,
        upgrade=upgrade,
        dry_run=dry_run,
    )
    if not cmd:
        console.print("[green]No missing Python dependencies to install.[/green]")
        return

    console.print(f"[cyan]Install command:[/cyan] {' '.join(cmd)}")
    if dry_run:
        return

    if code != 0:
        console.print(f"[red]pip install failed with exit code {code}[/red]")
        raise typer.Exit(code=code)

    console.print("[green]Dependency install completed.[/green]")
