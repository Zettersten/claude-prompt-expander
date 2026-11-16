"""Run with: python3 -m unittest

The tests take every term from ABBREVIATIONS rather than spelling any out, so
this file is safe to read and stays valid when the terms change.
"""

import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from expand_abbreviations import ABBREVIATIONS, expand_text

ROOT = Path(__file__).resolve().parent
KEY, EXPANSION = next(iter(ABBREVIATIONS.items()))

# Everyday words that have contained a configured term as a substring.
COMMON_WORDS = [
    "download", "Downloads", "window", "shadow", "meadow", "widow", "dodge",
    "Dodecahedron", "transaction", "compensate", "insane", "unsafe", "enroll",
    "unroll", "inroads", "circuit", "biscuit", "cuisine", "acuity",
]


def mixed_case(text):
    return "".join(c.upper() if i % 2 else c for i, c in enumerate(text))


class ExpandTextTest(unittest.TestCase):
    def test_expands_every_term_in_any_case(self):
        for key, expansion in ABBREVIATIONS.items():
            for form in (key, key.upper(), mixed_case(key)):
                with self.subTest(form=form):
                    self.assertEqual(expand_text(f"Review the {form}."), f"Review the {expansion}.")

    def test_expands_next_to_punctuation_and_separators(self):
        for key, expansion in ABBREVIATIONS.items():
            for before, after in [("(", ")"), ("", "'s"), ("", "-wide"), ("x/", "/y"),
                                  ("", "_report"), ('"', '"'), ("line\n", "\n")]:
                with self.subTest(key=key, before=before, after=after):
                    self.assertEqual(expand_text(before + key + after), before + expansion + after)

    def test_ignores_terms_inside_words(self):
        for key in ABBREVIATIONS:
            for word in (f"{key}s", f"x{key}", f"{key}2", f"2{key}", f"ñ{key}", f"{key}ñ"):
                with self.subTest(word=word):
                    self.assertEqual(expand_text(word), word)

    def test_ignores_common_words(self):
        for word in COMMON_WORDS:
            if word.lower() not in ABBREVIATIONS:
                with self.subTest(word=word):
                    self.assertEqual(expand_text(word), word)

    def test_dictionary_words_only_match_exact_keys(self):
        dictionary = Path("/usr/share/dict/words")
        if not dictionary.exists():
            self.skipTest("no system word list")
        for word in dictionary.read_text().split():
            if word.lower() not in ABBREVIATIONS:
                self.assertEqual(expand_text(word), word, word)

    def test_expansions_do_not_retrigger(self):
        for expansion in ABBREVIATIONS.values():
            with self.subTest(expansion=expansion):
                self.assertEqual(expand_text(expansion), expansion)

    def test_keys_are_lowercase_ascii(self):
        for key in ABBREVIATIONS:
            with self.subTest(key=key):
                self.assertTrue(key.isascii() and key.isalnum() and key == key.lower())

    def test_ignores_unicode_lookalikes(self):
        # Long s and Kelvin sign case-fold to "s" and "k" under re.IGNORECASE.
        for key in ABBREVIATIONS:
            lookalike = key.replace("s", "ſ").replace("k", "K")
            if lookalike != key:
                with self.subTest(key=key):
                    self.assertEqual(expand_text(lookalike), lookalike)


