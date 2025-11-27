# reach/core/server.py
from __future__ import annotations

from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session

from .db import Base, engine, get_db, models
from .api.routes import router as routes_router
from .api.logs import router as logs_router
from .routing.dynamic import register_dynamic_routing


def create_public_app() -> FastAPI:
    """
    Public-facing app: serves dynamic routes / payloads.
    Typically bound to a port like 8000.
    """
    # Dev: auto-create tables. Later: migrations.
    Base.metadata.create_all(bind=engine)

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
    # Dev: auto-create tables. Later: migrations.
    Base.metadata.create_all(bind=engine)

    app = FastAPI(
        title="REACH Core (admin)",
        description="Admin API for managing routes and logs",
        version="0.1.0",
    )

    @app.get("/api/health")
    async def health(db: Session = Depends(get_db)):
        count = db.query(models.Route).count()
        return {"status": "ok", "routes": count}

    @app.get("/debug/routes")
    async def debug_routes(db: Session = Depends(get_db)):
        routes = db.query(models.Route).all()
        return {
            "count": len(routes),
            "routes": [
                {
                    "id": r.id,
                    "method": r.method,
                    "path": "/" + r.path,
                    "status_code": r.status_code,
                    "content_type": r.content_type,
                    "response_preview": (r.response_body[:120] + "…")
                    if len(r.response_body) > 120
                    else r.response_body,
                }
                for r in routes
            ],
        }

    app.include_router(routes_router)
    app.include_router(logs_router)

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
