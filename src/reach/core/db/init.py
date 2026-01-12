from __future__ import annotations

from threading import Lock

from .base import Base
from .engine import engine

_DB_INIT_LOCK = Lock()
_db_initialized = False


def init_db(force: bool = False) -> None:
    """
    Initialize database schema once per process unless force=True.
    """
    global _db_initialized
    with _DB_INIT_LOCK:
        if _db_initialized and not force:
            return
        Base.metadata.create_all(bind=engine)
        _db_initialized = True
