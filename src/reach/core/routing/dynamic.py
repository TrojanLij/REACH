"""Dynamic routing and request logging for the public FastAPI app."""

from __future__ import annotations

from base64 import b64decode
from datetime import datetime, timezone, timedelta
import re
from typing import Any, Callable

import httpx
from fastapi import FastAPI, Request, Depends
from fastapi.responses import Response, JSONResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..db import get_db, models
from ..globals import random_server_header
from .reserved import reject_reserved_paths
from .filters import FILTERS
from .. import logging as reach_logging

DYNAMIC_HTTP_METHODS = ["GET", "POST", "PUT", "DELETE", "PATCH"]
# Paths that should bypass the public dynamic router (admin/docs/static)
DEFAULT_BODY_ENCODING = "none"


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
    @reject_reserved_paths
    async def dynamic_router(
        full_path: str,
        request: Request,
        db: Session = Depends(get_db),
    ) -> Any:
        """Catch-all router that serves stored dynamic routes."""
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

        stmt = select(models.Route).where(
            models.Route.method == method,
            models.Route.path == norm_path,
        )
        db_route = db.execute(stmt).scalar_one_or_none()
        request_context["route_exists"] = db_route is not None

        rule_match = _match_rules(db, request_context, route_exists=db_route is not None)
        if rule_match is not None:
            rule_action, rule_ctx = rule_match
            _maybe_create_route(db, rule_action, rule_ctx)
            status_code = _rule_status_code(rule_action)
        else:
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

        if rule_match is not None:
            _apply_rule_state(db, rule_action, rule_ctx)
            await _maybe_forward_action(rule_action, rule_ctx)
            return _build_rule_response(rule_action, rule_ctx)

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
                    content={"detail": f"Failed to decode base64 body."},
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
    if "any" in match and not _evaluate_any(match["any"], ctx):
        return False
    if "all" in match and not _evaluate_all(match["all"], ctx):
        return False
    if "not" in match and _evaluate_not(match["not"], ctx):
        return False
    return _evaluate_leaf(match, ctx)


def _evaluate_any(value: Any, ctx: dict[str, Any]) -> bool:
    if isinstance(value, list):
        items = [item for item in value if isinstance(item, dict)]
        return bool(items) and any(_rule_matches(item, ctx) for item in items)
    if isinstance(value, dict):
        return _rule_matches(value, ctx)
    return False


def _evaluate_all(value: Any, ctx: dict[str, Any]) -> bool:
    if isinstance(value, list):
        items = [item for item in value if isinstance(item, dict)]
        return bool(items) and all(_rule_matches(item, ctx) for item in items)
    if isinstance(value, dict):
        return _rule_matches(value, ctx)
    return False


def _evaluate_not(value: Any, ctx: dict[str, Any]) -> bool:
    if isinstance(value, list):
        items = [item for item in value if isinstance(item, dict)]
        return bool(items) and any(_rule_matches(item, ctx) for item in items)
    if isinstance(value, dict):
        return _rule_matches(value, ctx)
    return False


def _evaluate_leaf(match: dict[str, Any], ctx: dict[str, Any]) -> bool:
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
    if "state" in match:
        if not isinstance(match["state"], dict):
            return False
        state_data = ctx.get("state") or {}
        if not _match_mapping(match["state"], state_data):
            return False
    return True


def _match_rules(
    db: Session, ctx: dict[str, Any], route_exists: bool
) -> tuple[dict[str, Any], dict[str, Any]] | None:
    stmt = (
        select(models.TriggerRule)
        .where(models.TriggerRule.enabled.is_(True))
        .order_by(models.TriggerRule.priority, models.TriggerRule.id)
    )
    rules = db.execute(stmt).scalars().all()
    for rule in rules:
        rule_ctx = ctx
        match = rule.match
        state_data: dict[str, Any] = {}
        stage = "post"
        if isinstance(match, dict):
            stage = str(match.get("stage", stage)).lower()
        if stage != "pre" and not route_exists:
            if not _action_creates_route(rule.action):
                continue
        if isinstance(match, dict) and "state_key" in match:
            state_key = _render_template(match.get("state_key"), ctx)
            if state_key:
                state_data = _get_rule_state(db, state_key)
                rule_ctx = {**ctx, "state_key": state_key, "state": state_data}
        if _rule_matches(match, rule_ctx) and _chain_allows(rule.action, state_data):
            return rule.action, rule_ctx
    return None


