"""Claude Code PostToolUse adapter.

Expands abbreviations in a tool's output before Claude sees it. The output
keeps its exact shape, because Claude Code ignores a replacement that does
not match the tool's output schema. Only string values change, and values
under SKIP_KEYS pass through: Claude needs real paths to open files, and
base64 or IDs would break if rewritten.

Claude Code continues with the original output if this hook fails, so a
failure is reported on stderr and is not a guarantee of filtering.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

SKIP_KEYS = frozenset({
    "filePath", "file_path", "filenames", "path", "url",
    "base64", "data", "type", "mimeType", "media_type", "id", "tool_use_id",
})


def expand_output(value, expand_text, key=None):
    if key in SKIP_KEYS:
        return value
    if isinstance(value, str):
        return expand_text(value)
    if isinstance(value, list):
        return [expand_output(item, expand_text, key) for item in value]
    if isinstance(value, dict):
        return {name: expand_output(item, expand_text, name) for name, item in value.items()}
    return value


def main():
    try:
        from expand_abbreviations import expand_text

        response = json.load(sys.stdin.buffer)["tool_response"]
        expanded = expand_output(response, expand_text)
    except (ImportError, OSError, ValueError, KeyError, TypeError, RecursionError):
        print("Abbreviation filter failed. Tool output was not checked.", file=sys.stderr)
        return 1

    if expanded != response:
        print(json.dumps({
            "hookSpecificOutput": {
                "hookEventName": "PostToolUse",
                "updatedToolOutput": expanded,
            },
        }))
    return 0


if __name__ == "__main__":
    sys.exit(main())
