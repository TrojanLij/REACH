#!/usr/bin/env python3
"""Encode a text file into the same zero-width JavaScript payload format as hideV1.mjs."""

from __future__ import annotations

import argparse
from pathlib import Path


ZERO = "\u200b"
ONE = "\u200c"


def build_payload(source: str) -> str:
    bits = "".join(format(ord(char), "b").zfill(8) for char in source)
    hidden = bits.replace("0", ZERO).replace("1", ONE)

    return (
        f'eval("{hidden}".replace(/./g,c=>+!(c=="{ZERO}"))'
        ".replace(/.{8}/g,b=>String.fromCharCode('0b'+b)))\n"
    )


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Encode a UTF-8 text file into a zero-width JavaScript eval payload."
    )
    parser.add_argument("-i", "--input", required=True, help="Input file to encode")
    parser.add_argument("-o", "--output", required=True, help="Output file to write")
    args = parser.parse_args()

    input_path = Path(args.input)
    output_path = Path(args.output)

    source = input_path.read_text(encoding="utf-8")
    output_path.write_text(build_payload(source), encoding="utf-8")
    print(f"[+] {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
