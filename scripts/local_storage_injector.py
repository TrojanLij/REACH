#!/usr/bin/env python3
"""Standalone localStorage injector for browser session replay testing.

This MVP is intentionally separate from REACH internals.
"""

from __future__ import annotations

import argparse
import json
import sys
from importlib.util import find_spec
from pathlib import Path
from urllib.parse import urlparse


VALID_BROWSERS = {"chromium", "firefox", "webkit"}


def _validate_origin(origin: str) -> str:
    parsed = urlparse(origin)
    if parsed.scheme not in {"http", "https"}:
        raise ValueError("origin must include http:// or https://")
    if not parsed.netloc:
        raise ValueError("origin must include a host")
    if parsed.path not in {"", "/"} or parsed.params or parsed.query or parsed.fragment:
        raise ValueError("origin must be scheme://host[:port] with no path/query/fragment")
    return f"{parsed.scheme}://{parsed.netloc}"


def _parse_key_value(items: list[str]) -> dict[str, str]:
    out: dict[str, str] = {}
    for item in items:
        if "=" not in item:
            raise ValueError(f"invalid --set value '{item}', expected key=value")
        key, value = item.split("=", 1)
        key = key.strip()
        if not key:
            raise ValueError(f"invalid --set value '{item}', key cannot be empty")
        out[key] = value
    return out


def _load_json_map(path: Path | None, inline_json: str | None) -> dict[str, str]:
    merged: dict[str, str] = {}

    def _convert_map(data: object, source: str) -> dict[str, str]:
        if not isinstance(data, dict):
            raise ValueError(f"{source} must contain a JSON object of key/value pairs")
        out: dict[str, str] = {}
        for key, value in data.items():
            if not isinstance(key, str) or not key:
                raise ValueError(f"{source} contains an invalid key: {key!r}")
            # localStorage values are strings; stringify non-string values.
            out[key] = value if isinstance(value, str) else json.dumps(value)
        return out

    if path:
        file_data = json.loads(path.read_text(encoding="utf-8"))
        merged.update(_convert_map(file_data, str(path)))

    if inline_json:
        inline_data = json.loads(inline_json)
        merged.update(_convert_map(inline_data, "--json"))

    return merged


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Inject localStorage entries before first navigation using Playwright.",
    )
    parser.add_argument("--origin", required=True, help="Target origin (e.g. https://app.example.com)")
    parser.add_argument(
        "--navigate",
        help="URL to open after injection. Defaults to --origin if omitted.",
    )
    parser.add_argument(
        "--set",
        action="append",
        default=[],
        metavar="KEY=VALUE",
        help="localStorage entry. Repeat for multiple values.",
    )
    parser.add_argument(
        "--state-file",
        type=Path,
        help="JSON file with localStorage key/value map.",
    )
    parser.add_argument(
        "--json",
        help='Inline JSON object of key/value pairs, e.g. {"token":"abc"}',
    )
    parser.add_argument(
        "--browser",
        default="chromium",
        choices=sorted(VALID_BROWSERS),
        help="Browser engine to run.",
    )
    parser.add_argument(
        "--headless",
        action="store_true",
        help="Run headless (default is headed for operator inspection).",
    )
    parser.add_argument(
        "--wait-ms",
        type=int,
        default=10000,
        help="How long to keep the page open after navigation (default: 10000).",
    )
    parser.add_argument(
        "--keep-open",
        action="store_true",
        help="Keep browser open until interrupted (Ctrl+C).",
    )
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    try:
        origin = _validate_origin(args.origin)

        if args.state_file and not args.state_file.exists():
            raise ValueError(f"state file does not exist: {args.state_file}")

        state_map = _load_json_map(args.state_file, args.json)
        state_map.update(_parse_key_value(args.set))

        if not state_map:
            raise ValueError("no localStorage values provided; use --set, --json, or --state-file")

        navigate_url = args.navigate or origin

        local_storage = [{"name": key, "value": value} for key, value in state_map.items()]
        storage_state = {"origins": [{"origin": origin, "localStorage": local_storage}]}

        print(f"[+] Origin: {origin}")
        print(f"[+] Navigate: {navigate_url}")
        print(f"[+] Keys injected: {', '.join(state_map.keys())}")
        print(f"[+] Browser: {args.browser} (headless={args.headless})")

        if find_spec("playwright.sync_api") is None:
            raise RuntimeError(
                "Playwright is not installed. Run: python3 -m pip install playwright "
                "and then: python3 -m playwright install"
            )

        from playwright.sync_api import sync_playwright

        with sync_playwright() as playwright:
            browser = getattr(playwright, args.browser).launch(headless=args.headless)
            context = browser.new_context(storage_state=storage_state)
            page = context.new_page()
            page.goto(navigate_url, wait_until="domcontentloaded")
            if args.keep_open:
                print("[+] Browser will remain open. Press Ctrl+C to close.")
                try:
                    while True:
                        page.wait_for_timeout(1000)
                except KeyboardInterrupt:
                    print("[+] Closing browser.")
            else:
                page.wait_for_timeout(max(args.wait_ms, 0))
            context.close()
            browser.close()

        print("[+] Injection flow complete.")
        return 0
    except Exception as exc:
        print(f"[!] Error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
