"""Base64 encode filter."""

from base64 import b64encode


def filter(value: str) -> str:
    return b64encode(value.encode("utf-8")).decode("utf-8")


NAME = "b64encode"
