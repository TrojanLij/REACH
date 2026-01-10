"""A for fun payload to test the forge payload generator."""

from __future__ import annotations
__all__ = ["generate"]

def generate(length: int = 10) -> str:
    """
    Simple python script for testing forge console interaction.

    Author: @Trojan
    
    Params:
    - length: How many characters??
    
    Returns:
    - Rendered payload string.
    
    """
    ret = ""
    for i in range(int(length)):
        ret = f"{ret}x"

    return ret