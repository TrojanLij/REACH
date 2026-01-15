"""URL encode filter."""

from urllib.parse import quote_plus


def filter(value: str) -> str:
    return quote_plus(value)


NAME = "url_encode"
