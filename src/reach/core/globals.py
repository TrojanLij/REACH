"""Global configuration values shared across REACH Core. This is for commonly used variables or functions used throught the project. NOT FOR SECRETS OR TOKENS. USE ENV FILES!!!"""

from __future__ import annotations

import secrets
import string

RESERVED_PREFIXES = (
    "api/",
    "debug/",
    "docs",
    "docs/",
    "openapi.json",
    "redoc",
    "redoc/",
    "favicon.ico",
)


def random_string(length: int = 16, alphabet: str | None = None) -> str:
    """Return a cryptographically secure random string."""
    if length <= 0:
        raise ValueError("length must be > 0")
    chars = alphabet or (string.ascii_letters + string.digits)
    return "".join(secrets.choice(chars) for _ in range(length))


def random_id(prefix: str | None = None, length: int = 12) -> str:
    """Return a short random identifier, optionally with a prefix."""
    value = random_string(length=length)
    return f"{prefix}{value}" if prefix else value