def _rule_status_code(action: dict[str, Any]) -> int:
    status = action.get("status_code", 200)
    return status if isinstance(status, int) else 200


def _build_rule_response(action: dict[str, Any], ctx: dict[str, Any]) -> Response:
    body = action.get("body")
    if body is None:
        body = action.get("response_body", "")
    content_type = _render_template(action.get("content_type", "text/plain"), ctx)
    status_code = _rule_status_code(action)
    headers = action.get("headers")
    if not isinstance(headers, dict):
        headers = {}
    if not any(k.lower() == "server" for k in headers):
        headers["Server"] = random_server_header()
    rendered_headers = {str(k): _render_template(v, ctx) for k, v in headers.items()}
    return Response(
        content=_render_template(body, ctx),
        status_code=status_code,
        media_type=str(content_type),
        headers=rendered_headers,
    )


_TEMPLATE_RE = re.compile(r"{{\s*(.+?)\s*}}")


def _render_template(value: Any, ctx: dict[str, Any]) -> str:
    if value is None:
        return ""
    text = str(value)

    def replace(match: re.Match[str]) -> str:
        expr = match.group(1)
        parts = [p.strip() for p in expr.split("|") if p.strip()]
        if not parts:
            return ""
        current = _resolve_path(parts[0], ctx)
        for flt in parts[1:]:
            current = _apply_filter(current, flt)
        return str(current)

    return _TEMPLATE_RE.sub(replace, text)


def _resolve_path(path: str, ctx: dict[str, Any]) -> Any:
    current: Any = ctx
    for part in path.split("."):
        if isinstance(current, dict) and part in current:
            current = current[part]
        else:
            return ""
    return current


def _apply_filter(value: Any, flt: str) -> Any:
    text = str(value)
    name = flt
    arg: str | None = None
    if ":" in flt:
        name, arg = flt.split(":", 1)
        name = name.strip()
        arg = arg.strip()
    func = FILTERS.get(name)
    if func is None:
        return text
    try:
        if arg is not None:
            try:
                return func(text, arg)
            except TypeError:
                return func(text)
        return func(text)
    except Exception:
        return text


async def _maybe_forward_action(action: dict[str, Any], ctx: dict[str, Any]) -> None:
    forward = action.get("forward")
    if not isinstance(forward, dict):
        return
    url = _render_template(forward.get("url"), ctx).strip()
    if not url:
        return
    method = str(forward.get("method", "POST")).upper()
    headers = forward.get("headers")
    if not isinstance(headers, dict):
        headers = {}
    rendered_headers = {str(k): _render_template(v, ctx) for k, v in headers.items()}
    body = forward.get("body")
    content = None
    if body is not None:
        rendered_body = _render_template(body, ctx)
        content = rendered_body.encode("utf-8")
        if not any(k.lower() == "content-type" for k in rendered_headers):
            rendered_headers["Content-Type"] = "text/plain"
    timeout = forward.get("timeout_seconds", 5)
    if not isinstance(timeout, (int, float)):
        timeout = 5
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            await client.request(method, url, headers=rendered_headers, content=content)
    except Exception:
        return


def _get_rule_state(db: Session, state_key: str) -> dict[str, Any]:
    row = (
        db.query(models.RuleState)
        .filter(models.RuleState.state_key == state_key)
        .one_or_none()
    )
    if not row:
        return {}
    if row.expires_at is not None:
        now = datetime.now(timezone.utc)
        expires_at = row.expires_at
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)
        if now >= expires_at:
            db.delete(row)
            db.commit()
            return {}
    return row.payload


