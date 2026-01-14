"""Admin CRUD API for REACH Core trigger rules."""

from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..db import get_db, models
from ..db.schemas import TriggerRuleCreate, TriggerRuleUpdate, TriggerRuleOut

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
        db_rule.set_action(rule_upd.action)


@router.get("", response_model=list[TriggerRuleOut])
def list_rules(db: Session = Depends(get_db)) -> list[TriggerRuleOut]:
    """List all stored trigger rules ordered by priority."""
    stmt = select(models.TriggerRule).order_by(models.TriggerRule.priority, models.TriggerRule.id)
    rules = db.execute(stmt).scalars().all()
    return rules


@router.post("", response_model=TriggerRuleOut, status_code=201)
def create_rule(rule_in: TriggerRuleCreate, db: Session = Depends(get_db)) -> TriggerRuleOut:
    """Create a new trigger rule."""
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
    db_rule.updated_at = datetime.utcnow()
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
