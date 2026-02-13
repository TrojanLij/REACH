"""Admin CRUD API for REACH DNS zones."""

from __future__ import annotations

from datetime import UTC, datetime, timezone
import ipaddress
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..db import get_db, models
from ..db.schemas import DnsZoneCreate, DnsZoneOut, DnsZoneUpdate

router = APIRouter(prefix="/api/dns/zones", tags=["dns"])


def _normalize_zone(zone: str) -> str:
    return zone.strip(".").lower()


def _normalize_host(value: str) -> str:
    return value.strip(".").lower()


def _normalize_ns(ns: list[str] | None, zone: str) -> list[str]:
    if not ns:
        return [f"ns1.{zone}", f"ns2.{zone}"]
    return [_normalize_host(item) for item in ns]


def _validate_ip(value: str | None) -> None:
    if value is None:
        return
    try:
        ipaddress.ip_address(value)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


def _zone_out(db_zone: models.DnsZone) -> DnsZoneOut:
    return DnsZoneOut(
        id=db_zone.id,
        zone=db_zone.zone,
        a=db_zone.a,
        aaaa=db_zone.aaaa,
        ttl=db_zone.ttl,
        ns=db_zone.ns_list,
        soa_mname=db_zone.soa_mname,
        soa_rname=db_zone.soa_rname,
        soa_serial=db_zone.soa_serial,
        soa_refresh=db_zone.soa_refresh,
        soa_retry=db_zone.soa_retry,
        soa_expire=db_zone.soa_expire,
        soa_minimum=db_zone.soa_minimum,
        wildcard=db_zone.wildcard,
        enabled=db_zone.enabled,
        created_at=db_zone.created_at,
        updated_at=db_zone.updated_at,
    )


def _apply_updates(db_zone: models.DnsZone, zone_upd: DnsZoneUpdate) -> None:
    if hasattr(zone_upd, "model_dump"):
        updates: dict[str, Any] = zone_upd.model_dump(exclude_unset=True)  # type: ignore[attr-defined]
    else:
        updates = zone_upd.dict(exclude_unset=True)  # type: ignore[assignment]
    if "a" in updates:
        _validate_ip(updates["a"])
        db_zone.a = updates["a"]
    if "aaaa" in updates:
        _validate_ip(updates["aaaa"])
        db_zone.aaaa = updates["aaaa"]
    if "ttl" in updates:
        db_zone.ttl = updates["ttl"]
    if "ns" in updates:
        db_zone.set_ns(_normalize_ns(updates["ns"], db_zone.zone))
    if "soa_mname" in updates:
        db_zone.soa_mname = _normalize_host(updates["soa_mname"])
    if "soa_rname" in updates:
        db_zone.soa_rname = _normalize_host(updates["soa_rname"])
    if "soa_serial" in updates:
        db_zone.soa_serial = updates["soa_serial"]
    if "soa_refresh" in updates:
        db_zone.soa_refresh = updates["soa_refresh"]
    if "soa_retry" in updates:
        db_zone.soa_retry = updates["soa_retry"]
    if "soa_expire" in updates:
        db_zone.soa_expire = updates["soa_expire"]
    if "soa_minimum" in updates:
        db_zone.soa_minimum = updates["soa_minimum"]
    if "wildcard" in updates:
        db_zone.wildcard = updates["wildcard"]
    if "enabled" in updates:
        db_zone.enabled = updates["enabled"]


@router.get("", response_model=list[DnsZoneOut])
def list_zones(db: Session = Depends(get_db)) -> list[DnsZoneOut]:
    stmt = select(models.DnsZone).order_by(models.DnsZone.id)
    zones = db.execute(stmt).scalars().all()
    return [_zone_out(zone) for zone in zones]


@router.post("", response_model=DnsZoneOut, status_code=201)
def create_zone(zone_in: DnsZoneCreate, db: Session = Depends(get_db)) -> DnsZoneOut:
    zone = _normalize_zone(zone_in.zone)
    _validate_ip(zone_in.a)
    _validate_ip(zone_in.aaaa)
    ns_list = _normalize_ns(zone_in.ns, zone)
    soa_mname = _normalize_host(zone_in.soa_mname or ns_list[0])
    soa_rname = _normalize_host(zone_in.soa_rname or f"hostmaster.{zone}")
    soa_serial = zone_in.soa_serial or int(datetime.now(timezone.utc).timestamp())

    dup_stmt = select(models.DnsZone).where(models.DnsZone.zone == zone)
    existing = db.execute(dup_stmt).scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=400, detail="Zone already exists")

    db_zone = models.DnsZone(
        zone=zone,
        a=zone_in.a,
        aaaa=zone_in.aaaa,
        ttl=zone_in.ttl,
        soa_mname=soa_mname,
        soa_rname=soa_rname,
        soa_serial=soa_serial,
        soa_refresh=zone_in.soa_refresh,
        soa_retry=zone_in.soa_retry,
        soa_expire=zone_in.soa_expire,
        soa_minimum=zone_in.soa_minimum,
        wildcard=zone_in.wildcard,
        enabled=zone_in.enabled,
    )
    db_zone.set_ns(ns_list)
    db.add(db_zone)
    db.commit()
    db.refresh(db_zone)
    return _zone_out(db_zone)


@router.get("/{zone_id}", response_model=DnsZoneOut)
def get_zone(zone_id: int, db: Session = Depends(get_db)) -> DnsZoneOut:
    db_zone = db.get(models.DnsZone, zone_id)
    if not db_zone:
        raise HTTPException(status_code=404, detail="Zone not found")
    return _zone_out(db_zone)


@router.patch("/{zone_id}", response_model=DnsZoneOut)
def update_zone(zone_id: int, zone_upd: DnsZoneUpdate, db: Session = Depends(get_db)) -> DnsZoneOut:
    db_zone = db.get(models.DnsZone, zone_id)
    if not db_zone:
        raise HTTPException(status_code=404, detail="Zone not found")
    _apply_updates(db_zone, zone_upd)
    db_zone.updated_at = datetime.now(UTC)
    db.add(db_zone)
    db.commit()
    db.refresh(db_zone)
    return _zone_out(db_zone)


@router.delete("/{zone_id}", status_code=204)
def delete_zone(zone_id: int, db: Session = Depends(get_db)) -> None:
    db_zone = db.get(models.DnsZone, zone_id)
    if not db_zone:
        raise HTTPException(status_code=404, detail="Zone not found")
    db.delete(db_zone)
    db.commit()
