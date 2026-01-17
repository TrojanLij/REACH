"""Admin CRUD API for REACH Core dynamic routes."""
from __future__ import annotations

from datetime import datetime
from functools import wraps
from typing import Callable, Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..db import get_db, models
from ..db.schemas import RouteCreate, RouteUpdate, RouteOut

router = APIRouter(prefix="/api/routes", tags=["routes"])


def _normalize_path(path: str) -> str:
    """Normalize a route path to the stored form (no leading slash)."""
    return path.lstrip("/")


def _normalize_headers(headers: dict[str, str] | None) -> dict[str, str]:
    """Ensure headers are a {str: str} mapping."""
    if not headers:
        return {}
    return {str(k): str(v) for k, v in headers.items()}


def _model_copy(model: Any, update: dict[str, Any]) -> Any:
    if hasattr(model, "model_copy"):
        return model.model_copy(update=update)
    return model.copy(update=update)


def normalize_route_input(fn: Callable[..., Any]) -> Callable[..., Any]:
    """Normalize route path and headers for CRUD endpoints."""

    @wraps(fn)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        route_in = kwargs.get("route_in")
        if isinstance(route_in, RouteCreate):
            kwargs["route_in"] = _model_copy(
                route_in,
                {
                    "path": _normalize_path(route_in.path),
                    "headers": _normalize_headers(route_in.headers),
                },
            )

        route_upd = kwargs.get("route_upd")
        if isinstance(route_upd, RouteUpdate) and route_upd.headers is not None:
            kwargs["route_upd"] = _model_copy(
                route_upd,
                {"headers": _normalize_headers(route_upd.headers)},
            )

        return fn(*args, **kwargs)

    return wrapper


def _apply_route_updates(db_route: models.Route, route_upd: RouteUpdate) -> None:
    """Apply a partial RouteUpdate to an existing Route row."""
    if route_upd.status_code is not None:
        db_route.status_code = route_upd.status_code

    if route_upd.response_body is not None:
        db_route.response_body = route_upd.response_body

    if route_upd.content_type is not None:
        db_route.content_type = route_upd.content_type

    if route_upd.body_encoding is not None:
        db_route.body_encoding = route_upd.body_encoding

    if route_upd.headers is not None:
        db_route.set_headers(_normalize_headers(route_upd.headers))


@router.get("", response_model=list[RouteOut])
def list_routes(db: Session = Depends(get_db)) -> list[RouteOut]:
    """List all stored dynamic routes ordered by id."""
    stmt = select(models.Route).order_by(models.Route.id)
    routes = db.execute(stmt).scalars().all()
    return routes


@router.post("", response_model=RouteOut, status_code=201)
@normalize_route_input
def create_route(route_in: RouteCreate, db: Session = Depends(get_db)) -> RouteOut:
    """Create a new dynamic route; fail if method+path already exists."""
    method = route_in.method.upper()
    path = route_in.path

    dup_stmt = select(models.Route).where(
        models.Route.method == method,
        models.Route.path == path,
    )
    existing = db.execute(dup_stmt).scalar_one_or_none()
    if existing:
        raise HTTPException(
            status_code=400,
            detail="Route with this method and path already exists",
        )

    db_route = models.Route(
        method=method,
        path=path,
        status_code=route_in.status_code,
        response_body=route_in.response_body,
        content_type=route_in.content_type,
        body_encoding=route_in.body_encoding,
    )
    db_route.set_headers(_normalize_headers(route_in.headers))
    db.add(db_route)
    db.commit()
    db.refresh(db_route)
    return db_route


@router.get("/{route_id}", response_model=RouteOut)
def get_route(route_id: int, db: Session = Depends(get_db)) -> RouteOut:
    """Retrieve a single dynamic route by id."""
    db_route = db.get(models.Route, route_id)
    if not db_route:
        raise HTTPException(status_code=404, detail="Route not found")
    return db_route


@router.patch("/{route_id}", response_model=RouteOut)
@normalize_route_input
def update_route(route_id: int, route_upd: RouteUpdate, db: Session = Depends(get_db)) -> RouteOut:
    """Apply a partial update to an existing dynamic route."""
    db_route = db.get(models.Route, route_id)
    if not db_route:
        raise HTTPException(status_code=404, detail="Route not found")

    _apply_route_updates(db_route, route_upd)
    db_route.updated_at = datetime.utcnow()

    db.add(db_route)
    db.commit()
    db.refresh(db_route)
    return db_route


@router.delete("/{route_id}", status_code=204)
def delete_route(route_id: int, db: Session = Depends(get_db)) -> None:
    """Delete a stored dynamic route."""
    db_route = db.get(models.Route, route_id)
    if not db_route:
        raise HTTPException(status_code=404, detail="Route not found")
    db.delete(db_route)
    db.commit()
