# reach/core/db/config.py
from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass
class DBSettings:
    # Empty string means "use default SQLite"
    url: str = os.getenv("REACH_DB_URL", "")


settings = DBSettings()
