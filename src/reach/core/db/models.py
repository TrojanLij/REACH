# reach/core/db/models.py
from __future__ import annotations

from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime

from .base import Base


class Route(Base):
    __tablename__ = "routes"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    method = Column(String(10), nullable=False)
    path = Column(String(255), nullable=False)
    status_code = Column(Integer, nullable=False, default=200)
    response_body = Column(Text, nullable=False, default="OK")
    content_type = Column(String(100), nullable=False, default="text/plain")
    body_encoding = Column(String(16), nullable=False, default="none")
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
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
    method = Column(String(10), nullable=False)
    path = Column(String(255), nullable=False)
    route_id = Column(Integer, nullable=True)
    status_code = Column(Integer, nullable=True)
    client_ip = Column(String(45), nullable=True)
    host = Column(String(255), nullable=True)
    headers = Column(Text, nullable=False)
    query_params = Column(Text, nullable=False)
    body = Column(Text, nullable=True)
    body_encoding = Column(String(16), nullable=False, default="text")

