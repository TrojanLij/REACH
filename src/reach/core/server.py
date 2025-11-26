# reach/core/server.py
from __future__ import annotations

from fastapi import FastAPI, Request, Depends, HTTPException
from fastapi.responses import Response, JSONResponse
from sqlalchemy import select
from sqlalchemy.orm import Session
from base64 import b64decode

from .db import Base, engine, get_db, models
from .api.routes import router as routes_router
from .api.logs import router as logs_router
from . import logging as reach_logging


def create_app() -> FastAPI:
    # Dev: auto-create tables. Later: migrations.
    Base.metadata.create_all(bind=engine)

    app = FastAPI(
        title="REACH Core",
        description="Backend server, DB, routing, logging, REST API",
        version="0.1.0",
    )

    #! Global middleware: log EVERY request (api, debug, dynamic, etc.). HEADS UP! THIS IS NOISY IN THE LOGS :)
    @app.middleware("http")
    async def log_all_requests(request: Request, call_next):
        response = await call_next(request)

        # If someone already logged this request (dynamic_router), skip
        if getattr(request.state, "logged", False):
            return response

        client_ip = request.client.host if request.client else None
        host = request.headers.get("host")

        reach_logging.add_log(
            method=request.method,
            path=request.url.path,
            route_id=None,  # unknown here
            status_code=response.status_code,
            headers={k: v for k, v in request.headers.items()},
            query_params={k: v for k, v in request.query_params.items()},
            body=None,  # we don't read body in middleware for now
            client_ip=client_ip,
            host=host,
        )

        return response

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

    @app.api_route("/{full_path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
    async def dynamic_router(
        full_path: str,
        request: Request,
        db: Session = Depends(get_db),
    ):
        # Don't swallow API or debug endpoints
        if full_path.startswith("api/") or full_path.startswith("debug/"):
            raise HTTPException(status_code=404, detail="Not found")

        method = request.method.upper()
        norm_path = full_path.lstrip("/")

        stmt = select(models.Route).where(
            models.Route.method == method,
            models.Route.path == norm_path,
        )
        db_route = db.execute(stmt).scalar_one_or_none()

        # Read body for logging (dynamic endpoints are interesting)
        try:
            body_bytes = await request.body()
            body_text = body_bytes.decode("utf-8", errors="replace") if body_bytes else None
        except Exception:
            body_text = None

        status_code = db_route.status_code if db_route else 404

        client_ip = request.client.host if request.client else None
        host = request.headers.get("host")

        # Detailed log for dynamic routes (including body + route_id)
        reach_logging.add_log(
            method=method,
            path="/" + full_path,
            route_id=db_route.id if db_route else None,
            status_code=status_code,
            headers={k: v for k, v in request.headers.items()},
            query_params={k: v for k, v in request.query_params.items()},
            body=body_text,
            client_ip=client_ip,
            host=host,
        )
        
        # mark as logged so middleware won't double-log
        request.state.logged = True

        # No matching route → clean 404
        if not db_route:
            return JSONResponse(
                status_code=404,
                content={"detail": "No dynamic route matched"},
            )

        # Decide how to build the response body
        if getattr(db_route, "body_encoding", "none") == "base64":
            # Treat response_body as base64-encoded bytes (good for images)
            try:
                body_bytes = b64decode(db_route.response_body)
            except Exception as e:
                return JSONResponse(
                    status_code=500,
                    content={"detail": f"Failed to decode base64 body: {e}"},
                )
            # base64 / images
            return Response(
                content=body_bytes,
                status_code=db_route.status_code,
                media_type=db_route.content_type,
            )
        else:
            # Plain text payload
            body_str = db_route.response_body or ""
            return Response(
                content=body_str,
                status_code=db_route.status_code,
                media_type=db_route.content_type,
            )

    return app

# uvicorn entrypoint
app = create_app()
