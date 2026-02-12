"""Core app factories and backward-compatible HTTP shims."""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .db.init import init_db
from .protocols.http.server import create_app, create_public_app
from .routing.static import register_static_routing

def create_admin_app() -> FastAPI:
    """
    Admin app: manage routes, view logs, etc.
    Typically bound to a port like 8001.
    """
    app = FastAPI(
        title="REACH Core (admin)",
        description="Admin API for managing routes and logs",
        version="0.2.0",
        docs_url="/api/docs",
        redoc_url="/api/redoc",
        openapi_url="/api/openapi.json",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
        allow_credentials=False,
    )

    # Attach static/admin routes (health, debug, CRUD APIs, logs)
    register_static_routing(app)

    return app
