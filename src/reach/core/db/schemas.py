"""Pydantic schemas for REACH Core route definitions."""
from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Literal

from pydantic import BaseModel


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


class RouteCreate(RouteBase):
    """Payload for creating a new route."""


class RouteUpdate(BaseModel):
    """Payload for partially updating an existing route."""

    status_code: int | None = None
    response_body: str | None = None
    content_type: str | None = None
    body_encoding: BodyEncodingLiteral | None = None


class RouteOut(RouteBase):
    """Route model returned from the admin API."""

    id: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
