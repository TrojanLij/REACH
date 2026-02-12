"""Shared logging helper for non-HTTP protocol handlers."""

from __future__ import annotations

from typing import Any, Mapping

from .. import logging as reach_logging


def _normalize_mapping(value: Mapping[str, Any] | None) -> dict[str, str]:
    if not value:
        return {}
    return {str(k): str(v) for k, v in value.items()}


def log_protocol_request(
    *,
    protocol: str,
    method: str,
    path: str,
    route_id: int | None,
    status_code: int | None,
    headers: Mapping[str, Any] | None = None,
    query_params: Mapping[str, Any] | None = None,
    body: str | None = None,
    client_ip: str | None = None,
    host: str | None = None,
    body_encoding: str = "text",
    raw_bytes: str | None = None,
    raw_bytes_encoding: str = "none",
    command: str | None = None,
) -> None:
    reach_logging.add_log(
        protocol=protocol,
        method=method,
        path=path,
        command=command,
        route_id=route_id,
        status_code=status_code,
        headers=_normalize_mapping(headers),
        query_params=_normalize_mapping(query_params),
        body=body,
        client_ip=client_ip,
        host=host,
        body_encoding=body_encoding,
        raw_bytes=raw_bytes,
        raw_bytes_encoding=raw_bytes_encoding,
    )
