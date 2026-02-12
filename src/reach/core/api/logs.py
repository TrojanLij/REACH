# reach/core/api/logs.py
from __future__ import annotations

from fastapi import APIRouter
from typing import List

from reach.core.logging import LoggedRequest, get_logs_since

router = APIRouter(prefix="/api/logs", tags=["logs"])


def _normalize_dns_name(value: str | None) -> str:
    if not value:
        return ""
    return value.rstrip(".").lower()


def _dns_label_for_entry(entry: LoggedRequest) -> str | None:
    if (entry.protocol or "").lower() != "dns":
        return None
    zone = _normalize_dns_name(entry.headers.get("zone"))
    if not zone:
        return None
    qname = _normalize_dns_name(entry.path)
    if qname == zone:
        return None
    suffix = "." + zone
    if not qname.endswith(suffix):
        return None
    prefix = qname[: -len(suffix)]
    if not prefix:
        return None
    return prefix.split(".", 1)[0]

@router.get("", response_model=List[LoggedRequest])
def list_logs(
    since_id: int = 0,
    limit: int = 100,
    protocol: str | None = None,
    dns_label: str | None = None,
):
    """
    Return logs with id > since_id (for streaming / tailing).
    """
    entries = get_logs_since(since_id, limit, protocol)
    if dns_label:
        target = _normalize_dns_name(dns_label)
        entries = [entry for entry in entries if _dns_label_for_entry(entry) == target]
    return entries
