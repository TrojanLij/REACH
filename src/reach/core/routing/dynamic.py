"""Dynamic routing and request logging for the public FastAPI app."""

from __future__ import annotations

from base64 import b64decode
import re
from typing import Any, Callable

from fastapi import FastAPI, Request, Depends, HTTPException
from fastapi.responses import Response, JSONResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..db import get_db, models
from ..globals import RESERVED_PREFIXES, random_server_header
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

        # Read body for logging (dynamic endpoints are interesting).
        # We always treat this as text on the logging side to avoid
        # accidentally interpreting it as anything executable.
        try:
            body_bytes = await request.body()
            body_text = body_bytes.decode("utf-8", errors="replace") if body_bytes else None
        except Exception:
            body_text = None

        client_ip = request.client.host if request.client else None
        host = request.headers.get("host")

        request_context = {
            "method": method,
            "path": "/" + full_path,
            "headers": {k.lower(): v for k, v in request.headers.items()},
            "query": {k: v for k, v in request.query_params.items()},
            "body": body_text or "",
            "client_ip": client_ip or "",
            "host": host or "",
        }

        db_route = None
        rule_action = _match_rules(db, request_context)
        if rule_action is not None:
            status_code = _rule_status_code(rule_action)
        else:
            stmt = select(models.Route).where(
                models.Route.method == method,
                models.Route.path == norm_path,
            )
            db_route = db.execute(stmt).scalar_one_or_none()
            status_code = db_route.status_code if db_route else 404

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

        if rule_action is not None:
            return _build_rule_response(rule_action)

        # No matching route → clean 404
        if not db_route:
            return JSONResponse(
                status_code=404,
                content={"detail": "No dynamic route matched"},
            )

        response_headers = dict(db_route.headers or {})
        if not any(k.lower() == "server" for k in response_headers):
            response_headers["Server"] = random_server_header()

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
                headers=response_headers,
            )
        else:
            # Plain text payload
            body_str = db_route.response_body or ""
            return Response(
                content=body_str,
                status_code=db_route.status_code,
                media_type=db_route.content_type,
                headers=response_headers,
            )


def _regex_match(pattern: str, value: str) -> bool:
    try:
        return re.search(pattern, value) is not None
    except re.error:
        return False


def _match_mapping(patterns: dict[str, Any], values: dict[str, Any]) -> bool:
    for key, pattern in patterns.items():
        candidate = values.get(str(key))
        if candidate is None:
            return False
        if not _regex_match(str(pattern), str(candidate)):
            return False
    return True


def _rule_matches(match: dict[str, Any], ctx: dict[str, Any]) -> bool:
    if not match:
        return True
    if "method" in match and not _regex_match(str(match["method"]), ctx["method"]):
        return False
    if "path" in match and not _regex_match(str(match["path"]), ctx["path"]):
        return False
    if "host" in match and not _regex_match(str(match["host"]), ctx["host"]):
        return False
    if "client_ip" in match and not _regex_match(str(match["client_ip"]), ctx["client_ip"]):
        return False
    if "body" in match and not _regex_match(str(match["body"]), ctx["body"]):
        return False
    if "headers" in match:
        if not isinstance(match["headers"], dict):
            return False
        header_patterns = {str(k).lower(): v for k, v in match["headers"].items()}
        if not _match_mapping(header_patterns, ctx["headers"]):
            return False
    if "query" in match:
        if not isinstance(match["query"], dict):
            return False
        if not _match_mapping(match["query"], ctx["query"]):
            return False
    return True


def _match_rules(db: Session, ctx: dict[str, Any]) -> dict[str, Any] | None:
    stmt = (
        select(models.TriggerRule)
        .where(models.TriggerRule.enabled.is_(True))
        .order_by(models.TriggerRule.priority, models.TriggerRule.id)
    )
    rules = db.execute(stmt).scalars().all()
    for rule in rules:
        if _rule_matches(rule.match, ctx):
            return rule.action
    return None


def _rule_status_code(action: dict[str, Any]) -> int:
    status = action.get("status_code", 200)
    return status if isinstance(status, int) else 200


def _build_rule_response(action: dict[str, Any]) -> Response:
    body = action.get("body")
    if body is None:
        body = action.get("response_body", "")
    content_type = action.get("content_type", "text/plain")
    status_code = _rule_status_code(action)
    headers = action.get("headers")
    if not isinstance(headers, dict):
        headers = {}
    if not any(k.lower() == "server" for k in headers):
        headers["Server"] = random_server_header()
    return Response(
        content=str(body),
        status_code=status_code,
        media_type=str(content_type),
        headers={str(k): str(v) for k, v in headers.items()},
    )