class AdapterTest(unittest.TestCase):
    def run_script(self, script, stdin):
        return subprocess.run(
            [sys.executable, str(ROOT / script)],
            input=stdin.encode(),
            capture_output=True,
            check=False,
        )

    def rewrite(self, payload):
        result = self.run_script("integrations/rewrite.py", json.dumps(payload))
        self.assertEqual(result.returncode, 0, result.stderr)
        return json.loads(result.stdout)

    def test_claude_code_hook_allows_clean_prompt(self):
        result = self.run_script(
            "integrations/claude-code/check_prompt.py",
            json.dumps({"prompt": "Download the window shadow report."}),
        )
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout, b"")

    def test_claude_code_hook_blocks_abbreviation(self):
        result = self.run_script(
            "integrations/claude-code/check_prompt.py",
            json.dumps({"prompt": f"Download the {KEY.upper()} report."}),
        )
        output = json.loads(result.stdout)
        self.assertEqual(output["decision"], "block")
        self.assertIn(f"Download the {EXPANSION} report.", output["reason"])

    def check_prompt(self, prompt, cwd):
        result = self.run_script(
            "integrations/claude-code/check_prompt.py",
            json.dumps({"prompt": prompt, "cwd": str(cwd)}),
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        return json.loads(result.stdout) if result.stdout else None

    def test_claude_code_hook_blocks_mentioned_files_with_terms(self):
        with tempfile.TemporaryDirectory() as tmp:
            cwd = Path(tmp)
            (cwd / "notes.txt").write_text(f"About the {KEY}.\n")
            (cwd / "spaced name.txt").write_text(KEY.upper())
            for prompt in ("Look at @notes.txt", "Look at @notes.txt.", "See @notes.txt#L1-2",
                           f"@{cwd / 'notes.txt'}", 'Read @"spaced name.txt" please'):
                with self.subTest(prompt=prompt):
                    output = self.check_prompt(prompt, cwd)
                    self.assertEqual(output["decision"], "block")
                    self.assertIn("@-mentioned files", output["reason"])
                    self.assertNotIn("expanded prompt", output["reason"])

            output = self.check_prompt(f"Explain the {KEY} in @notes.txt", cwd)
            self.assertIn(str(cwd / "notes.txt"), output["reason"])
            self.assertIn(f"Explain the {EXPANSION} in @notes.txt", output["reason"])

    def test_claude_code_hook_ignores_clean_binary_and_missing_mentions(self):
        with tempfile.TemporaryDirectory() as tmp:
            cwd = Path(tmp)
            (cwd / "clean.txt").write_text("Download the window shadow report.")
            (cwd / "image.png").write_bytes(b"\x89PNG\0" + KEY.encode())
            (cwd / "folder").mkdir()
            (cwd / "notes.txt").write_text(KEY)
            for prompt in ("@clean.txt", "@image.png", "@folder", "@missing.txt",
                           "mail me at user@notes.txt"):
                with self.subTest(prompt=prompt):
                    self.assertIsNone(self.check_prompt(prompt, cwd))

    def check_tool_output(self, response):
        result = self.run_script(
            "integrations/claude-code/check_tool_output.py",
            json.dumps({"hook_event_name": "PostToolUse", "tool_name": "X", "tool_response": response}),
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        if not result.stdout:
            return None
        output = json.loads(result.stdout)["hookSpecificOutput"]
        self.assertEqual(output["hookEventName"], "PostToolUse")
        return output["updatedToolOutput"]

    def test_tool_output_hook_expands_text_and_keeps_shape(self):
        bash = {"stdout": f"the {KEY} log", "stderr": KEY, "interrupted": False, "isImage": False}
        self.assertEqual(
            self.check_tool_output(bash),
            {"stdout": f"the {EXPANSION} log", "stderr": EXPANSION, "interrupted": False, "isImage": False},
        )
        read = {"type": "text", "file": {"filePath": f"/tmp/{KEY}.txt", "content": KEY, "numLines": 1}}
        self.assertEqual(
            self.check_tool_output(read),
            {"type": "text", "file": {"filePath": f"/tmp/{KEY}.txt", "content": EXPANSION, "numLines": 1}},
        )
        self.assertEqual(self.check_tool_output(f"MCP says {KEY}"), f"MCP says {EXPANSION}")
        mcp = [{"type": "text", "text": KEY}, {"type": "image", "data": f"+{KEY}/", "mimeType": "image/png"}]
        self.assertEqual(
            self.check_tool_output(mcp),
            [{"type": "text", "text": EXPANSION}, mcp[1]],
        )

    def test_tool_output_hook_is_silent_when_nothing_changes(self):
        for response in (
            {"stdout": "Download the window shadow report.", "stderr": ""},
            {"type": "image", "file": {"base64": f"+{KEY}/", "type": "image/png"}},
            {"filenames": [f"/tmp/{KEY}.txt"], "numFiles": 1},
        ):
            with self.subTest(response=response):
                self.assertIsNone(self.check_tool_output(response))

    def test_tool_output_hook_reports_bad_input(self):
        result = self.run_script("integrations/claude-code/check_tool_output.py", "not json")
        self.assertEqual(result.returncode, 1)
        self.assertEqual(result.stdout, b"")

    def test_provider_rewrite_expands_prose_fields(self):
        payload = {
            "system": f"About the {KEY}.",
            "instructions": KEY,
            "messages": [
                {"role": "user", "content": f"{KEY} transaction download"},
                {"role": "user", "content": [{"type": "text", "text": KEY}]},
                {"role": "user", "content": [
                    {"type": "tool_result", "tool_use_id": "t1", "content": KEY},
                ]},
            ],
        }
        result = self.rewrite(payload)
        self.assertEqual(result["system"], f"About the {EXPANSION}.")
        self.assertEqual(result["instructions"], EXPANSION)
        self.assertEqual(result["messages"][0]["content"], f"{EXPANSION} transaction download")
        self.assertEqual(result["messages"][1]["content"][0]["text"], EXPANSION)
        self.assertEqual(result["messages"][2]["content"][0]["content"], EXPANSION)

    def test_provider_rewrite_leaves_data_and_identifiers_alone(self):
        payload = {
            "model": KEY,
            KEY: KEY,
            "messages": [
                {"role": "user", "content": [
                    {"type": "image", "source": {
                        "type": "base64", "media_type": "image/png",
                        "data": f"iVBOR+{KEY}/{KEY.upper()}+AAA=",
                    }},
                    {"type": "image_url", "image_url": {"url": f"data:image/png;base64,+{KEY}/"}},
                ]},
                {"role": "assistant", "content": [
                    {"type": "thinking", "thinking": KEY, "signature": f"+{KEY}/"},
                    {"type": "redacted_thinking", "data": f"+{KEY}/"},
                    {"type": "tool_use", "id": KEY, "name": KEY, "input": {"command": KEY}},
                ]},
            ],
        }
        self.assertEqual(self.rewrite(payload), payload)


if __name__ == "__main__":
    unittest.main()
