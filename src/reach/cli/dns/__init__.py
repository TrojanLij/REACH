"""CLI for running the REACH DNS service."""

from __future__ import annotations

import typer

from reach.dns.server import run_dns_server

app = typer.Typer(help="Start the REACH DNS server")


@app.command("serve")
def serve(
    domain: str = typer.Option(..., "--domain", help="Delegated domain (e.g., oob.pntst.net)"),
    host: str = typer.Option("0.0.0.0", "--host", help="Bind host"),
    port: int = typer.Option(53, "--port", help="Bind port"),
    a: str = typer.Option("127.0.0.1", "--a", help="A record IP"),
    aaaa: str | None = typer.Option(None, "--aaaa", help="Optional AAAA record IP"),
    ttl: int = typer.Option(60, "--ttl", help="TTL for answers"),
    tcp: bool = typer.Option(False, "--tcp", help="Also listen on TCP"),
    log_level: str = typer.Option("info", "--log-level", help="Log level (debug, info, warning, error)"),
) -> None:
    """Run the DNS server and log queries into REACH Core."""
    run_dns_server(
        host=host,
        port=port,
        domain=domain,
        a=a,
        aaaa=aaaa,
        ttl=ttl,
        tcp=tcp,
        log_level=log_level,
    )
