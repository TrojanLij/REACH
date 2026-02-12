# reach/core/db/session.py
from __future__ import annotations

from typing import Any, Callable, Iterator
from functools import wraps
import inspect
from sqlalchemy.orm import Session

from .engine import SessionLocal


def get_db() -> Iterator[Session]:
    db: Session = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def with_session(fn: Callable[..., Any]) -> Callable[..., Any]:
    """
    Decorator that injects a managed SessionLocal into a sync helper.
    """
    sig = inspect.signature(fn)

    @wraps(fn)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        if "db" not in sig.parameters:
            return fn(*args, **kwargs)
        if "db" in kwargs and kwargs["db"] is not None:
            return fn(*args, **kwargs)
        db: Session = SessionLocal()
        try:
            return fn(*args, db=db, **kwargs)
        finally:
            db.close()

    return wrapper
