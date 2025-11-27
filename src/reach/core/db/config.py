# reach/core/db/config.py
from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass
class DBSettings:
    # Empty string means "use default SQLite"
    url: str = os.getenv("REACH_DB_URL", "")
    # Set to "1" to enable SQLAlchemy echo logging
    echo: bool = os.getenv("REACH_DB_ECHO", "0") == "1"
    # Optional explicit SQLite file path, e.g. "~/.reach/reach_core.db"
    sqlite_path: str | None = os.getenv("REACH_DB_FILE") or None


settings = DBSettings()
