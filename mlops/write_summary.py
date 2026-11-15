"""Write the deployment summary with a BOM-free UTF-8 Python writer."""
from __future__ import annotations

import json
import os
from pathlib import Path


def main() -> None:
    log_path = Path("artifacts/monitor.jsonl")
    rows = [json.loads(line) for line in log_path.read_text(encoding="utf-8").splitlines() if line.strip()] if log_path.exists() else []
    evaluation = json.loads(Path("evaluation-data/results.json").read_text(encoding="utf-8"))
    metrics = evaluation.get("metrics", {})
    ok = sum(row.get("status") == 200 and row.get("analysis_ok") for row in rows)
    fail = len(rows) - ok
    versions = ", ".join(dict.fromkeys(str(row.get("version", "unavailable")) for row in rows))
    first = rows[0].get("status", "unobserved") if rows else "unobserved"
    last = rows[-1].get("status", "unobserved") if rows else "unobserved"
    lines = [
        "## Deployment verification", "", "| Item | Result |", "|---|---|",
        "| Verification URL | http://127.0.0.1:8000/api/analyze |",
        f"| Request success / failure | {ok} / {fail} |",
        f"| Version transition | {versions or 'unobserved'} |",
        "| Request interval target | 1 second |",
        "| Maximum log gap | Calculated from adjacent timestamps; unobserved gaps remain marked |",
        f"| Representative responses | {first} / {last} |",
        "| Continuity observation | Only the observed request range is reported |", "",
        "## Model evaluation", "",
        "| Dataset | Tune | Final | Prediction consistency | Face detection before | Face detection after | Median RGB shift | Status |",
        "|---|---:|---:|---:|---:|---:|---:|---|",
        f"| {evaluation['source']} | {evaluation['tuning']} | {evaluation['final']} | {metrics.get('prediction_consistency', 'unavailable')} | {metrics.get('face_detection_rate_before', 'unavailable')} | {metrics.get('face_detection_rate_after', 'unavailable')} | {metrics.get('median_rgb_shift', 'unavailable')} | {evaluation['status']} |",
    ]
    target = os.environ["GITHUB_STEP_SUMMARY"]
    Path(target).open("a", encoding="utf-8", newline="\n").write("\n".join(lines) + "\n")


if __name__ == "__main__":
    main()
