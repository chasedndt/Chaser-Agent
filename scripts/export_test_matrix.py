"""Export the exact public JSONL seed and contract values to readable Markdown."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        value = json.loads(line)
        if not isinstance(value, dict):
            raise ValueError(f"{path}:{line_number} is not a JSON object")
        rows.append(value)
    return rows


def _classification(path: Path) -> tuple[str, str, str]:
    if path.parent.name == "contract":
        return (
            "`chaser-agent contract-eval` / `chaser_agent.evals.contract_runner`",
            "EXECUTABLE CONTRACT SEED",
            "pending_operator_review",
        )
    if path.name == "source_card_summary_eval.jsonl":
        return (
            "`scripts/run_eval_smoke.py` / generic deterministic summary runner",
            "CONNECTED SMOKE SEED",
            "not_recorded",
        )
    if path.name == "visual_completion_eval.jsonl":
        return (
            "`chaser-agent visual-eval` / evidence-metadata evaluator; no pixel inspection",
            "CONNECTED METADATA-EVAL SEED",
            "not_recorded",
        )
    return (
        "generic `chaser_agent.evals.runner`; no task-specific evaluator",
        "GENERIC SMOKE SEED ONLY",
        "not_recorded",
    )


def _case_id(row: dict[str, Any]) -> str:
    return str(row.get("id", row.get("case_id", "unknown")))


def build_test_matrix(dataset_root: Path) -> tuple[str, dict[str, int]]:
    files = sorted(dataset_root.glob("golden/*.jsonl")) + sorted(dataset_root.glob("contract/*.jsonl"))
    sections: list[str] = []
    counts = {"files": len(files), "cases": 0, "golden_cases": 0, "contract_cases": 0}
    summary_rows: list[str] = []
    for path in files:
        rows = _read_jsonl(path)
        execution_path, maturity, default_review = _classification(path)
        counts["cases"] += len(rows)
        if path.parent.name == "contract":
            counts["contract_cases"] += len(rows)
        else:
            counts["golden_cases"] += len(rows)
        relative = path.relative_to(dataset_root.parent.parent).as_posix()
        summary_rows.append(
            f"| `{relative}` | {len(rows)} | {maturity} | {execution_path} |"
        )
        case_sections: list[str] = []
        for row in rows:
            review_status = str(row.get("provenance", {}).get("review_status", default_review))
            exact_values = json.dumps(row, ensure_ascii=False, indent=2, sort_keys=True)
            case_sections.append(
                "\n".join(
                    (
                        f"### `{_case_id(row)}`",
                        "",
                        f"- Task: `{row.get('task', 'visual_completion')}`",
                        f"- Maturity: **{maturity}**",
                        f"- Execution path: {execution_path}",
                        f"- Operator-review status: `{review_status}`",
                        "- Interpretation: values below are configured seed inputs, expectations, weights, or assertions; they are not achieved model scores.",
                        "",
                        "```json",
                        exact_values,
                        "```",
                    )
                )
            )
        sections.append(f"## `{relative}`\n\n" + "\n\n".join(case_sections))

    header = "\n".join(
        (
            "# Chaser Agent Current Test Matrix",
            "",
            "**Status:** GENERATED VISIBILITY ARTIFACT",
            "",
            "This file exposes the exact current public JSONL values and their real execution maturity. A JSONL row is a configured seed, not proof that a task-specific evaluator, model, or product workflow has passed it.",
            "",
            "## Inventory",
            "",
            f"- Dataset files: {counts['files']}",
            f"- Golden seed rows: {counts['golden_cases']}",
            f"- Layer 0 contract rows: {counts['contract_cases']}",
            f"- Total rows: {counts['cases']}",
            "",
            "| Dataset | Rows | Maturity | Current execution path |",
            "|---|---:|---|---|",
            *summary_rows,
            "",
            "## Maturity labels",
            "",
            "- **EXECUTABLE CONTRACT SEED:** exact artifact assertions run against the canonical deterministic builder.",
            "- **CONNECTED SMOKE SEED:** a generic deterministic runner executes the row, without domain-specific quality validation.",
            "- **CONNECTED METADATA-EVAL SEED:** deterministic evidence metadata is evaluated; pixels and live browser state are not inspected.",
            "- **GENERIC SMOKE SEED ONLY:** JSONL is valid and can enter the generic runner, but no task-specific evaluator exists.",
            "",
        )
    )
    return header + "\n\n".join(sections) + "\n", counts


def export_test_matrix(dataset_root: Path, output_path: Path) -> dict[str, int]:
    content, counts = build_test_matrix(dataset_root)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(content, encoding="utf-8")
    return counts


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Export Chaser Agent JSONL seeds and exact assertions to Markdown.")
    parser.add_argument("--datasets", type=Path, default=Path("evals/datasets"))
    parser.add_argument(
        "--out", type=Path, default=Path("docs/02_Evals/Chaser-Agent-Current-Test-Matrix.md")
    )
    args = parser.parse_args(argv)
    counts = export_test_matrix(args.datasets, args.out)
    print(json.dumps({"output": str(args.out), **counts}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
