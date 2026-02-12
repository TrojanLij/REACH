"""URL decode filter."""

from urllib.parse import unquote_plus


def filter(value: str) -> str:
    return unquote_plus(value)


NAME = "url_decode"
