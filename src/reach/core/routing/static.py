"""Static/admin routing helpers for the REACH Core FastAPI apps."""

from __future__ import annotations

from typing import TypedDict

from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session

from ..db import get_db, models
from ..api.routes import router as routes_router
from ..api.rules import router as rules_router
from ..api.logs import router as logs_router
from ..api.dns_zones import router as dns_zones_router
from ..api.plugins import router as plugins_router


class RouteDebugSummary(TypedDict):
    """Shape of a route entry in the /debug/routes response."""
    id: int
    method: str
    path: str
    status_code: int
    content_type: str
    response_preview: str


def _debug_route_summary(route: models.Route) -> RouteDebugSummary:
    """Return a lightweight, human-friendly summary of a stored route."""
    body = route.response_body or ""
    preview = body if len(body) <= 120 else body[:120] + "…"
    return {
        "id": route.id,
        "method": route.method,
        "path": "/" + route.path,
        "status_code": route.status_code,
        "content_type": route.content_type,
        "response_preview": preview,
    }


def register_static_routing(app: FastAPI) -> None:
    """
    Attach static/admin routes to the given FastAPI application.

    This includes health checks, debug endpoints, and the admin CRUD
    APIs for routes and logs.
    """
    @app.get("/api/health")
    async def health(db: Session = Depends(get_db)):
        """Simple health endpoint summarizing stored routes."""
        count = db.query(models.Route).count()
        dns_zones = db.query(models.DnsZone).count()
        return {"status": "ok", "routes": count, "dns_zones": dns_zones}

    @app.get("/debug/routes")
    async def debug_routes(db: Session = Depends(get_db)):
        """Return a compact debug view of all stored routes."""
        routes = db.query(models.Route).all()
        return {
            "count": len(routes),
            "routes": [_debug_route_summary(r) for r in routes],
        }

    app.include_router(routes_router)
    app.include_router(rules_router)
    app.include_router(logs_router)
    app.include_router(dns_zones_router)
    app.include_router(plugins_router)
