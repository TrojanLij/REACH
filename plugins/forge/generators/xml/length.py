"""A for-fun payload to test the forge generator interaction."""

from __future__ import annotations

__all__ = ["PLUGIN", "generate"]

PLUGIN = {
    "api_version": "1",
    "type": "generator",
    "kind": "xml_length",
    "entrypoint": "generate",
    "summary": "Emit an 'x' string of requested length.",
    "requires_python": [],
    "requires_system": [],
}


def generate(length: int = 10) -> str:
    """
    Simple python function for testing forge console interaction.

    Params:
    - length: Number of characters to return.

    Returns:
    - Rendered payload string.
    """
    ret = ""
    for _ in range(int(length)):
        ret = f"{ret}x"

    return ret
