"""Evaluate a public 100-image face sample without changing production code."""
from __future__ import annotations

import json
from pathlib import Path


def main() -> int:
    root = Path("evaluation-data")
    output = Path("artifacts") / "evaluation.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    result_path = root / "results.json"
    result = {"source": "LFW", "total": 100, "tuning": 30, "final": 70, "status": "not-run"}
    if result_path.exists():
        result.update(json.loads(result_path.read_text(encoding="utf-8")))
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
