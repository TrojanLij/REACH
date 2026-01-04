"""App factories for the REACH Core public and admin FastAPI applications."""

from __future__ import annotations

from fastapi import FastAPI

from .db import Base, engine
from .routing.dynamic import register_dynamic_routing
from .routing.static import register_static_routing


def init_db() -> None:
    """
    Initialize database schema.

    Call this explicitly from the CLI or your own bootstrap code so that
    app import does not have side effects.
    """
    Base.metadata.create_all(bind=engine)


def create_public_app() -> FastAPI:
    """
    Public-facing app: serves dynamic routes / payloads.
    Typically bound to a port like 8000.
    """
    app = FastAPI(
        title="REACH Core (public)",
        description="Public server for dynamic routes / payloads",
        version="0.1.0",
        docs_url=None,
        redoc_url=None,
        openapi_url=None,
    )

    # Attach dynamic routing + logging middleware
    register_dynamic_routing(app)

    return app


def create_admin_app() -> FastAPI:
    """
    Admin app: manage routes, view logs, etc.
    Typically bound to a port like 8001.
    """
    app = FastAPI(
        title="REACH Core (admin)",
        description="Admin API for managing routes and logs",
        version="0.1.0",
        docs_url="/api/docs",
        redoc_url="/api/redoc",
        openapi_url="/api/openapi.json",
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
