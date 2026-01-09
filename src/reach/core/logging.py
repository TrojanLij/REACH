"""Database-backed request logging utilities for REACH Core."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Dict, List
import json

from pydantic import BaseModel
from sqlalchemy import select, delete

from .db import SessionLocal, models


class LoggedRequest(BaseModel):
    """
    Pydantic representation of a logged request, returned by /api/logs
    and usable by CLI tools.
    """

    id: int
    timestamp: datetime
    protocol: str = "http"
    method: str
    path: str
    command: str | None = None
    route_id: int | None
    status_code: int | None
    client_ip: str | None = None
    host: str | None = None
    headers: Dict[str, str]
    query_params: Dict[str, str]
    body: str | None = None
    body_encoding: str = "text"
    raw_bytes: str | None = None
    raw_bytes_encoding: str = "none"

    model_config = {"from_attributes": True}


def _mapping_to_json(value: Dict[str, str]) -> str:
    """Serialize a mapping (headers, query params) to JSON for storage."""
    return json.dumps(value, ensure_ascii=False)


def _json_to_mapping(raw: str) -> Dict[str, str]:
    """Deserialize a JSON mapping into a {str: str} dict, or {} on error."""
    try:
        data = json.loads(raw)
        if isinstance(data, dict):
            # ensure keys/values are strings for the API
            return {str(k): str(v) for k, v in data.items()}
    except Exception:
        pass
    return {}


def add_log(
    *,
    protocol: str = "http",
    method: str,
    path: str,
    command: str | None = None,
    route_id: int | None,
    status_code: int | None,
    headers: Dict[str, str],
    query_params: Dict[str, str],
    body: str | None,
    client_ip: str | None = None,
    host: str | None = None,
    body_encoding: str = "text",
    raw_bytes: str | None = None,
    raw_bytes_encoding: str = "none",
) -> None:
    """
    Persist a request log entry to the database.

    This replaces the previous in-memory-only log so that
    pentesters can retain full history and payloads.
    """
    db = SessionLocal()
    try:
        entry = models.RequestLog(
            timestamp=datetime.now(timezone.utc),
            protocol=protocol,
            method=method,
            path=path,
            command=command,
            route_id=route_id,
            status_code=status_code,
            client_ip=client_ip,
            host=host,
            headers=_mapping_to_json(headers),
            query_params=_mapping_to_json(query_params),
            body=body,
            body_encoding=body_encoding,
            raw_bytes=raw_bytes,
            raw_bytes_encoding=raw_bytes_encoding,
        )
        db.add(entry)
        db.commit()
    finally:
        db.close()


def _to_logged_request(row: models.RequestLog) -> LoggedRequest:
    return LoggedRequest(
        id=row.id,
        timestamp=row.timestamp,
        protocol=getattr(row, "protocol", "http"),
        method=row.method,
        path=row.path,
        command=getattr(row, "command", None),
        route_id=row.route_id,
        status_code=row.status_code,
        client_ip=row.client_ip,
        host=row.host,
        headers=_json_to_mapping(row.headers),
        query_params=_json_to_mapping(row.query_params),
        body=row.body,
        body_encoding=getattr(row, "body_encoding", "text"),
        raw_bytes=getattr(row, "raw_bytes", None),
        raw_bytes_encoding=getattr(row, "raw_bytes_encoding", "none"),
    )


def get_logs(limit: int = 100, protocol: str | None = None) -> List[LoggedRequest]:
    """
    Return the most recent logs, ordered newest-first.
    """
    db = SessionLocal()
    try:
        stmt = select(models.RequestLog).order_by(models.RequestLog.id.desc())
        if protocol:
            stmt = stmt.where(models.RequestLog.protocol == protocol)
        stmt = stmt.limit(limit)
        rows = db.execute(stmt).scalars().all()
        return [_to_logged_request(r) for r in rows]
    finally:
        db.close()


def get_logs_since(
    since_id: int,
    limit: int = 100,
    protocol: str | None = None,
) -> List[LoggedRequest]:
    """
    Return logs with id > since_id, ordered by id ascending.
    """
    db = SessionLocal()
    try:
        stmt = (
            select(models.RequestLog)
            .where(models.RequestLog.id > since_id)
            .order_by(models.RequestLog.id.asc())
        )
        if protocol:
            stmt = stmt.where(models.RequestLog.protocol == protocol)
        if limit is not None:
            stmt = stmt.limit(limit)
        rows = db.execute(stmt).scalars().all()
        return [_to_logged_request(r) for r in rows]
    finally:
        db.close()


def clear_logs() -> None:
    """
    Dev helper: clear all request logs from the database.
    """
    db = SessionLocal()
    try:
        db.execute(delete(models.RequestLog))
        db.commit()
    finally:
        db.close()
