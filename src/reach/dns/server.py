"""Authoritative DNS server with REACH logging integration."""

from __future__ import annotations

import argparse
from datetime import datetime, UTC
import ipaddress
import logging
import time
from typing import Optional

try:
    from dnslib import A, AAAA, CNAME, DNSLabel, DNSRecord, QTYPE, RR, SOA, NS
    from dnslib.server import BaseResolver, DNSServer
except Exception as exc:  # pragma: no cover - optional dependency
    raise RuntimeError("dnslib is required for reach.dns. Install with: pip install dnslib") from exc

from reach.core.app_logging import setup_logging
from reach.core.db.init import init_db
from reach.core import logging as reach_logging

logger = logging.getLogger("reach.dns")


class LoggingResolver(BaseResolver):
    def __init__(
        self,
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
    ) -> None:
        self.domain = DNSLabel(domain.strip("."))
        self.a = a
        self.aaaa = aaaa
        self.ttl = ttl
        self.ns = [DNSLabel(item.strip(".")) for item in ns]
        self.soa_mname = DNSLabel(soa_mname.strip("."))
        self.soa_rname = DNSLabel(soa_rname.strip("."))
        self.soa_serial = soa_serial
        self.soa_refresh = soa_refresh
        self.soa_retry = soa_retry
        self.soa_expire = soa_expire
        self.soa_minimum = soa_minimum

    def resolve(self, request: DNSRecord, handler):  # type: ignore[override]
        reply = request.reply()
        qname = request.q.qname
        qtype = QTYPE[request.q.qtype]
        client_ip = handler.client_address[0]
        now = datetime.now(UTC)

        logger.info("DNS query %s %s from %s", qname, qtype, client_ip)
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug("DNS raw query: %s", request)

        reach_logging.add_log(
            protocol="dns",
            method=qtype,
            path=str(qname),
            route_id=None,
            status_code=None,
            headers={"qtype": qtype},
            query_params={},
            body=None,
            client_ip=client_ip,
            host=str(qname),
        )

        if qname.matchSuffix(self.domain):
            if qtype in ("A", "ANY"):
                reply.add_answer(RR(qname, QTYPE.A, rdata=A(self.a), ttl=self.ttl))
            if self.aaaa and qtype in ("AAAA", "ANY"):
                reply.add_answer(RR(qname, QTYPE.AAAA, rdata=AAAA(self.aaaa), ttl=self.ttl))
            if qtype == "CNAME":
                reply.add_answer(RR(qname, QTYPE.CNAME, rdata=CNAME(str(qname)), ttl=self.ttl))
            if qname == self.domain and qtype in ("NS", "ANY"):
                for ns_name in self.ns:
                    reply.add_answer(RR(qname, QTYPE.NS, rdata=NS(str(ns_name)), ttl=self.ttl))
            if qname == self.domain and qtype in ("SOA", "ANY"):
                reply.add_answer(
                    RR(
                        qname,
                        QTYPE.SOA,
                        rdata=SOA(
                            mname=str(self.soa_mname),
                            rname=str(self.soa_rname),
                            times=(
                                self.soa_serial,
                                self.soa_refresh,
                                self.soa_retry,
                                self.soa_expire,
                                self.soa_minimum,
                            ),
                        ),
                        ttl=self.ttl,
                    )
                )
            if not reply.rr:
                reply.header.rcode = getattr(QTYPE, "NXDOMAIN", 3)
                reply.add_auth(
                    RR(
                        self.domain,
                        QTYPE.SOA,
                        rdata=SOA(
                            mname=str(self.soa_mname),
                            rname=str(self.soa_rname),
                            times=(
                                self.soa_serial,
                                self.soa_refresh,
                                self.soa_retry,
                                self.soa_expire,
                                self.soa_minimum,
                            ),
                        ),
                        ttl=self.ttl,
                    )
                )

        return reply


def _validate_ip(value: str) -> str:
    try:
        ipaddress.ip_address(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(str(exc)) from exc
    return value


def run_dns_server(
    *,
    host: str,
    port: int,
    domain: str,
    a: str,
    aaaa: Optional[str],
    ttl: int,
    tcp: bool,
    ns: list[str],
    soa_mname: str,
    soa_rname: str,
    soa_serial: int,
    soa_refresh: int,
    soa_retry: int,
    soa_expire: int,
    soa_minimum: int,
    log_level: str = "info",
) -> None:
    setup_logging(level=log_level)
    init_db()
    resolver = LoggingResolver(
        domain,
        a,
        aaaa,
        ttl,
        ns=ns,
        soa_mname=soa_mname,
        soa_rname=soa_rname,
        soa_serial=soa_serial,
        soa_refresh=soa_refresh,
        soa_retry=soa_retry,
        soa_expire=soa_expire,
        soa_minimum=soa_minimum,
    )

    udp_server = DNSServer(resolver, port=port, address=host, tcp=False)
    udp_server.start_thread()

    tcp_server = None
    if tcp:
        tcp_server = DNSServer(resolver, port=port, address=host, tcp=True)
        tcp_server.start_thread()

    mode = "udp+tcp" if tcp else "udp"
    logger.info("🚀 Starting REACH DNS server on %s://%s:%s (domain=%s)", mode, host, port, domain)

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("🛑 Shutting down REACH DNS server")


def main() -> int:
    parser = argparse.ArgumentParser(description="REACH authoritative DNS server")
    parser.add_argument("--host", default="0.0.0.0", help="Bind host")
    parser.add_argument("--port", type=int, default=53, help="Bind port")
    parser.add_argument("--domain", required=True, help="Delegated domain (e.g., oob.pntst.net)")
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
    args = parser.parse_args()

    domain = args.domain.strip(".")
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
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
