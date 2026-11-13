#!/usr/bin/env python3
"""Read raw UTF-8 text from stdin and expand literal substrings."""

import re
import sys

ABBREVIATIONS = {
    "cui": "Controlled Unclassified Information",
    "fouo": "For Official Use Only",
    "dod": "Department of Defense",
    "dow": "Department of War",
    "nsa": "National Security Agency",
    "nro": "National Reconnaissance Office",
    "eicd": "External Interface Control Document",
}

PATTERN = re.compile("|".join(ABBREVIATIONS), re.IGNORECASE | re.ASCII)


def expand_text(value: str) -> str:
    return PATTERN.sub(lambda match: ABBREVIATIONS[match[0].lower()], value)


def main() -> int:
    try:
        source = sys.stdin.buffer.read().decode("utf-8")
        sys.stdout.buffer.write(expand_text(source).encode("utf-8"))
        sys.stdout.buffer.flush()
    except (UnicodeError, OSError):
        print("Abbreviation filter failed.", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
