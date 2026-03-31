"""Admin CRUD API for REACH Core trigger rules."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..db import get_db, models
from ..db.schemas import (
    RulePreviewRequest,
    RulePreviewResponse,
    RulePreviewStep,
    TriggerRuleCreate,
    TriggerRuleOut,
    TriggerRuleUpdate,
)
from ..routing.dynamic import (
    _action_creates_route,
    _chain_allows,
    _render_template,
    _rule_matches,
    _rule_status_code,
    _validate_forward_url_template,
)
from ..routing.filters import FILTERS

router = APIRouter(prefix="/api/rules", tags=["rules"])


def _apply_rule_updates(db_rule: models.TriggerRule, rule_upd: TriggerRuleUpdate) -> None:
    """Apply a partial TriggerRuleUpdate to an existing rule row."""
    if rule_upd.name is not None:
        db_rule.name = rule_upd.name
    if rule_upd.enabled is not None:
        db_rule.enabled = rule_upd.enabled
    if rule_upd.priority is not None:
        db_rule.priority = rule_upd.priority
    if rule_upd.match is not None:
        db_rule.set_match(rule_upd.match)
    if rule_upd.action is not None:
        _validate_trigger_rule_action(rule_upd.action)
        db_rule.set_action(rule_upd.action)


def _validate_trigger_rule_action(action: dict[str, Any]) -> None:
    forward = action.get("forward")
    if not isinstance(forward, dict):
        return
    reason = _validate_forward_url_template(forward.get("url"))
    if reason is not None:
        raise HTTPException(status_code=400, detail=reason)


@router.get("", response_model=list[TriggerRuleOut])
def list_rules(db: Session = Depends(get_db)) -> list[TriggerRuleOut]:
    """List all stored trigger rules ordered by priority."""
    stmt = select(models.TriggerRule).order_by(models.TriggerRule.priority, models.TriggerRule.id)
    rules = db.execute(stmt).scalars().all()
    return rules


def _preview_step(steps: list[RulePreviewStep], label: str, ok: bool, detail: str) -> None:
    steps.append(RulePreviewStep(label=label, ok=ok, detail=detail))


def _normalize_preview_context(raw_request: dict[str, Any]) -> dict[str, Any]:
    method = str(raw_request.get("method", "GET")).upper()
    path = str(raw_request.get("path", "/"))
    if not path.startswith("/"):
        path = "/" + path
    headers_raw = raw_request.get("headers")
    query_raw = raw_request.get("query")
    state_raw = raw_request.get("state")
    headers = {}
    if isinstance(headers_raw, dict):
        headers = {str(k).lower(): str(v) for k, v in headers_raw.items()}
    query = {}
    if isinstance(query_raw, dict):
        query = {str(k): str(v) for k, v in query_raw.items()}
    state: dict[str, Any] = {}
    if isinstance(state_raw, dict):
        state = state_raw
    return {
        "method": method,
        "path": path,
        "host": str(raw_request.get("host", "")),
        "headers": headers,
        "query": query,
        "body": str(raw_request.get("body", "")),
        "client_ip": str(raw_request.get("client_ip", "")),
        "route_exists": bool(raw_request.get("route_exists", True)),
        "state_key": str(raw_request.get("state_key", "")),
        "state": state,
    }


def _render_action_preview(action: dict[str, Any], ctx: dict[str, Any]) -> dict[str, Any]:
    body = action.get("body")
    if body is None:
        body = action.get("response_body", "")
    headers = action.get("headers")
    if not isinstance(headers, dict):
        headers = {}
    rendered_headers = {str(k): _render_template(v, ctx) for k, v in headers.items()}

    preview: dict[str, Any] = {
        "status_code": _rule_status_code(action),
        "content_type": _render_template(action.get("content_type", "text/plain"), ctx),
        "body": _render_template(body, ctx),
        "headers": rendered_headers,
    }

    forward = action.get("forward")
    if isinstance(forward, dict):
        forward_headers = forward.get("headers")
        if not isinstance(forward_headers, dict):
            forward_headers = {}
        preview["forward"] = {
            "url": _render_template(forward.get("url"), ctx).strip(),
            "method": str(forward.get("method", "POST")).upper(),
            "headers": {str(k): _render_template(v, ctx) for k, v in forward_headers.items()},
            "body": None
            if forward.get("body") is None
            else _render_template(forward.get("body"), ctx),
        }

    create = action.get("create_route")
    if isinstance(create, dict):
        preview["create_route"] = {
            "method": _render_template(create.get("method", ctx.get("method", "GET")), ctx).upper(),
            "path": _render_template(create.get("path", ctx.get("path", "/")), ctx),
            "status_code": create.get("status_code", 200)
            if isinstance(create.get("status_code"), int)
            else 200,
            "content_type": _render_template(create.get("content_type", "text/plain"), ctx),
            "response_body": _render_template(create.get("response_body", "OK"), ctx),
        }

    return preview


@router.get("/filters", response_model=list[str])
def list_rule_filters() -> list[str]:
    """List the currently loaded rule filter names."""
    return sorted(FILTERS.keys())


@router.post("/preview", response_model=RulePreviewResponse)
def preview_rule(payload: RulePreviewRequest) -> RulePreviewResponse:
    """Run a non-mutating rule preview against supplied request context."""
    steps: list[RulePreviewStep] = []
    rule_data = payload.rule.model_dump()
    match = rule_data.get("match")
    action = rule_data.get("action")
    if not isinstance(match, dict):
        match = {}
    if not isinstance(action, dict):
        action = {}

    if not bool(rule_data.get("enabled", True)):
        _preview_step(steps, "rule.enabled", False, "Rule is disabled.")
        return RulePreviewResponse(
            matched=False,
            steps=steps,
            rendered_context={},
            rendered_action=None,
        )
    _preview_step(steps, "rule.enabled", True, "Rule is enabled.")

    ctx = _normalize_preview_context(payload.request)
    stage = str(match.get("stage", "post")).lower()
    if stage != "pre" and not ctx["route_exists"] and not _action_creates_route(action):
        _preview_step(
            steps,
            "match.stage",
            False,
            f"stage={stage}, route_exists=false, and action.create_route missing.",
        )
        return RulePreviewResponse(
            matched=False,
            steps=steps,
            rendered_context=ctx,
            rendered_action=None,
        )
    _preview_step(
        steps,
        "match.stage",
        True,
        f"stage={stage}, route_exists={str(ctx['route_exists']).lower()}",
    )

    if "state_key" in match:
        rendered_state_key = _render_template(match.get("state_key"), ctx).strip()
        ctx["state_key"] = rendered_state_key
        _preview_step(
            steps,
            "match.state_key",
            True,
            f"Resolved to '{rendered_state_key}'.",
        )

    matched = _rule_matches(match, ctx)
    _preview_step(
        steps,
        "match.result",
        matched,
        "Rule matched request context." if matched else "Rule did not match request context.",
    )
    if not matched:
        return RulePreviewResponse(
            matched=False,
            steps=steps,
            rendered_context=ctx,
            rendered_action=None,
        )

    state_data = ctx["state"] if isinstance(ctx.get("state"), dict) else {}
    chain_ok = _chain_allows(action, state_data)
    _preview_step(
        steps,
        "action.chain",
        chain_ok,
        "Chain checks passed." if chain_ok else "Chain checks blocked action.",
    )
    if not chain_ok:
        return RulePreviewResponse(
            matched=False,
            steps=steps,
            rendered_context=ctx,
            rendered_action=None,
        )

    rendered_action = _render_action_preview(action, ctx)
    _preview_step(steps, "action.render", True, "Action rendered with backend filters.")
    return RulePreviewResponse(
        matched=True,
        steps=steps,
        rendered_context=ctx,
        rendered_action=rendered_action,
    )


@router.post("", response_model=TriggerRuleOut, status_code=201)
def create_rule(rule_in: TriggerRuleCreate, db: Session = Depends(get_db)) -> TriggerRuleOut:
    """Create a new trigger rule."""
    _validate_trigger_rule_action(rule_in.action)
    db_rule = models.TriggerRule(
        name=rule_in.name,
        enabled=rule_in.enabled,
        priority=rule_in.priority,
    )
    db_rule.set_match(rule_in.match)
    db_rule.set_action(rule_in.action)
    db.add(db_rule)
    db.commit()
    db.refresh(db_rule)
    return db_rule


@router.get("/{rule_id}", response_model=TriggerRuleOut)
def get_rule(rule_id: int, db: Session = Depends(get_db)) -> TriggerRuleOut:
    """Retrieve a single trigger rule by id."""
    db_rule = db.get(models.TriggerRule, rule_id)
    if not db_rule:
        raise HTTPException(status_code=404, detail="Rule not found")
    return db_rule


@router.patch("/{rule_id}", response_model=TriggerRuleOut)
def update_rule(rule_id: int, rule_upd: TriggerRuleUpdate, db: Session = Depends(get_db)) -> TriggerRuleOut:
    """Apply a partial update to an existing trigger rule."""
    db_rule = db.get(models.TriggerRule, rule_id)
    if not db_rule:
        raise HTTPException(status_code=404, detail="Rule not found")
    _apply_rule_updates(db_rule, rule_upd)
    db_rule.updated_at = datetime.now(UTC)
    db.add(db_rule)
    db.commit()
    db.refresh(db_rule)
    return db_rule


@router.delete("/{rule_id}", status_code=204)
def delete_rule(rule_id: int, db: Session = Depends(get_db)) -> None:
    """Delete a stored trigger rule."""
    db_rule = db.get(models.TriggerRule, rule_id)
    if not db_rule:
        raise HTTPException(status_code=404, detail="Rule not found")
    db.delete(db_rule)
    db.commit()
