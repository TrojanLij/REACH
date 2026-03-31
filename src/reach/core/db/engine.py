# reach/core/db/engine.py
from __future__ import annotations

from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from .config import settings

# If REACH_DB_URL is set, we use that.
# Otherwise we create / use a SQLite file.
if settings.url:
    db_url = settings.url
else:
    if settings.sqlite_path:
        db_path = Path(settings.sqlite_path).expanduser()
    else:
        BASE_DIR = Path(__file__).resolve().parent.parent.parent  # .../reach/
        db_path = BASE_DIR / "reach_core.db"
    db_url = f"sqlite:///{db_path}"

engine = create_engine(
    db_url,
    future=True,
    echo=settings.echo,
    connect_args={"check_same_thread": False} if db_url.startswith("sqlite:///") else {},
)

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
    future=True,
)
