"""HTTP public app factory for REACH Core."""

from __future__ import annotations

from fastapi import FastAPI

from ...routing.dynamic import register_dynamic_routing
from ..registry import register_protocol
from ...db.init import init_db


def create_public_app() -> FastAPI:
    """
    Public-facing app: serves dynamic routes / payloads.
    Typically bound to a port like 8000.
    """
    app = FastAPI(
        title="REACH Core (public)",
        description="Public server for dynamic routes / payloads",
        version="0.1.0",
        docs_url="None",
        redoc_url=None,
        openapi_url=None,
        # openapi_url="/openapi.json", # --> un-comment to test if the file is accidentally exposed
    )

    # Attach dynamic routing + logging middleware
    register_dynamic_routing(app)

    return app


def create_app() -> FastAPI:
    """
    Backwards-compatible helper returning the public app.

    External code importing reach.core.create_app or reach.core.server:create_app
    will get the public-facing application.
    """
    return create_public_app()


register_protocol(
    "http",
    public_app="reach.core.protocols.http.server:create_public_app",
    init_db=init_db,
    description="Public HTTP server (FastAPI/Uvicorn).",
)
