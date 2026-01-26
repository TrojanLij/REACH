"""DNS zone loading helpers for the REACH DNS service."""

from __future__ import annotations

from dataclasses import dataclass
import logging
import threading
import time
from typing import Iterable

from dnslib import DNSLabel
from sqlalchemy import select

from reach.core.db import models
from reach.core.db.session import with_session

logger = logging.getLogger("reach.dns.zones")


@dataclass(frozen=True)
class ZoneConfig:
    zone: str
    label: DNSLabel
    depth: int
    a: str
    aaaa: str | None
    ttl: int
    ns: list[str]
    soa_mname: str
    soa_rname: str
    soa_serial: int
    soa_refresh: int
    soa_retry: int
    soa_expire: int
    soa_minimum: int
    wildcard: bool


def _normalize_zone(zone: str) -> str:
    return zone.strip(".").lower()


def _zone_depth(zone: str) -> int:
    return len(zone.split(".")) if zone else 0


def _as_zone_config(row: models.DnsZone) -> ZoneConfig:
    zone = _normalize_zone(row.zone)
    return ZoneConfig(
        zone=zone,
        label=DNSLabel(zone),
        depth=_zone_depth(zone),
        a=row.a,
        aaaa=row.aaaa,
        ttl=row.ttl,
        ns=row.ns_list,
        soa_mname=row.soa_mname,
        soa_rname=row.soa_rname,
        soa_serial=row.soa_serial,
        soa_refresh=row.soa_refresh,
        soa_retry=row.soa_retry,
        soa_expire=row.soa_expire,
        soa_minimum=row.soa_minimum,
        wildcard=row.wildcard,
    )


@with_session
def load_zones(*, db=None) -> list[ZoneConfig]:
    stmt = select(models.DnsZone).where(models.DnsZone.enabled.is_(True)).order_by(models.DnsZone.id)
    rows = db.execute(stmt).scalars().all()
    return [_as_zone_config(row) for row in rows]


class ZoneStore:
    """Cache DNS zones from the core database with periodic refresh."""

    def __init__(self, refresh_interval: float = 2.0) -> None:
        self._refresh_interval = max(refresh_interval, 0.1)
        self._lock = threading.Lock()
        self._zones: list[ZoneConfig] = []
        self._last_refresh = 0.0

    def _needs_refresh(self) -> bool:
        return (time.monotonic() - self._last_refresh) >= self._refresh_interval

    def refresh(self) -> None:
        try:
            zones = load_zones()
        except Exception:
            logger.exception("Failed to refresh DNS zones from database")
            return
        with self._lock:
            self._zones = zones
            self._last_refresh = time.monotonic()

    def list_zones(self) -> list[ZoneConfig]:
        if self._needs_refresh():
            self.refresh()
        with self._lock:
            return list(self._zones)

    def extend(self, zones: Iterable[ZoneConfig]) -> list[ZoneConfig]:
        combined = list(zones)
        combined.extend(self.list_zones())
        return combined
