"""Base64 decode filter."""

from base64 import b64decode


def filter(value: str) -> str:
    try:
        return b64decode(value).decode("utf-8", errors="replace")
    except Exception:
        return ""


NAME = "b64decode"
