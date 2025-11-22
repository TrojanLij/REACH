# reach/core/db/session.py
from __future__ import annotations

from typing import Iterator
from sqlalchemy.orm import Session

from .engine import SessionLocal


def get_db() -> Iterator[Session]:
    db: Session = SessionLocal()
    try:
        yield db
    finally:
        db.close()
