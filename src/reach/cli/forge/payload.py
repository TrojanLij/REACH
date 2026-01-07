from __future__ import annotations

import typer
from rich.console import Console

from . import app
from reach.core.client import CoreClient
from reach.forge.api import ForgeController, generate_payload


def _parse_payload_kwargs(items: list[str]) -> dict[str, str]:
    parsed: dict[str, str] = {}
    for item in items:
        if "=" not in item:
            raise typer.BadParameter(
                f"Invalid payload kwarg {item!r}; expected KEY=VALUE."
            )
        key, value = item.split("=", 1)
        key = key.strip()
        if not key:
            raise typer.BadParameter(
                f"Invalid payload kwarg {item!r}; expected non-empty KEY."
            )
        parsed[key] = value
    return parsed


payload_app = typer.Typer(help="Forge payload management")
app.add_typer(payload_app, name="payload")


@payload_app.callback(invoke_without_command=True)
def payload_callback(ctx: typer.Context) -> None:
    if ctx.invoked_subcommand is None:
        typer.echo(ctx.get_help())
        raise typer.Exit()


@payload_app.command("new")
def create_payload_route(
    kind: str = typer.Argument(..., help="Payload kind (e.g., xss_basic, xxe_external_entity)"),
    endpoint: str | None = typer.Option(
        None,
        "--endpoint",
        "-e",
        help="Route path to create (e.g., /test/endpoint). Required unless --dry-run.",
    ),
    method: str = typer.Option("GET", "--method", "-m", help="HTTP method for the route"),
    status: int = typer.Option(200, "--status", "-s", help="HTTP status code for the route"),
    content_type: str = typer.Option("text/html", "--content-type", "-c", help="Content-Type for the response"),
    core_url: str = typer.Option("http://127.0.0.1:8001", "--core-url", help="Admin API base URL"),
    token: str | None = typer.Option(None, "--token", help="Bearer token for admin API (if configured) [not yet working]"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Generate payload only; do not create a route"),
    payload_kwarg: list[str] = typer.Option(
        None,
        "--payload-kwarg",
        "--payload-kwargs",
        help="Payload-specific args as KEY=VALUE (repeatable; later duplicates win).",
    ),
) -> None:
    """
    Generate a payload and (optionally) create a dynamic route serving it.

    Example:
      reach forge payload new xss_gh0st --endpoint /xss --payload-kwarg command=id
    """
    console = Console()

    if not dry_run and endpoint is None:
        raise typer.BadParameter("Missing --endpoint. Provide a route path or use --dry-run.")

    payload_kwargs = _parse_payload_kwargs(payload_kwarg or [])

    # Normalize endpoint: ensure leading slash, trim trailing slash except root
    norm_endpoint = None
    if endpoint is not None:
        norm_endpoint = endpoint if endpoint.startswith("/") else f"/{endpoint}"
        if len(norm_endpoint) > 1 and norm_endpoint.endswith("/"):
            norm_endpoint = norm_endpoint.rstrip("/")

    # Generate payload first so dry-run can return it
    try:
        payload = generate_payload(kind, **payload_kwargs)
    except Exception as e:
        console.print(f"[red]Error generating payload:[/red] {e}")
        raise typer.Exit(code=1)

    if dry_run:
        console.print(f"[green]Payload ({kind}):[/green]\n{payload.value}")
        return

    try:
        client = CoreClient(core_url, token=token)
        controller = ForgeController(client)
        result = controller.create_route_with_payload(
            kind=kind,
            path=norm_endpoint or "",
            method=method,
            status_code=status,
            content_type=content_type,
            **payload_kwargs,
        )
    except Exception as e:
        console.print(f"[red]Error creating route:[/red] {e}")
        raise typer.Exit(code=1)

    route = result["route"]
    console.print("[green]Route created[/green]")
    console.print(f"\tID: {route.get('id')}")
    console.print(f"\tMethod: {route.get('method')}")
    console.print(f"\tPath: /{route.get('path')}")
    console.print(f"\tStatus: {route.get('status_code')}")
    console.print(f"\tContent-Type: {route.get('content_type')}")

    if len(result["payload"].value) < 100:
        console.print(f"[green]Payload ({kind}):[/green]")
        console.print(result["payload"].value)
    else:
        console.print(f"[green]Payload Created but it is '{len(result["payload"].value)}' characters long... so I wont show it here.[/green]")
