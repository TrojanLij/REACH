"""App factories for the REACH Core public and admin FastAPI applications."""

from __future__ import annotations

from fastapi import FastAPI

from .db import Base, engine
from .routing.dynamic import register_dynamic_routing
from .routing.static import register_static_routing


def init_db() -> None:
    """Initialize database schema (development convenience)."""
    # Dev: auto-create tables. Later: migrations.
    Base.metadata.create_all(bind=engine)


def create_public_app() -> FastAPI:
    """
    Public-facing app: serves dynamic routes / payloads.
    Typically bound to a port like 8000.
    """
    init_db()

    app = FastAPI(
        title="REACH Core (public)",
        description="Public server for dynamic routes / payloads",
        version="0.1.0",
    )

    # Attach dynamic routing + logging middleware
    register_dynamic_routing(app)

    return app


def create_admin_app() -> FastAPI:
    """
    Admin app: manage routes, view logs, etc.
    Typically bound to a port like 8001.
    """
    init_db()

    app = FastAPI(
        title="REACH Core (admin)",
        description="Admin API for managing routes and logs",
        version="0.1.0",
    )

    # Attach static/admin routes (health, debug, CRUD APIs, logs)
    register_static_routing(app)

    return app


def create_app() -> FastAPI:
    """
    Backwards-compatible helper returning the public app.

    External code importing reach.core.create_app or reach.core.server:create_app
    will get the public-facing application.
    """
    return create_public_app()


# Default uvicorn entrypoint: public app
public_app = create_public_app()
admin_app = create_admin_app()
app = public_app
