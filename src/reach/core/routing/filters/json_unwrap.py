"""Unwrap JSON-encoded string layers.

Examples:
- '"{\\"a\\":1}"' -> '{"a":1}'
- '"\\"hello\\""' -> 'hello'
"""

import json


def _parse_depth(raw: str | int) -> int:
    if isinstance(raw, int):
        return raw if raw > 0 else 1
    try:
        value = int(str(raw).strip())
        return value if value > 0 else 1
    except Exception:
        return 1


def filter(value: str, depth: str | int = 1) -> str:
    current = str(value)
    layers = _parse_depth(depth)
    for _ in range(layers):
        try:
            parsed = json.loads(current)
        except Exception:
            return current
        if isinstance(parsed, str):
            current = parsed
            continue
        # Stop when decoded value is no longer a string.
        return current
    return current


NAME = "json_unwrap"
