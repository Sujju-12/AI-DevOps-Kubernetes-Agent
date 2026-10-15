"""Run deterministic evaluation cases against the local rule-based analyzer.

This intentionally avoids paid/network LLM calls. It measures only the known
local correlation cases in cases.jsonl; it is not a general LLM benchmark.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "backend"))

from app.ai.analyzer import correlate_locally  # noqa: E402


def main() -> int:
    cases_path = Path(__file__).with_name("cases.jsonl")
    total = 0
    passed = 0

    for line in cases_path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        case = json.loads(line)
        total += 1
        diagnosis = correlate_locally(case["input"])
        text = f"{diagnosis.root_cause} {diagnosis.explanation}".lower()
        missing = [word for word in case["expected_keywords"] if word.lower() not in text]
        ok = not missing
        passed += int(ok)
        print(f"{'PASS' if ok else 'FAIL'} {case['id']}: {diagnosis.root_cause}")
        if missing:
            print(f"  Missing expected terms: {', '.join(missing)}")

    print(f"\nResult: {passed}/{total} cases passed")
    return 0 if total > 0 and passed == total else 1


if __name__ == "__main__":
    raise SystemExit(main())
