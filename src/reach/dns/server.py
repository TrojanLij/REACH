"""Authoritative DNS server with REACH logging integration."""

from __future__ import annotations

import argparse
from datetime import datetime, UTC
import ipaddress
import logging
import queue
import threading
import time
from typing import Callable, Optional

try:
    from dnslib import A, AAAA, DNSLabel, DNSRecord, QTYPE, RR, SOA, NS, RCODE
    from dnslib.server import BaseResolver, DNSServer
except Exception as exc:  # pragma: no cover - optional dependency
    raise RuntimeError("dnslib is required for reach.dns. Install with: pip install dnslib") from exc

from reach.core.app_logging import setup_logging
from reach.core.db.init import init_db
from reach.core.protocols.logging import log_protocol_request
from reach.dns.zones import ZoneConfig, ZoneStore

logger = logging.getLogger("reach.dns")


class LoggingResolver(BaseResolver):
    def __init__(
        self,
        *,
        static_zones: list[ZoneConfig],
        zone_store: ZoneStore | None,
        log_handler: Callable[..., None],
    ) -> None:
        self.static_zones = static_zones
        self.zone_store = zone_store
        self.log_handler = log_handler

    def _zones(self) -> list[ZoneConfig]:
        if self.zone_store is None:
            return list(self.static_zones)
        return self.zone_store.extend(self.static_zones)

    def _select_zone(self, qname: DNSLabel) -> ZoneConfig | None:
        best_match: ZoneConfig | None = None
        for zone in self._zones():
            if qname.matchSuffix(zone.label):
                if best_match is None or zone.depth > best_match.depth:
                    best_match = zone
        return best_match

    def resolve(self, request: DNSRecord, handler):  # type: ignore[override]
        reply = request.reply()
        qname = request.q.qname
        qtype = QTYPE[request.q.qtype]
        client_ip = None
        if handler is not None and getattr(handler, "client_address", None):
            try:
                client_ip = handler.client_address[0]
            except Exception:
                client_ip = None

        logger.info("DNS query %s %s from %s", qname, qtype, client_ip)
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug("DNS raw query: %s", request)

        zone = self._select_zone(qname)
        self.log_handler(
            protocol="dns",
            method=qtype,
            path=str(qname),
            command=None,
            route_id=None,
            status_code=None,
            headers={"qtype": qtype, "zone": zone.zone if zone else ""},
            query_params={},
            body=None,
            client_ip=client_ip,
            host=str(qname),
        )

        if zone is not None:
            is_apex = qname == zone.label
            answer_any_name = zone.wildcard or is_apex
            if qtype in ("A", "ANY"):
                if answer_any_name:
                    reply.add_answer(RR(qname, QTYPE.A, rdata=A(zone.a), ttl=zone.ttl))
            if zone.aaaa and qtype in ("AAAA", "ANY"):
                if answer_any_name:
                    reply.add_answer(RR(qname, QTYPE.AAAA, rdata=AAAA(zone.aaaa), ttl=zone.ttl))
            if is_apex and qtype in ("NS", "ANY"):
                for ns_name in zone.ns:
                    reply.add_answer(RR(qname, QTYPE.NS, rdata=NS(str(ns_name)), ttl=zone.ttl))
            if is_apex and qtype in ("SOA", "ANY"):
                reply.add_answer(
                    RR(
                        qname,
                        QTYPE.SOA,
                        rdata=SOA(
                            mname=str(zone.soa_mname),
                            rname=str(zone.soa_rname),
                            times=(
                                zone.soa_serial,
                                zone.soa_refresh,
                                zone.soa_retry,
                                zone.soa_expire,
                                zone.soa_minimum,
                            ),
                        ),
                        ttl=zone.ttl,
                    )
                )
            if not reply.rr:
                reply.header.rcode = RCODE.NOERROR
                reply.add_auth(
                    RR(
                        zone.label,
                        QTYPE.SOA,
                        rdata=SOA(
                            mname=str(zone.soa_mname),
                            rname=str(zone.soa_rname),
                            times=(
                                zone.soa_serial,
                                zone.soa_refresh,
                                zone.soa_retry,
                                zone.soa_expire,
                                zone.soa_minimum,
                            ),
                        ),
                        ttl=zone.ttl,
                    )
                )
        else:
            reply.header.rcode = RCODE.REFUSED

        return reply


