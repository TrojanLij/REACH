"""JSON path extraction filter."""

import json
from typing import Any


def filter(value: str, path: str) -> Any:
    if not path:
        return ""
    try:
        current: Any = json.loads(value)
    except Exception:
        return ""
    for part in path.split("."):
        if isinstance(current, dict) and part in current:
            current = current[part]
            continue
        if isinstance(current, list) and part.isdigit():
            index = int(part)
            if 0 <= index < len(current):
                current = current[index]
                continue
        return ""
    return current


NAME = "json_get"
