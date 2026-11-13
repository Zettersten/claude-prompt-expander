"""Claude Code UserPromptSubmit adapter."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))


def block(reason):
    print(json.dumps({
        "decision": "block",
        "reason": reason,
        "hookSpecificOutput": {
            "hookEventName": "UserPromptSubmit",
            "suppressOriginalPrompt": True,
        },
    }))


def main():
    try:
        from expand_abbreviations import expand_text

        prompt = json.load(sys.stdin.buffer)["prompt"]
        expanded = expand_text(prompt)
    except (ImportError, OSError, ValueError, KeyError, TypeError):
        block("Abbreviation filter failed. Check the hook installation.")
        return

    if expanded != prompt:
        block("Resubmit this expanded prompt:\n\n" + expanded)


if __name__ == "__main__":
    main()
