from __future__ import annotations
import json
from pathlib import Path
from chaser_agent.schemas import EvalCase, EvalResult, SourceInput
from chaser_agent.summary.source_card import build_source_card
from chaser_agent.evals.rubric import score_required_includes

def read_jsonl(path: str | Path) -> list[dict]:
    rows=[]
    with Path(path).open("r", encoding="utf-8") as f:
        for line_no,line in enumerate(f,1):
            if not line.strip():
                continue
            obj=json.loads(line)
            if not isinstance(obj, dict):
                raise ValueError(f"line {line_no} is not an object")
            for key in ("id", "task", "input", "expected"):
                if key not in obj:
                    raise ValueError(f"line {line_no} missing required field {key}")
            rows.append(obj)
    return rows

def run_case(row: dict) -> EvalResult:
    case=EvalCase(id=row["id"], task=row["task"], input=row["input"], expected=row.get("expected", {}), rubric=row.get("rubric", {}))
    source=SourceInput(id=case.id, title=case.input.get("title", case.id), text=case.input.get("text", ""))
    card=build_source_card(source)
    output_text=" ".join([card.summary]+[c.text for c in card.claims])
    passed, score=score_required_includes(output_text, list(case.expected.get("must_include", [])))
    if case.expected.get("requires_uncertainty_label") and not card.uncertainty_labels:
        passed=False
        score=min(score,0.5)
    return EvalResult(id=case.id, task=case.task, passed=passed, score=score, notes="deterministic placeholder evaluation", output={"summary": card.summary, "uncertainty_labels": card.uncertainty_labels})

def run_jsonl_eval(input_path: str | Path, output_path: str | Path | None = None) -> list[EvalResult]:
    results=[run_case(row) for row in read_jsonl(input_path)]
    if output_path:
        out=Path(output_path)
        out.parent.mkdir(parents=True, exist_ok=True)
        with out.open("w", encoding="utf-8") as f:
            for result in results:
                f.write(json.dumps(result.__dict__, ensure_ascii=False) + "\n")
    return results
