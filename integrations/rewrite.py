"""Adapt JSON payloads to the raw text filter without rewriting member names."""
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from expand_abbreviations import expand_text


def rewrite(value):
    if isinstance(value, str):
        return expand_text(value)
    if isinstance(value, list):
        return [rewrite(item) for item in value]
    if isinstance(value, dict):
        if any(expand_text(key) != key for key in value):
            raise ValueError("abbreviation in a JSON member name")
        return {key: rewrite(item) for key, item in value.items()}
    return value


if __name__ == "__main__":
    try:
        result = rewrite(json.load(sys.stdin.buffer))
        print(json.dumps(result, allow_nan=False))
    except (ValueError, RecursionError, OSError):
        sys.exit("Could not filter provider payload.")
