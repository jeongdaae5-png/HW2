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
    contiguous = [row.get("id") for row in rows] == list(range(1, len(rows) + 1))
    window_start = rows[0].get("start", "unobserved") if rows else "unobserved"
    window_end = rows[-1].get("end", "unobserved") if rows else "unobserved"
    success = "SUCCESS" if fail == 0 and rows else "FAILURE"
    by_stage = {stage: [row for row in rows if str(row.get("stage", "")).lower() == stage.lower()] for stage in ("Before", "During", "After")}
    stage_lines = []
    for stage in ("Before", "During", "After"):
        group = by_stage[stage]
        stage_ok = sum(row.get("status") == 200 and row.get("analysis_ok") for row in group)
        representative = group[0] if group else {}
        stage_lines.append(f"| {stage} | {stage_ok}/{len(group)} | #{representative.get('id', 'unobserved')} | {representative.get('start', 'unobserved')} | {representative.get('status', 'unobserved')} | {representative.get('analysis_ok', 'unobserved')} | {representative.get('version', 'unobserved')} | {representative.get('result', 'unobserved')} |")
    lines = [
        f"Result: {success} | Stable URL: http://127.0.0.1:8000 | Window (UTC): {window_start} to {window_end}",
        f"API requests: {len(rows)} total, {ok} successful, {fail} failed, request IDs contiguous: {str(contiguous)}", "",
        "## Deployment verification", "",
        "| Stage | Requests (ok/total) | Representative request | UTC start | HTTP | Analysis | Response revision | Result |",
        "|---|---:|---:|---|---:|---|---|---|",
        *stage_lines, "",
        "## Model evaluation", "",
        "| Dataset | Tune | Final | Prediction consistency | Face detection before | Face detection after | Median RGB shift | Status |",
        "|---|---:|---:|---:|---:|---:|---:|---|",
        f"| {evaluation['source']} | {evaluation['tuning']} | {evaluation['final']} | {metrics.get('prediction_consistency', 'unavailable')} | {metrics.get('face_detection_rate_before', 'unavailable')} | {metrics.get('face_detection_rate_after', 'unavailable')} | {metrics.get('median_rgb_shift', 'unavailable')} | {evaluation['status']} |",
    ]
    target = os.environ["GITHUB_STEP_SUMMARY"]
    Path(target).open("a", encoding="utf-8", newline="\n").write("\n".join(lines) + "\n")


if __name__ == "__main__":
    main()
