"""Get cookie from header by name."""

# from urllib.parse import quote_plus


def filter(value: str, search: str) -> str:
    cookies = value.split(";")
    target = search.strip()
    if not target:
        return "nothing"

    for cookie in cookies:
        cookie = cookie.strip()
        if not cookie:
            continue
        if "=" not in cookie:
            continue
        name, cookie_value = cookie.split("=", 1)
        if name.strip() == target:
            return cookie_value.strip()

    return "nothing"


NAME = "get_cookie"
