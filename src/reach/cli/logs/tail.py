# reach/cli/logs/tail.py
from __future__ import annotations

import time
import re

import httpx
import typer
from rich.console import Console

from . import app


@app.command("tail")
def tail_logs(
    core_url: str = typer.Option(
        "http://127.0.0.1:8000",
        "--core-url",
        help="Base URL of REACH Core server",
    ),
    interval: float = typer.Option(
        1.0,
        "--interval",
        "-i",
        help="Polling interval in seconds",
    ),
    once: bool = typer.Option(
        False,
        "--once",
        help="Fetch logs once and exit (no streaming).",
    ),
    regex: str | None = typer.Option(
        None,
        "--regex",
        help="Only show log entries where this regex matches (method/path/status/ip/host/body).",
    ),
) -> None:
    """
    Stream inbound requests (and status) from REACH Core, like `tail -f`.

    If --regex is provided, only matching entries are shown.
    """
    console = Console()
    last_id = 0

    pattern = None
    if regex:
        try:
            pattern = re.compile(regex)
        except re.error as e:
            console.print(f"[red]Invalid regex:[/red] {e}")
            raise typer.Exit(code=1)

    console.print(f"[cyan]Streaming logs from[/cyan] {core_url} (Ctrl+C to stop)")

    with httpx.Client(base_url=core_url, timeout=5.0) as client:
        while True:
            try:
                resp = client.get(
                    "/api/logs",
                    params={"since_id": last_id, "limit": 200},
                    headers={"REACHTailLogServer": "True"},
                )
                resp.raise_for_status()
            except Exception as e:
                console.print(f"[red]Error fetching logs:[/red] {e}")
                if once:
                    break
                time.sleep(interval)
                continue

            logs = resp.json()
            if logs:
                for entry in logs:
                    if entry["id"] > last_id:
                        last_id = entry["id"]

                    ts = entry["timestamp"]
                    method = entry["method"]
                    path = entry["path"]
                    status = entry.get("status_code")
                    route_id = entry.get("route_id")
                    client_ip = entry.get("client_ip") or "-"
                    host = entry.get("host") or "-"
                    body = entry.get("body") or ""
                    query_params = entry.get("query_params") or {}

                    text_for_match = " ".join(
                        str(x)
                        for x in [
                            method,
                            path,
                            status,
                            route_id,
                            client_ip,
                            host,
                            body,
                        ]
                    )

                    if pattern is not None and not pattern.search(text_for_match):
                        continue

                    console.print(
                        f"[bold]{entry['id']:>5}[/bold] "
                        f"[dim]{ts}[/dim] "
                        f"[green]{method:<6}[/green] "
                        f"{path} "
                        f"-> [yellow]{status}[/yellow] "
                        f"(route_id={route_id}, ip={client_ip}, host={host})"
                    )

                    # For GET requests, also show query parameters (if any)
                    if method.upper() == "GET" and isinstance(query_params, dict) and query_params:
                        for key, value in query_params.items():
                            console.print(f"\t{key}={value}")

                    # For POST/PUT/PATCH, show body (if any)
                    if method.upper() in {"POST", "PUT", "PATCH"} and body:
                        console.print("\t[body]")
                        for line in str(body).splitlines():
                            console.print(f"\t{line}")

            if once:
                break

            time.sleep(interval)
