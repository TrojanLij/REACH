# reach/core/db/engine.py
from __future__ import annotations

import os
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from .config import settings

# If REACH_DB_URL is set, we use that.
# Otherwise we create a SQLite file next to your project root.
if settings.url:
    db_url = settings.url
else:
    BASE_DIR = Path(__file__).resolve().parent.parent.parent  # .../reach/
    db_path = BASE_DIR / "reach_core.db"
    db_url = f"sqlite:///{db_path}"

engine = create_engine(
    db_url,
    future=True,
    echo=True,  # TEMP: True so you can see SQL in the console
)

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
    future=True,
)
