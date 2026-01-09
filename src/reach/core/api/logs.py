# reach/core/api/logs.py
from __future__ import annotations

from fastapi import APIRouter
from typing import List

from reach.core.logging import LoggedRequest, get_logs_since

router = APIRouter(prefix="/api/logs", tags=["logs"])

@router.get("", response_model=List[LoggedRequest])
def list_logs(
    since_id: int = 0,
    limit: int = 100,
    protocol: str | None = None,
):
    """
    Return logs with id > since_id (for streaming / tailing).
    """
    return get_logs_since(since_id, limit, protocol)
