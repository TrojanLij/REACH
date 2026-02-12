"""JSON normalize filter."""

import json


def filter(value: str) -> str:
    try:
        return json.dumps(json.loads(value), separators=(",", ":"), ensure_ascii=True)
    except Exception:
        return value


NAME = "json"