def _validate_ip(value: str) -> str:
    try:
        ipaddress.ip_address(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(str(exc)) from exc
    return value


def _normalize_zone(zone: str) -> str:
    return zone.strip(".").lower()


def _zone_depth(zone: str) -> int:
    return len(zone.split(".")) if zone else 0


def _build_static_zone(
    *,
    domain: str,
    a: str,
    aaaa: Optional[str],
    ttl: int,
    ns: list[str],
    soa_mname: str,
    soa_rname: str,
    soa_serial: int,
    soa_refresh: int,
    soa_retry: int,
    soa_expire: int,
    soa_minimum: int,
    wildcard: bool,
) -> ZoneConfig:
    zone = _normalize_zone(domain)
    return ZoneConfig(
        zone=zone,
        label=DNSLabel(zone),
        depth=_zone_depth(zone),
        a=a,
        aaaa=aaaa,
        ttl=ttl,
        ns=[item.strip(".").lower() for item in ns],
        soa_mname=soa_mname.strip(".").lower(),
        soa_rname=soa_rname.strip(".").lower(),
        soa_serial=soa_serial,
        soa_refresh=soa_refresh,
        soa_retry=soa_retry,
        soa_expire=soa_expire,
        soa_minimum=soa_minimum,
        wildcard=wildcard,
    )


def _start_log_worker(log_queue: queue.Queue[dict]) -> threading.Thread:
    """Start a background log writer for DNS requests."""
    def _worker() -> None:
        while True:
            item = log_queue.get()
            if item is None:
                break
            try:
                log_protocol_request(**item)
            except Exception:
                logger.exception("Failed to write DNS log entry")
            finally:
                log_queue.task_done()

    thread = threading.Thread(target=_worker, name="reach-dns-log-worker", daemon=True)
    thread.start()
    return thread


def _make_log_handler(*, async_logging: bool, queue_size: int) -> tuple[Callable[..., None], queue.Queue | None]:
    """Return a log handler; optionally buffered to avoid blocking DNS responses."""
    if not async_logging:
        return log_protocol_request, None

    log_queue: queue.Queue[dict] = queue.Queue(maxsize=queue_size)
    _start_log_worker(log_queue)
    dropped_counter = {"count": 0}
    last_warn = {"ts": 0.0}

    def _log_handler(**kwargs) -> None:
        try:
            log_queue.put_nowait(kwargs)
        except queue.Full:
            dropped_counter["count"] += 1
            now = time.monotonic()
            if now - last_warn["ts"] > 5:
                last_warn["ts"] = now
                logger.warning("DNS log queue full; dropped %d entries", dropped_counter["count"])

    return _log_handler, log_queue


def run_dns_server(
    *,
    host: str,
    port: int,
    domain: str | None,
    a: str | None,
    aaaa: Optional[str],
    ttl: int,
    tcp: bool,
    ns: list[str] | None,
    soa_mname: str | None,
    soa_rname: str | None,
    soa_serial: int | None,
    soa_refresh: int,
    soa_retry: int,
    soa_expire: int,
    soa_minimum: int,
    log_level: str = "info",
    async_logging: bool = False,
    log_queue_size: int = 1000,
    wildcard: bool = True,
    use_db_zones: bool = True,
    zones_refresh: float = 2.0,
) -> None:
    setup_logging(level=log_level)
    init_db()
    log_handler, log_queue = _make_log_handler(
        async_logging=async_logging,
        queue_size=log_queue_size,
    )
    static_zones: list[ZoneConfig] = []
    if domain:
        if not a:
            raise ValueError("A record value is required when --domain is set")
        norm_domain = _normalize_zone(domain)
        ns_list = ns or [f"ns1.{norm_domain}", f"ns2.{norm_domain}"]
        soa_mname = soa_mname or ns_list[0]
        soa_rname = soa_rname or f"hostmaster.{norm_domain}"
        soa_serial = soa_serial or int(datetime.now(UTC).timestamp())
        static_zones.append(
            _build_static_zone(
                domain=norm_domain,
                a=a,
                aaaa=aaaa,
                ttl=ttl,
                ns=ns_list,
                soa_mname=soa_mname,
                soa_rname=soa_rname,
                soa_serial=soa_serial,
                soa_refresh=soa_refresh,
                soa_retry=soa_retry,
                soa_expire=soa_expire,
                soa_minimum=soa_minimum,
                wildcard=wildcard,
            )
        )

    zone_store = ZoneStore(refresh_interval=zones_refresh) if use_db_zones else None
    resolver = LoggingResolver(
        static_zones=static_zones,
        zone_store=zone_store,
        log_handler=log_handler,
    )

    udp_server = DNSServer(resolver, port=port, address=host, tcp=False)
    udp_server.start_thread()

    tcp_server = None
    if tcp:
        tcp_server = DNSServer(resolver, port=port, address=host, tcp=True)
        tcp_server.start_thread()

    mode = "udp+tcp" if tcp else "udp"
    zone_sources: list[str] = []
    if static_zones:
        zone_sources.append("static")
    if use_db_zones:
        zone_sources.append("db")
    zone_desc = "+".join(zone_sources) if zone_sources else "none"
    logger.info("🚀 Starting REACH DNS server on %s://%s:%s (zones=%s)", mode, host, port, zone_desc)
    if not static_zones and not use_db_zones:
        logger.warning("No DNS zones configured; all queries will be refused")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("🛑 Shutting down REACH DNS server")
    finally:
        if log_queue is not None:
            try:
                log_queue.put_nowait(None)
            except Exception:
                pass


def main() -> int:
    parser = argparse.ArgumentParser(description="REACH authoritative DNS server")
    parser.add_argument("--host", default="0.0.0.0", help="Bind host")
    parser.add_argument("--port", type=int, default=53, help="Bind port")
    parser.add_argument("--domain", help="Delegated domain (e.g., oob.pntst.net)")
    parser.add_argument("--a", type=_validate_ip, default="127.0.0.1", help="A record IP")
    parser.add_argument("--aaaa", type=_validate_ip, help="Optional AAAA record IP")
    parser.add_argument("--ttl", type=int, default=60, help="TTL for answers")
    parser.add_argument("--tcp", action="store_true", help="Also listen on TCP")
    parser.add_argument(
        "--ns",
        action="append",
        help="Authoritative NS hostname (repeatable). Defaults to ns1.<domain> and ns2.<domain>.",
    )
    parser.add_argument("--soa-mname", help="SOA primary NS (defaults to ns1.<domain>)")
    parser.add_argument("--soa-rname", help="SOA admin email (dots instead of @)")
    parser.add_argument("--soa-serial", type=int, help="SOA serial (defaults to current epoch)")
    parser.add_argument("--soa-refresh", type=int, default=3600, help="SOA refresh")
    parser.add_argument("--soa-retry", type=int, default=600, help="SOA retry")
    parser.add_argument("--soa-expire", type=int, default=1209600, help="SOA expire")
    parser.add_argument("--soa-minimum", type=int, default=300, help="SOA minimum")
    parser.add_argument("--log-level", default="info", help="Log level (debug, info, warning, error)")
    parser.add_argument(
        "--async-logging",
        action="store_true",
        help="Log DNS queries asynchronously to avoid blocking responses",
    )
    parser.add_argument(
        "--log-queue-size",
        type=int,
        default=1000,
        help="Max queued DNS log entries when --async-logging is enabled",
    )
    parser.add_argument(
        "--strict-zone",
        action="store_true",
        help="Only answer A/AAAA for the zone apex (disable wildcard subdomains)",
    )
    parser.add_argument(
        "--db-zones",
        dest="db_zones",
        action="store_true",
        default=True,
        help="Load zones from the REACH database (default)",
    )
    parser.add_argument(
        "--no-db-zones",
        dest="db_zones",
        action="store_false",
        help="Disable loading zones from the REACH database",
    )
    parser.add_argument(
        "--zones-refresh",
        type=float,
        default=5.0,
        help="Zone refresh interval in seconds when using DB zones",
    )
    args = parser.parse_args()

    domain = args.domain.strip(".") if args.domain else None
    if not domain and not args.db_zones:
        raise SystemExit("Either --domain or --db-zones must be set")
    ns_list = None
    soa_mname = None
    soa_rname = None
    soa_serial = None
    if domain:
        ns_list = args.ns or [f"ns1.{domain}", f"ns2.{domain}"]
        soa_mname = args.soa_mname or ns_list[0]
        soa_rname = args.soa_rname or f"hostmaster.{domain}"
        soa_serial = args.soa_serial or int(datetime.now(UTC).timestamp())

    run_dns_server(
        host=args.host,
        port=args.port,
        domain=domain,
        a=args.a,
        aaaa=args.aaaa,
        ttl=args.ttl,
        tcp=args.tcp,
        ns=ns_list,
        soa_mname=soa_mname,
        soa_rname=soa_rname,
        soa_serial=soa_serial,
        soa_refresh=args.soa_refresh,
        soa_retry=args.soa_retry,
        soa_expire=args.soa_expire,
        soa_minimum=args.soa_minimum,
        log_level=args.log_level,
        async_logging=args.async_logging,
        log_queue_size=args.log_queue_size,
        wildcard=not args.strict_zone,
        use_db_zones=args.db_zones,
        zones_refresh=args.zones_refresh,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
