#!/usr/bin/env python3
"""Re-grade saved replies with a different judge model and report agreement with the original judge.
Answers "isn't Sonnet grading Sonnet biased?" with data instead of an argument.

    python3 evals/rejudge.py evals/results-heldout.json --judge-model opus
"""
import argparse
import json
import os
import sys
from concurrent.futures import ThreadPoolExecutor

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import run_evals  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("results")
    ap.add_argument("--cases", default=None, help="cases file (default: matches the results file)")
    ap.add_argument("--judge-model", default="opus")
    ap.add_argument("--jobs", type=int, default=6)
    a = ap.parse_args()
    cases_path = a.cases or os.path.join(os.path.dirname(a.results),
                                         "heldout.jsonl" if "heldout" in a.results else "cases.jsonl")
    cases = {c["id"]: c for c in run_evals.load_cases(cases_path)}
    results = json.load(open(a.results, encoding="utf-8"))

    def regrade(r):
        ok, reasons, cost = run_evals.check(cases[r["id"]], r["reply"], a.judge_model)
        return dict(r, repass=ok, rereasons=reasons, recost=cost)

    with ThreadPoolExecutor(a.jobs) as pool:
        out = list(pool.map(regrade, results))
    agree = sum(r["pass"] == r["repass"] for r in out)
    print("Judges agree on %d/%d replies (%.0f%%)" % (agree, len(out), 100 * agree / len(out)))
    for mode in ("off", "on"):
        rs = [r for r in out if r["mode"] == mode]
        if rs:
            print("  skill %-3s original judge %2d/%d   %s judge %2d/%d" % (
                mode, sum(r["pass"] for r in rs), len(rs), a.judge_model, sum(r["repass"] for r in rs), len(rs)))
    for r in out:
        if r["pass"] != r["repass"]:
            print("  disagree [%s] %s: original=%s, %s=%s %s" % (r["mode"], r["id"], r["pass"], a.judge_model,
                                                                r["repass"], "; ".join(r["rereasons"])[:160]))
    print("cost: $%.2f" % sum(r["recost"] for r in out))
    with open(a.results.replace(".json", "-rejudged-%s.json" % a.judge_model), "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2)


if __name__ == "__main__":
    main()
