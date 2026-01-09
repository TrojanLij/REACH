"""SQLAlchemy ORM models backing REACH Core persistence."""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import Column, Integer, String, Text, DateTime

from .base import Base


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
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    # Manually maintained; updated in the admin API.
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow)


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
