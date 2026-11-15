"""Evaluate a labeled 100-image split without changing the production model.

The manifest must contain exactly 100 records: 30 tune and 70 final.  Labels
are required for accuracy; unlabeled public face datasets are reported as
unavailable rather than being treated as ground truth.
"""
from __future__ import annotations

import csv
import json
from pathlib import Path


def main() -> int:
    root = Path("evaluation-data")
    manifest = root / "manifest.csv"
    output = Path("artifacts") / "evaluation.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    result = {"source": "not configured", "total": 0, "tuning": 0, "final": 0, "accuracy": None, "consistency": None, "status": "unavailable"}
    if manifest.exists():
        with manifest.open("r", encoding="utf-8", newline="") as handle:
            rows = list(csv.DictReader(handle))
        result["total"] = len(rows)
        result["tuning"] = sum(row.get("split") == "tuning" for row in rows)
        result["final"] = sum(row.get("split") == "final" for row in rows)
        result["source"] = rows[0].get("source", "unknown") if rows else "unknown"
        if len(rows) == 100 and result["tuning"] == 30 and result["final"] == 70 and all(row.get("label") for row in rows):
            result["status"] = "ready-for-scored-run"
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
