"""Claude Code UserPromptSubmit adapter.

Claude Code attaches @-mentioned files after this hook runs, and the hook
only sees the mention, so the files are read and checked here. They cannot
be rewritten, so a match blocks the prompt and names the file to fix.
"""
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

# @path or @"path with spaces", at the start or after whitespace so email
# addresses are not read as mentions. An optional #L10-20 range is dropped.
MENTION = re.compile(r'(?<!\S)@(?:"([^"]+)"|(\S+))')


def block(reason):
    print(json.dumps({
        "decision": "block",
        "reason": reason,
        "hookSpecificOutput": {
            "hookEventName": "UserPromptSubmit",
            "suppressOriginalPrompt": True,
        },
    }))


def mentioned_files(prompt, cwd):
    for quoted, bare in MENTION.findall(prompt):
        candidates = [quoted] if quoted else [bare, bare.rstrip(".,;:!?)")]
        for candidate in candidates:
            path = Path(candidate.split("#", 1)[0]).expanduser()
            path = path if path.is_absolute() else cwd / path
            if path.is_file():
                yield path
                break


def flagged_files(prompt, cwd, pattern):
    flagged = []
    for path in dict.fromkeys(mentioned_files(prompt, cwd)):
        try:
            data = path.read_bytes()
        except OSError:
            continue  # Claude Code cannot attach it either.
        # Binary files such as images cannot be checked as text.
        if b"\0" not in data and pattern.search(data.decode("utf-8", "replace")):
            flagged.append(path)
    return flagged


def main():
    try:
        from expand_abbreviations import PATTERN, expand_text

        event = json.load(sys.stdin.buffer)
        prompt = event["prompt"]
        expanded = expand_text(prompt)
        flagged = flagged_files(prompt, Path(event.get("cwd") or Path.cwd()), PATTERN)
    except (ImportError, OSError, ValueError, KeyError, TypeError):
        block("Abbreviation filter failed. Check the hook installation.")
        return

    if flagged:
        files = "\n".join(f"- {path}" for path in flagged)
        reason = (
            "These @-mentioned files contain configured abbreviations. "
            "Expand them in the files or remove the mentions, then resubmit:\n\n" + files
        )
        if expanded != prompt:
            reason += "\n\nUse this expanded prompt:\n\n" + expanded
        block(reason)
    elif expanded != prompt:
        block("Resubmit this expanded prompt:\n\n" + expanded)


if __name__ == "__main__":
    main()
