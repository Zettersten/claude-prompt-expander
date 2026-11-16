"""Run with: python3 -m unittest"""

import json
from pathlib import Path
import subprocess
import sys
import unittest

from expand_abbreviations import ABBREVIATIONS, expand_text

ROOT = Path(__file__).resolve().parent


class ExpandTextTest(unittest.TestCase):
    def test_expands_standalone_abbreviations_in_any_case(self):
        self.assertEqual(
            expand_text("Review the eIcD."),
            "Review the External Interface Control Document.",
        )
        self.assertEqual(expand_text("DOD"), "Department of Defense")
        self.assertEqual(expand_text("dod"), "Department of Defense")

    def test_expands_next_to_punctuation_and_separators(self):
        cases = {
            "(CUI)": "(Controlled Unclassified Information)",
            "DoD's budget": "Department of Defense's budget",
            "DoD-wide": "Department of Defense-wide",
            "NSA/NRO": "National Security Agency/National Reconnaissance Office",
            "cui_marking": "Controlled Unclassified Information_marking",
            '"FOUO"': '"For Official Use Only"',
            "line\nDoW\n": "line\nDepartment of War\n",
        }
        for source, expected in cases.items():
            with self.subTest(source=source):
                self.assertEqual(expand_text(source), expected)

    def test_ignores_abbreviations_inside_words(self):
        words = [
            "download", "Downloads", "window", "shadow", "meadow", "widow",
            "dodge", "Dodecahedron", "transaction", "compensate", "insane",
            "unsafe", "enroll", "unroll", "inroads", "circuit", "biscuit",
            "cuisine", "acuity", "nsaid", "eicds", "DoD2", "2DoD", "CUIs",
            "dowñ", "ñdow", "Ωnsa",
        ]
        for word in words:
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
        # Long s; IGNORECASE would match it and then fail the dict lookup.
        self.assertEqual(expand_text("nſa"), "nſa")


class AdapterTest(unittest.TestCase):
    def run_script(self, script, stdin):
        return subprocess.run(
            [sys.executable, str(ROOT / script)],
            input=stdin.encode(),
            capture_output=True,
            check=False,
        )

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
            json.dumps({"prompt": "Download the DoW report."}),
        )
        output = json.loads(result.stdout)
        self.assertEqual(output["decision"], "block")
        self.assertIn("Download the Department of War report.", output["reason"])

    def test_provider_rewrite_expands_values_only(self):
        payload = {"messages": [{"role": "user", "content": "NSA transaction download"}]}
        result = self.run_script("integrations/rewrite.py", json.dumps(payload))
        self.assertEqual(result.returncode, 0)
        self.assertEqual(
            json.loads(result.stdout)["messages"][0]["content"],
            "National Security Agency transaction download",
        )

    def test_provider_rewrite_rejects_abbreviated_member_names(self):
        result = self.run_script("integrations/rewrite.py", json.dumps({"cui": 1}))
        self.assertNotEqual(result.returncode, 0)


if __name__ == "__main__":
    unittest.main()
