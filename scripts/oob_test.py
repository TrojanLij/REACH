#!/usr/bin/env python3
"""Minimal DNS + HTTP probe for testing OOB logging.

Usage example:
  python scripts/oob_test.py --dns-server 1.2.3.4 --domain oob.example.com \
    --http-url https://your-reach.example.com/oob/callback

This will:
  - generate a random token
  - query <token>.<domain> against the DNS server
  - send an HTTP GET to the provided URL with the token as a query param
"""

from __future__ import annotations

import argparse
import secrets
import sys
import time
import urllib.parse
import urllib.request


def _dns_query_dnslib(server: str, port: int, qname: str, qtype: str, timeout: float) -> str:
    try:
        from dnslib import DNSRecord  # type: ignore
    except Exception as exc:  # pragma: no cover - optional dependency
        raise RuntimeError(
            "dnslib is not installed; install it with: pip install dnslib"
        ) from exc

    req = DNSRecord.question(qname, qtype)
    data = req.pack()

    import socket

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.settimeout(timeout)
    try:
        sock.sendto(data, (server, port))
        resp, _ = sock.recvfrom(4096)
    finally:
        sock.close()

    return str(DNSRecord.parse(resp))


def _http_get(url: str, timeout: float, host_header: str | None = None) -> tuple[int, str]:
    headers = {"User-Agent": "reach-oob-test/1.0"}
    if host_header:
        headers["Host"] = host_header
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        body = resp.read(2048)
        return resp.status, body.decode("utf-8", errors="replace")


def main() -> int:
    parser = argparse.ArgumentParser(description="DNS + HTTP OOB test probe")
    parser.add_argument("--dns-server", required=True, help="Authoritative DNS server IP")
    parser.add_argument("--domain", required=True, help="Delegated domain (e.g., oob.example.com)")
    parser.add_argument(
        "--qtype",
        default="A",
        choices=["A", "AAAA", "TXT", "CNAME"],
        help="DNS query type",
    )
    parser.add_argument("--dns-port", type=int, default=53, help="DNS server port")
    parser.add_argument(
        "--http-url",
        required=True,
        help="HTTP endpoint to ping (token will be added as ?t=...)",
    )
    parser.add_argument(
        "--http-host",
        help="Override connect host/IP for HTTP while keeping Host header from --http-url",
    )
    parser.add_argument("--token", help="Optional fixed token")
    parser.add_argument("--timeout", type=float, default=3.0, help="Timeout in seconds")

    args = parser.parse_args()

    token = args.token or secrets.token_urlsafe(8)
    fqdn = f"{token}.{args.domain.strip('.')}"

    print(f"token: {token}")
    print(f"fqdn: {fqdn}")

    print("dns: sending query...")
    try:
        dns_resp = _dns_query_dnslib(args.dns_server, args.dns_port, fqdn, args.qtype, args.timeout)
        print("dns: response received")
        print(dns_resp)
    except Exception as exc:
        print(f"dns: failed: {exc}")

    time.sleep(0.2)

    parsed = urllib.parse.urlparse(args.http_url)
    query = urllib.parse.parse_qsl(parsed.query, keep_blank_values=True)
    query.append(("t", token))
    base_netloc = parsed.netloc
    url = parsed._replace(query=urllib.parse.urlencode(query)).geturl()
    host_header = None
    if args.http_host:
        url = parsed._replace(netloc=args.http_host, query=urllib.parse.urlencode(query)).geturl()
        host_header = base_netloc

    print("http: sending request...")
    try:
        status, body = _http_get(url, args.timeout, host_header=host_header)
        print(f"http: status={status}")
        if body:
            print("http: body (first 2KB):")
            print(body)
    except Exception as exc:
        print(f"http: failed: {exc}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
