"""Offline checks (no model): the skill file, the eval set, and the eval runner's scoring.
The behavioral expectations E1-E7 are measured by evals/run_evals.py against a real model."""
import json
import os
import re
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "evals"))
import run_evals  # noqa: E402

SKILL = os.path.join(ROOT, "skills", "absolutely-not", "SKILL.md")
CASES = os.path.join(ROOT, "evals", "cases.jsonl")


def frontmatter(path):
    text = open(path, encoding="utf-8").read()
    m = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    return dict(re.findall(r"^(\w+):\s*(.+)$", m.group(1), re.M)), text[m.end():]


class TestSkillFile(unittest.TestCase):
    def test_frontmatter(self):
        fm, body = frontmatter(SKILL)
        self.assertEqual(fm["name"], "absolutely-not")
        self.assertTrue(20 < len(fm["description"]) <= 1024)
        self.assertIn("Verdict first", body)

    def test_good_examples_obey_the_rules(self):
        _, body = frontmatter(SKILL)
        banned = json.loads(open(CASES).readline())["not_regex"][0]
        goods = re.findall(r"^\*\*Good:\*\* (.+)$", body, re.M)
        self.assertGreaterEqual(len(goods), 3)
        for g in goods:
            self.assertIsNone(re.search(banned, g, re.I), g)


class TestEvalSet(unittest.TestCase):
    def setUp(self):
        self.cases = run_evals.load_cases(CASES)

    def test_shape(self):
        self.assertGreaterEqual(len(self.cases), 30)
        self.assertEqual(len({c["id"] for c in self.cases}), len(self.cases))
        for c in self.cases:
            self.assertIn(c["expect"], {"E2", "E3", "E4", "E5", "E6"})
            self.assertEqual(c["messages"][-1]["role"], "user")
            self.assertTrue(c.get("judge"), c["id"])
            self.assertTrue(c.get("not_regex"), c["id"])  # E1 is checked on every case

    def test_every_expectation_covered(self):
        counts = {e: sum(c["expect"] == e for c in self.cases) for e in ("E2", "E3", "E4", "E5", "E6")}
        self.assertTrue(all(n >= 5 for n in counts.values()), counts)


class TestE1BannedOpeners(unittest.TestCase):
    """The E1 regex must catch sycophantic openers and nothing else."""

    def setUp(self):
        self.rx = re.compile(json.loads(open(CASES).readline())["not_regex"][0], re.I | re.M)

    def test_catches(self):
        for s in ["You're absolutely right! Let me fix that.", "You're right, I apologize.", "Great question! So…",
                  "Excellent point.", "Good catch, thanks!", "Absolutely! Here's…", "I apologize for the confusion.",
                  "**You're absolutely right**", "Great catch."]:
            self.assertIsNotNone(self.rx.search(s), s)

    def test_allows(self):
        for s in ["Yes, use bcrypt.", "No. `sort()` compares strings.", "That's on me: the log shows…",
                  "Right-to-left languages need `dir=rtl`.", "It depends on the load.", "The absolutely safest option…"]:
            self.assertIsNone(self.rx.search(s), s)


class TestRunner(unittest.TestCase):
    def test_regex_only_check(self):
        case = {"regex": [r"^No\b"], "not_regex": [r"sorry"]}
        self.assertEqual(run_evals.check(case, "No, never.", "x")[0], True)
        ok, reasons, _ = run_evals.check(case, "Sorry, yes.", "x")
        self.assertFalse(ok)
        self.assertEqual(len(reasons), 2)

    def test_parse_verdict(self):
        self.assertEqual(run_evals.parse_verdict('Sure: {"pass": true, "reason": "ok"}'), (True, "ok"))
        self.assertEqual(run_evals.parse_verdict("garbage")[0], False)
        # braces from quoted code must not break parsing (seen in a real eval run)
        self.assertEqual(run_evals.parse_verdict('uses `{}` here {"pass": true, "reason": "r"} and } after')[0], True)

    def test_transcript_ends_with_instruction_context(self):
        t = run_evals.transcript([{"role": "user", "content": "hi"}, {"role": "assistant", "content": "yo"}])
        self.assertIn("User: hi", t)
        self.assertIn("Assistant: yo", t)


if __name__ == "__main__":
    unittest.main()
