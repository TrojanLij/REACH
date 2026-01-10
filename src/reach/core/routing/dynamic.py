"""Dynamic routing and request logging for the public FastAPI app."""

from __future__ import annotations

from base64 import b64decode
from typing import Any, Callable

from fastapi import FastAPI, Request, Depends, HTTPException
from fastapi.responses import Response, JSONResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..db import get_db, models
from ..globals import RESERVED_PREFIXES
from .. import logging as reach_logging

DYNAMIC_HTTP_METHODS = ["GET", "POST", "PUT", "DELETE", "PATCH"]
# Paths that should bypass the public dynamic router (admin/docs/static)
DEFAULT_BODY_ENCODING = "none"


def _is_reserved_path(full_path: str) -> bool:
    """Return True if the request path should bypass dynamic routing."""
    return any(full_path.startswith(prefix) for prefix in RESERVED_PREFIXES)


def register_dynamic_routing(app: FastAPI) -> None:
    """
    Attach logging middleware and the catch-all dynamic route
    to the given FastAPI application.
    """

    @app.middleware("http")
    async def log_all_requests(request: Request, call_next: Callable[..., Any]) -> Response:
        """Log every request that wasn't already logged by dynamic routing."""
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

    @app.api_route(
        "/{full_path:path}",
        methods=DYNAMIC_HTTP_METHODS,
        include_in_schema=False,  # catch-all router doesn't need OpenAPI entries; avoids duplicate operation IDs
    )
    async def dynamic_router(
        full_path: str,
        request: Request,
        db: Session = Depends(get_db),
    ) -> Any:
        """Catch-all router that serves stored dynamic routes."""
        # Don't swallow API or debug endpoints
        if _is_reserved_path(full_path):
            raise HTTPException(status_code=404, detail="Not found")

        method = request.method.upper()
        norm_path = full_path.lstrip("/")

        stmt = select(models.Route).where(
            models.Route.method == method,
            models.Route.path == norm_path,
        )
        db_route = db.execute(stmt).scalar_one_or_none()

        # Read body for logging (dynamic endpoints are interesting).
        # We always treat this as text on the logging side to avoid
        # accidentally interpreting it as anything executable.
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
            body_encoding="text",
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
        if getattr(db_route, "body_encoding", DEFAULT_BODY_ENCODING) == "base64":
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
