"""Pydantic schemas for REACH Core route definitions."""
from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Literal, Any

from pydantic import BaseModel, Field


class BodyEncoding(str, Enum):
    """Supported encodings for stored route response bodies."""

    NONE = "none"
    BASE64 = "base64"


BodyEncodingLiteral = Literal["none", "base64"]


class RouteBase(BaseModel):
    method: str
    path: str
    status_code: int = 200
    response_body: str = "OK"
    content_type: str = "text/plain"
    body_encoding: BodyEncodingLiteral = BodyEncoding.NONE
    headers: dict[str, str] = Field(default_factory=dict)


class RouteCreate(RouteBase):
    """Payload for creating a new route."""


class RouteUpdate(BaseModel):
    """Payload for partially updating an existing route."""

    status_code: int | None = None
    response_body: str | None = None
    content_type: str | None = None
    body_encoding: BodyEncodingLiteral | None = None
    headers: dict[str, str] | None = None


class RouteOut(RouteBase):
    """Route model returned from the admin API."""

    id: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class TriggerRuleBase(BaseModel):
    name: str
    enabled: bool = True
    priority: int = 100
    match: dict[str, Any] = Field(default_factory=dict)
    action: dict[str, Any] = Field(default_factory=dict)


class TriggerRuleCreate(TriggerRuleBase):
    """Payload for creating a new trigger rule."""


class TriggerRuleUpdate(BaseModel):
    """Payload for partially updating an existing trigger rule."""

    name: str | None = None
    enabled: bool | None = None
    priority: int | None = None
    match: dict[str, Any] | None = None
    action: dict[str, Any] | None = None


class TriggerRuleOut(TriggerRuleBase):
    """Trigger rule model returned from the admin API."""

    id: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class DnsZoneBase(BaseModel):
    zone: str
    a: str
    aaaa: str | None = None
    ttl: int = 60
    ns: list[str] = Field(default_factory=list)
    soa_mname: str
    soa_rname: str
    soa_serial: int
    soa_refresh: int = 3600
    soa_retry: int = 600
    soa_expire: int = 1209600
    soa_minimum: int = 300
    wildcard: bool = True
    enabled: bool = True


class DnsZoneCreate(BaseModel):
    """Payload for creating a new DNS zone."""

    zone: str
    a: str
    aaaa: str | None = None
    ttl: int = 60
    ns: list[str] | None = None
    soa_mname: str | None = None
    soa_rname: str | None = None
    soa_serial: int | None = None
    soa_refresh: int = 3600
    soa_retry: int = 600
    soa_expire: int = 1209600
    soa_minimum: int = 300
    wildcard: bool = True
    enabled: bool = True


class DnsZoneUpdate(BaseModel):
    """Payload for partially updating an existing DNS zone."""

    a: str | None = None
    aaaa: str | None = None
    ttl: int | None = None
    ns: list[str] | None = None
    soa_mname: str | None = None
    soa_rname: str | None = None
    soa_serial: int | None = None
    soa_refresh: int | None = None
    soa_retry: int | None = None
    soa_expire: int | None = None
    soa_minimum: int | None = None
    wildcard: bool | None = None
    enabled: bool | None = None


class DnsZoneOut(DnsZoneBase):
    """DNS zone model returned from the admin API."""

    id: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
