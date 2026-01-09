#!/usr/bin/env python3
"""Proof-of-concept FTP traffic capture server.

Listens on a TCP port (default 2121) and prints raw bytes from clients.
Responds with minimal FTP banners to keep clients talking.
"""

from __future__ import annotations

import argparse
import asyncio
from datetime import datetime, UTC
from typing import Optional


FTP_BANNER = b"220 REACH FTP capture ready\r\n"
FTP_OK = b"200 OK\r\n"
FTP_QUIT = b"221 Bye\r\n"
FTP_USER_OK = b"331 Username OK, need password\r\n"
FTP_PASS_OK = b"230 Login OK\r\n"


def _ts() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds") + "Z"


async def handle_client(reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
    peer = writer.get_extra_info("peername")
    print(f"[{_ts()}] connect from {peer}")

    writer.write(FTP_BANNER)
    await writer.drain()

    while True:
        data = await reader.read(4096)
        if not data:
            break

        print(f"[{_ts()}] {peer} -> {data!r}")

        upper = data.strip().upper()
        if upper.startswith(b"USER"):
            writer.write(FTP_USER_OK)
        elif upper.startswith(b"PASS"):
            writer.write(FTP_PASS_OK)
        elif upper.startswith(b"QUIT"):
            writer.write(FTP_QUIT)
            await writer.drain()
            break
        else:
            writer.write(FTP_OK)

        await writer.drain()

    writer.close()
    await writer.wait_closed()
    print(f"[{_ts()}] disconnect from {peer}")


async def run_server(host: str, port: int) -> None:
    server = await asyncio.start_server(handle_client, host, port)
    addrs = ", ".join(str(sock.getsockname()) for sock in server.sockets or [])
    print(f"[{_ts()}] listening on {addrs}")
    async with server:
        await server.serve_forever()


def parse_args(argv: Optional[list[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="FTP traffic capture (POC)")
    parser.add_argument("--host", default="0.0.0.0", help="Bind host")
    parser.add_argument("--port", type=int, default=2121, help="Bind port")
    return parser.parse_args(argv)


def main() -> None:
    args = parse_args()
    try:
        asyncio.run(run_server(args.host, args.port))
    except KeyboardInterrupt:
        print(f"[{_ts()}] shutdown")


if __name__ == "__main__":
    main()
