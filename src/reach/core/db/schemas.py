# reach/core/db/schemas.py
from __future__ import annotations

from datetime import datetime
from pydantic import BaseModel
from typing import Literal


class RouteBase(BaseModel):
    method: str
    path: str
    status_code: int = 200
    response_body: str = "OK"
    content_type: str = "text/plain"
    body_encoding: Literal["none", "base64"] = "none" 

class RouteCreate(RouteBase):
    pass


class RouteUpdate(BaseModel):
    status_code: int | None = None
    response_body: str | None = None
    content_type: str | None = None
    body_encoding: Literal["none", "base64"] | None = None


class RouteOut(RouteBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True  # Pydantic v2 / FastAPI 0.111+
