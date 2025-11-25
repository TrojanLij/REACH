# reach/core/api/routes.py
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..db import get_db, models
from ..db.schemas import RouteCreate, RouteUpdate, RouteOut

router = APIRouter(prefix="/api/routes", tags=["routes"])


def _normalize_path(path: str) -> str:
    return path.lstrip("/")

@router.get("", response_model=list[RouteOut])
def list_routes(db: Session = Depends(get_db)):
    stmt = select(models.Route).order_by(models.Route.id)
    routes = db.execute(stmt).scalars().all()
    return routes


@router.post("", response_model=RouteOut, status_code=201)
def create_route(route_in: RouteCreate, db: Session = Depends(get_db)):
    method = route_in.method.upper()
    path = _normalize_path(route_in.path)

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
    db.add(db_route)
    db.commit()
    db.refresh(db_route)
    return db_route


@router.get("/{route_id}", response_model=RouteOut)
def get_route(route_id: int, db: Session = Depends(get_db)):
    db_route = db.get(models.Route, route_id)
    if not db_route:
        raise HTTPException(status_code=404, detail="Route not found")
    return db_route


@router.patch("/{route_id}", response_model=RouteOut)
def update_route(route_id: int, route_upd: RouteUpdate, db: Session = Depends(get_db)):
    db_route = db.get(models.Route, route_id)
    if not db_route:
        raise HTTPException(status_code=404, detail="Route not found")

    if route_upd.status_code is not None:
        db_route.status_code = route_upd.status_code

    if route_upd.response_body is not None:
        db_route.response_body = route_upd.response_body

    if route_upd.content_type is not None:
        db_route.content_type = route_upd.content_type

    if route_upd.body_encoding is not None:
        db_route.body_encoding = route_upd.body_encoding

    from datetime import datetime
    db_route.updated_at = datetime.utcnow()

    db.add(db_route)
    db.commit()
    db.refresh(db_route)
    return db_route



@router.delete("/{route_id}", status_code=204)
def delete_route(route_id: int, db: Session = Depends(get_db)):
    db_route = db.get(models.Route, route_id)
    if not db_route:
        raise HTTPException(status_code=404, detail="Route not found")
    db.delete(db_route)
    db.commit()
