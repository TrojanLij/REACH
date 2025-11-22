# reach/core/logging.py
from __future__ import annotations

from datetime import datetime
from typing import Dict, List

from pydantic import BaseModel


class LoggedRequest(BaseModel):
    id: int                      # 👈 NEW
    timestamp: datetime
    method: str
    path: str
    route_id: int | None
    status_code: int | None
    headers: Dict[str, str]
    query_params: Dict[str, str]
    body: str | None = None


_request_log: List[LoggedRequest] = []
_next_id: int = 1  # 👈 NEW


def add_log(
    *,
    method: str,
    path: str,
    route_id: int | None,
    status_code: int | None,
    headers: Dict[str, str],
    query_params: Dict[str, str],
    body: str | None,
) -> None:
    global _next_id

    entry = LoggedRequest(
        id=_next_id,
        timestamp=datetime.utcnow(),
        method=method,
        path=path,
        route_id=route_id,
        status_code=status_code,
        headers=headers,
        query_params=query_params,
        body=body,
    )
    _next_id += 1
    _request_log.append(entry)


def get_logs(limit: int = 100) -> List[LoggedRequest]:
    return list(reversed(_request_log[-limit:]))

def get_logs_since(since_id: int, limit: int = 100) -> List[LoggedRequest]:
    """
    Return logs with id > since_id, ordered by id ascending.
    """
    new = [e for e in _request_log if e.id > since_id]
    if limit is not None and len(new) > limit:
        new = new[-limit:]
    return new

def clear_logs() -> None:
    """Dev helper: clear in-memory request log."""
    _request_log.clear()
    global _next_id
    _next_id = 1
