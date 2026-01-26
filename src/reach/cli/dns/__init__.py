"""CLI for running the REACH DNS service."""

from __future__ import annotations

from datetime import datetime, UTC
import os
import sys

import typer

from reach.dns.server import _validate_ip, run_dns_server

app = typer.Typer(help="Run the REACH DNS service (authoritative, OOB-friendly)")


def _validate_ip_optional(value: str | None) -> str | None:
    if value is None:
        return None
    return _validate_ip(value)


def _daemonize(pidfile: str | None) -> None:
    if os.name != "posix":
        raise typer.BadParameter("--daemon is only supported on POSIX systems")
    if os.fork() > 0:
        raise SystemExit(0)
    os.setsid()
    if os.fork() > 0:
        raise SystemExit(0)
    sys.stdout.flush()
    sys.stderr.flush()
    with open(os.devnull, "rb") as devnull:
        os.dup2(devnull.fileno(), 0)
    with open(os.devnull, "ab") as devnull:
        os.dup2(devnull.fileno(), 1)
        os.dup2(devnull.fileno(), 2)
    if pidfile:
        with open(pidfile, "w", encoding="utf-8") as handle:
            handle.write(str(os.getpid()))


@app.command("serve")
def serve(
    domain: str | None = typer.Option(
        None,
        "--domain",
        help="Delegated domain (e.g., oob.pntst.net). Optional when using DB zones.",
    ),
    host: str = typer.Option("0.0.0.0", "--host", help="Bind host"),
    port: int = typer.Option(53, "--port", help="Bind port"),
    a: str = typer.Option(
        "127.0.0.1",
        "--a",
        help="A record IP",
        callback=_validate_ip,
    ),
    aaaa: str | None = typer.Option(
        None,
        "--aaaa",
        help="Optional AAAA record IP",
        callback=_validate_ip_optional,
    ),
    ttl: int = typer.Option(60, "--ttl", help="TTL for answers"),
    tcp: bool = typer.Option(False, "--tcp", help="Also listen on TCP"),
    ns: list[str] | None = typer.Option(
        None,
        "--ns",
        help="Authoritative NS hostname (repeatable). Defaults to ns1.<domain> and ns2.<domain>.",
    ),
    soa_mname: str | None = typer.Option(
        None,
        "--soa-mname",
        help="SOA primary NS (defaults to ns1.<domain>)",
    ),
    soa_rname: str | None = typer.Option(
        None,
        "--soa-rname",
        help="SOA admin email (dots instead of @)",
    ),
    soa_serial: int | None = typer.Option(
        None,
        "--soa-serial",
        help="SOA serial (defaults to current epoch)",
    ),
    soa_refresh: int = typer.Option(3600, "--soa-refresh", help="SOA refresh"),
    soa_retry: int = typer.Option(600, "--soa-retry", help="SOA retry"),
    soa_expire: int = typer.Option(1209600, "--soa-expire", help="SOA expire"),
    soa_minimum: int = typer.Option(300, "--soa-minimum", help="SOA minimum"),
    log_level: str = typer.Option("info", "--log-level", help="Log level (debug, info, warning, error)"),
    async_logging: bool = typer.Option(
        False,
        "--async-logging",
        help="Log DNS queries asynchronously to avoid blocking responses",
    ),
    log_queue_size: int = typer.Option(
        1000,
        "--log-queue-size",
        help="Max queued DNS log entries when --async-logging is enabled",
    ),
    strict_zone: bool = typer.Option(
        False,
        "--strict-zone",
        help="Only answer A/AAAA for the zone apex (disable wildcard subdomains)",
    ),
    db_zones: bool = typer.Option(
        True,
        "--db-zones/--no-db-zones",
        help="Load zones from the REACH database",
    ),
    zones_refresh: float = typer.Option(
        2.0,
        "--zones-refresh",
        help="Zone refresh interval in seconds when using DB zones",
    ),
    daemon: bool = typer.Option(
        False,
        "--daemon",
        help="Run the DNS server in the background (POSIX only)",
    ),
    pidfile: str | None = typer.Option(
        None,
        "--pidfile",
        help="Write the daemon PID to this file",
    ),
) -> None:
    """Run the DNS server and log queries into REACH Core."""
    if daemon:
        _daemonize(pidfile)

    domain = domain.strip(".") if domain else None
    if not domain and not db_zones:
        raise typer.BadParameter("Either --domain or --db-zones must be set")
    ns_list = None
    if domain:
        ns_list = ns or [f"ns1.{domain}", f"ns2.{domain}"]
        soa_mname = soa_mname or ns_list[0]
        soa_rname = soa_rname or f"hostmaster.{domain}"
        soa_serial = soa_serial or int(datetime.now(UTC).timestamp())
    else:
        soa_mname = None
        soa_rname = None
        soa_serial = None

    run_dns_server(
        host=host,
        port=port,
        domain=domain,
        a=a,
        aaaa=aaaa,
        ttl=ttl,
        tcp=tcp,
        ns=ns_list,
        soa_mname=soa_mname,
        soa_rname=soa_rname,
        soa_serial=soa_serial,
        soa_refresh=soa_refresh,
        soa_retry=soa_retry,
        soa_expire=soa_expire,
        soa_minimum=soa_minimum,
        log_level=log_level,
        async_logging=async_logging,
        log_queue_size=log_queue_size,
        wildcard=not strict_zone,
        use_db_zones=db_zones,
        zones_refresh=zones_refresh,
    )
