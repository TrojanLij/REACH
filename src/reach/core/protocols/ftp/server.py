"""FTP protocol capture server for REACH Core."""

from __future__ import annotations

import asyncio

from ..logging import log_protocol_request
from ..registry import register_protocol

FTP_BANNER = b"220 REACH FTP capture ready\r\n"
FTP_OK = b"200 OK\r\n"
FTP_QUIT = b"221 Bye\r\n"
FTP_USER_OK = b"331 Username OK, need password\r\n"
FTP_PASS_OK = b"230 Login OK\r\n"


def _parse_command(data: bytes) -> str | None:
    if not data:
        return None
    line = data.split(b"\n", 1)[0].strip()
    if not line:
        return None
    return line.split(b" ", 1)[0].decode("ascii", errors="replace").upper()


def _response_for_command(command: str | None) -> bytes:
    if not command:
        return FTP_OK
    if command == "USER":
        return FTP_USER_OK
    if command == "PASS":
        return FTP_PASS_OK
    if command == "QUIT":
        return FTP_QUIT
    return FTP_OK


async def _handle_client(reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
    peer = writer.get_extra_info("peername")
    client_ip = None
    if isinstance(peer, (tuple, list)) and peer:
        client_ip = str(peer[0])

    writer.write(FTP_BANNER)
    await writer.drain()

    while True:
        data = await reader.read(4096)
        if not data:
            break

        command = _parse_command(data)
        response = _response_for_command(command)
        status_code = None
        try:
            status_code = int(response[:3])
        except Exception:
            status_code = None

        raw_text = data.decode("utf-8", errors="replace")

        log_protocol_request(
            protocol="ftp",
            method=command or "FTP",
            path="/",
            command=command,
            route_id=None,
            status_code=status_code,
            headers={},
            query_params={},
            body=None,
            client_ip=client_ip,
            host=None,
            body_encoding="text",
            raw_bytes=raw_text,
            raw_bytes_encoding="text",
        )

        writer.write(response)
        await writer.drain()

        if command == "QUIT":
            break

    writer.close()
    await writer.wait_closed()


async def _run_server(host: str, port: int) -> None:
    server = await asyncio.start_server(_handle_client, host, port)
    async with server:
        await server.serve_forever()


def run(host: str, port: int) -> None:
    asyncio.run(_run_server(host, port))


register_protocol(
    "ftp",
    public_app="reach.core.protocols.ftp.server:run",
    description="FTP capture server (raw command logging).",
    server_type="tcp",
    run=run,
)