def _chain_allows(action: dict[str, Any], state_data: dict[str, Any]) -> bool:
    chain = action.get("chain")
    if not isinstance(chain, dict):
        return True
    max_hops = chain.get("max_hops")
    if isinstance(max_hops, int) and max_hops >= 0:
        hops = state_data.get("__hops")
        if isinstance(hops, int) and hops >= max_hops:
            return False
    cooldown = chain.get("cooldown_seconds")
    if isinstance(cooldown, int) and cooldown > 0:
        last_seen = state_data.get("__last_seen")
        if isinstance(last_seen, (int, float)):
            now = datetime.now(timezone.utc).timestamp()
            if (now - float(last_seen)) < cooldown:
                return False
    return True


def _action_creates_route(action: dict[str, Any]) -> bool:
    create = action.get("create_route")
    return isinstance(create, dict)


def _maybe_create_route(db: Session, action: dict[str, Any], ctx: dict[str, Any]) -> None:
    create = action.get("create_route")
    if not isinstance(create, dict):
        return
    method = _render_template(create.get("method", ctx.get("method", "GET")), ctx).upper()
    path = _render_template(create.get("path", ctx.get("path", "/")), ctx)
    norm_path = path.lstrip("/")
    if not norm_path:
        return
    existing = (
        db.query(models.Route)
        .filter(models.Route.method == method, models.Route.path == norm_path)
        .one_or_none()
    )
    if existing is not None:
        return
    status_code = create.get("status_code", 200)
    if not isinstance(status_code, int):
        status_code = 200
    response_body = _render_template(create.get("response_body", "OK"), ctx)
    content_type = _render_template(create.get("content_type", "text/plain"), ctx)
    body_encoding = create.get("body_encoding", DEFAULT_BODY_ENCODING)
    headers = create.get("headers")
    if not isinstance(headers, dict):
        headers = {}
    rendered_headers = {str(k): _render_template(v, ctx) for k, v in headers.items()}
    db_route = models.Route(
        method=method,
        path=norm_path,
        status_code=status_code,
        response_body=response_body,
        content_type=content_type,
        body_encoding=body_encoding,
    )
    db_route.set_headers(rendered_headers)
    db.add(db_route)
    db.commit()


def _apply_rule_state(db: Session, action: dict[str, Any], ctx: dict[str, Any]) -> None:
    state_action = action.get("set_state")
    chain = action.get("chain")
    raw_key = None
    if isinstance(state_action, dict):
        raw_key = state_action.get("key")
    if raw_key is None:
        raw_key = ctx.get("state_key")
    if raw_key is None:
        return
    state_key = _render_template(raw_key, ctx).strip()
    if not state_key:
        return

    raw_data: dict[str, Any] = {}
    ttl_seconds = None
    if isinstance(state_action, dict):
        raw_data = state_action.get("data") if isinstance(state_action.get("data"), dict) else {}
        ttl_seconds = state_action.get("ttl_seconds")
    if isinstance(chain, dict) and isinstance(chain.get("ttl_seconds"), int):
        ttl_seconds = chain.get("ttl_seconds")
    expires_at = None
    if isinstance(ttl_seconds, int) and ttl_seconds > 0:
        expires_at = datetime.now(timezone.utc) + timedelta(seconds=ttl_seconds)

    row = (
        db.query(models.RuleState)
        .filter(models.RuleState.state_key == state_key)
        .one_or_none()
    )
    payload = {}
    if row is None:
        row = models.RuleState(state_key=state_key)
        db.add(row)
    else:
        payload = row.payload

    data = {str(k): _render_template(v, ctx) for k, v in raw_data.items()}
    payload.update(data)
    if isinstance(chain, dict):
        hops = payload.get("__hops")
        payload["__hops"] = (hops if isinstance(hops, int) else 0) + 1
        payload["__last_seen"] = datetime.now(timezone.utc).timestamp()

    row.set_payload(payload)
    row.expires_at = expires_at
    row.updated_at = datetime.utcnow()
    db.commit()
