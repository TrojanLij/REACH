#!/usr/bin/env python3
"""Minimal authoritative DNS test server with logging.

Requires: pip install dnslib

Example:
  python scripts/dns_test_server.py --host 127.0.0.1 --port 5353 --domain oob.pntst.net

Then query:
  dig @127.0.0.1 -p 5353 token.oob.pntst.net A
"""

from __future__ import annotations

import argparse
from datetime import datetime, UTC
import ipaddress
import json
import sys
import time
import urllib.request
from typing import Optional

from dnslib import A, AAAA, CNAME, DNSLabel, DNSRecord, QTYPE, RR
from dnslib.server import BaseResolver, DNSServer


class LoggingResolver(BaseResolver):
    def __init__(
        self,
        domain: str,
        a: str,
        aaaa: Optional[str],
        ttl: int,
        reach_url: Optional[str],
        reach_timeout: float,
    ) -> None:
        self.domain = DNSLabel(domain.strip("."))
        self.a = a
        self.aaaa = aaaa
        self.ttl = ttl
        self.reach_url = reach_url
        self.reach_timeout = reach_timeout

    def resolve(self, request: DNSRecord, handler):  # type: ignore[override]
        reply = request.reply()
        qname = request.q.qname
        qtype = QTYPE[request.q.qtype]
        client_ip = handler.client_address[0]
        now = datetime.now(UTC)

        print(f"{now} {client_ip} {qname} {qtype}")
        self._maybe_send_to_reach(
            {
                "timestamp": now.isoformat(),
                "client_ip": client_ip,
                "qname": str(qname),
                "qtype": qtype,
            }
        )

        # Only answer within the delegated domain
        if qname.matchSuffix(self.domain):
            if qtype in ("A", "ANY"):
                reply.add_answer(RR(qname, QTYPE.A, rdata=A(self.a), ttl=self.ttl))
            if self.aaaa and qtype in ("AAAA", "ANY"):
                reply.add_answer(RR(qname, QTYPE.AAAA, rdata=AAAA(self.aaaa), ttl=self.ttl))
            if qtype == "CNAME":
                reply.add_answer(RR(qname, QTYPE.CNAME, rdata=CNAME(str(qname)), ttl=self.ttl))
        return reply

    def _maybe_send_to_reach(self, payload: dict[str, str]) -> None:
        if not self.reach_url:
            return
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            self.reach_url,
            data=data,
            headers={"Content-Type": "application/json", "User-Agent": "reach-dns-test/1.0"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=self.reach_timeout):
                return
        except Exception as exc:
            print(f"reach: post failed: {exc}")


def _validate_ip(value: str) -> str:
    try:
        ipaddress.ip_address(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(str(exc)) from exc
    return value


def main() -> int:
    parser = argparse.ArgumentParser(description="Test DNS server with logging")
    parser.add_argument("--host", default="127.0.0.1", help="Bind host")
    parser.add_argument("--port", type=int, default=5353, help="Bind port (avoid 53)")
    parser.add_argument("--domain", required=True, help="Delegated domain (e.g., oob.pntst.net)")
    parser.add_argument("--a", type=_validate_ip, default="127.0.0.1", help="A record IP")
    parser.add_argument("--aaaa", type=_validate_ip, help="Optional AAAA record IP")
    parser.add_argument("--ttl", type=int, default=60, help="TTL for answers")
    parser.add_argument(
        "--reach-url",
        help="Optional REACH public endpoint to post logs (e.g., http://127.0.0.1:8000/oob/dns)",
    )
    parser.add_argument("--reach-timeout", type=float, default=2.0, help="HTTP timeout (seconds)")
    args = parser.parse_args()

    resolver = LoggingResolver(
        args.domain,
        args.a,
        args.aaaa,
        args.ttl,
        args.reach_url,
        args.reach_timeout,
    )
    server = DNSServer(resolver, port=args.port, address=args.host, tcp=False)

    server.start_thread()
    print(f"listening on {args.host}:{args.port} for domain {args.domain}")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nshutting down")
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
