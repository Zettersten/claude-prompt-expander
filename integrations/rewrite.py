"""Expand abbreviations in the prose fields of a provider JSON payload.

Only strings stored under TEXT_KEYS are rewritten. Everything else passes
through untouched: base64 image and document data, thinking blocks and their
signatures, tool call IDs and arguments, model names, and member names.
Rewriting those would corrupt files or make the provider reject the request.
"""
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from expand_abbreviations import expand_text

# Keys that hold natural-language text across the Anthropic, OpenAI, and
# Gemini request shapes. A list under one of these keys inherits it, so
# "content": ["..."] is covered too.
TEXT_KEYS = frozenset({
    "text", "content", "system", "instructions", "prompt",
    "input", "output", "description",
})


def rewrite(value, key=None):
    if isinstance(value, str):
        return expand_text(value) if key in TEXT_KEYS else value
    if isinstance(value, list):
        return [rewrite(item, key) for item in value]
    if isinstance(value, dict):
        return {name: rewrite(item, name) for name, item in value.items()}
    return value


if __name__ == "__main__":
    try:
        result = rewrite(json.load(sys.stdin.buffer))
        print(json.dumps(result, allow_nan=False))
    except (ValueError, RecursionError, OSError):
        sys.exit("Could not filter provider payload.")
