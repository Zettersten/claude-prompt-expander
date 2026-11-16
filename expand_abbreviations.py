#!/usr/bin/env python3
"""Read raw UTF-8 text from stdin and expand standalone abbreviations."""

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


def _any_case(key: str) -> str:
    # Explicit ASCII classes instead of re.IGNORECASE, which would also match
    # Unicode look-alikes such as "ſ" for "s" and break the lookup below.
    return "".join(f"[{c}{c.upper()}]" if c.isalpha() else re.escape(c) for c in key)


# Match an abbreviation only as a whole token: no letter or digit, in any
# script, may touch either side. "dow" matches "DoW", "DoW's", "DoW-wide",
# and "dow_report", but not "download", "window", or "shadow". Underscores
# and punctuation count as separators. Longer keys go first so a key that
# prefixes another can never shadow it.
WORD_CHAR = r"[^\W_]"
PATTERN = re.compile(
    rf"(?<!{WORD_CHAR})(?:"
    + "|".join(map(_any_case, sorted(ABBREVIATIONS, key=len, reverse=True)))
    + rf")(?!{WORD_CHAR})"
)


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
