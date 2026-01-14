"""SQLAlchemy ORM models backing REACH Core persistence."""
from __future__ import annotations

import json
from datetime import datetime
from typing import Any

from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean

from .base import Base


def _mapping_to_json(value: dict[str, str]) -> str:
    """Serialize a mapping to JSON for storage."""
    return json.dumps(value or {}, ensure_ascii=False)


def _json_to_mapping(raw: str) -> dict[str, str]:
    """Deserialize a JSON mapping into a {str: str} dict."""
    try:
        data = json.loads(raw)
        if isinstance(data, dict):
            return {str(k): str(v) for k, v in data.items()}
    except Exception:
        pass
    return {}


def _obj_to_json(value: dict[str, Any]) -> str:
    """Serialize a JSON-compatible dict for storage."""
    return json.dumps(value or {}, ensure_ascii=False)


def _json_to_obj(raw: str) -> dict[str, Any]:
    """Deserialize a JSON object into a dict."""
    try:
        data = json.loads(raw)
        if isinstance(data, dict):
            return data
    except Exception:
        pass
    return {}


class Route(Base):
    """Dynamic route definition stored in the database."""

    __tablename__ = "routes"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    method = Column(String(10), nullable=False)
    path = Column(String(255), nullable=False)
    status_code = Column(Integer, nullable=False, default=200)
    response_body = Column(Text, nullable=False, default="OK")
    content_type = Column(String(100), nullable=False, default="text/plain")
    # Encoding of response_body, e.g. "none" or "base64".
    body_encoding = Column(String(16), nullable=False, default="none")
    # JSON-encoded mapping of header name to value.
    response_headers = Column(Text, nullable=False, default="{}")
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    # Manually maintained; updated in the admin API.
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    @property
    def headers(self) -> dict[str, str]:
        """Return response headers as a mapping."""
        return _json_to_mapping(getattr(self, "response_headers", "{}"))

    def set_headers(self, headers: dict[str, str]) -> None:
        """Persist response headers as JSON."""
        self.response_headers = _mapping_to_json(headers)


class RequestLog(Base):
    """
    Persistent request log for REACH Core.

    This replaces the in-memory log so that pentesters can retain
    full history and payloads across restarts and long sessions.
    """

    __tablename__ = "request_logs"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow)
    protocol = Column(String(16), nullable=False, default="http")
    method = Column(String(10), nullable=False)
    path = Column(String(255), nullable=False)
    command = Column(String(32), nullable=True)
    route_id = Column(Integer, nullable=True)
    status_code = Column(Integer, nullable=True)
    client_ip = Column(String(45), nullable=True)
    host = Column(String(255), nullable=True)
    # JSON-encoded mapping of header name to value.
    headers = Column(Text, nullable=False)
    # JSON-encoded mapping of query parameter name to value.
    query_params = Column(Text, nullable=False)
    # Request body as text; encoding tracked in body_encoding.
    body = Column(Text, nullable=True)
    # Encoding of the stored body field. Currently always "text".
    body_encoding = Column(String(16), nullable=False, default="text")
    # Raw payload bytes for non-HTTP protocols (stored as text or base64).
    raw_bytes = Column(Text, nullable=True)
    raw_bytes_encoding = Column(String(16), nullable=False, default="none")


class TriggerRule(Base):
    """Rule definition for dynamic request matching and responses."""

    __tablename__ = "trigger_rules"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(128), nullable=False)
    enabled = Column(Boolean, nullable=False, default=True)
    priority = Column(Integer, nullable=False, default=100)
    match_criteria = Column(Text, nullable=False, default="{}")
    action_data = Column(Text, nullable=False, default="{}")
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    @property
    def match(self) -> dict[str, Any]:
        """Return match criteria as a dict."""
        return _json_to_obj(self.match_criteria)

    def set_match(self, match: dict[str, Any]) -> None:
        """Persist match criteria as JSON."""
        self.match_criteria = _obj_to_json(match)

    @property
    def action(self) -> dict[str, Any]:
        """Return rule action as a dict."""
        return _json_to_obj(self.action_data)

    def set_action(self, action: dict[str, Any]) -> None:
        """Persist rule action as JSON."""
        self.action_data = _obj_to_json(action)
