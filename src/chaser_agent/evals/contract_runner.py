from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from chaser_agent.run_artifacts import build_run_log
from chaser_agent.schemas import SourceInput
from chaser_agent.source_card import build_source_card_artifacts


REQUIRED_CASE_FIELDS = (
    "id",
    "task",
    "layer0_clause",
    "input",
    "expected_behavior",
    "forbidden_behavior",
    "privacy",
    "human_review_required",
    "failure_modes",
    "provenance",
)

AGENT_AUTHORED_TEXT_PATHS = (
    "source_card.json:chaser_agent_inferences[*].inference_text",
    "source_card.json:uncertainty_labels[*].explanation",
    "source_card.json:action_candidates[*].action_text",
    "source_card.json:memory_candidates[*].candidate_text",
    "human_review_packet.json:reviewer_notes",
    "run_log.json:blocked_actions[*]",
    "run_log.json:notes",
)


@dataclass
class ContractEvalResult:
    id: str
    task: str
    passed: bool
    score: float
    notes: str
    output: dict[str, Any] = field(default_factory=dict)
    layer0_clause: str = ""
    assertion_details: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def read_contract_jsonl(path: str | Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with Path(path).open("r", encoding="utf-8") as handle:
        for line_no, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            row = json.loads(line)
            if not isinstance(row, dict):
                raise ValueError(f"line {line_no} is not an object")
            missing = [field for field in REQUIRED_CASE_FIELDS if field not in row]
            if missing:
                raise ValueError(f"line {line_no} missing required field(s): {', '.join(missing)}")
            if not isinstance(row["input"], dict):
                raise ValueError(f"line {line_no} input must be an object")
            for section in ("expected_behavior", "forbidden_behavior"):
                if not isinstance(row[section], dict):
                    raise ValueError(f"line {line_no} {section} must be an object")
            rows.append(row)
    return rows


def _resolve_path(artifacts: dict[str, Any], path: str) -> list[Any]:
    if ":" not in path:
        raise ValueError(f"artifact path must use '<artifact>:<field>': {path}")
    artifact_name, field_path = path.split(":", 1)
    if artifact_name not in artifacts:
        raise ValueError(f"artifact not found: {artifact_name}")

    values: list[Any] = [artifacts[artifact_name]]
    if not field_path:
        return values

    for segment in field_path.split("."):
        wildcard = segment.endswith("[*]")
        key = segment[:-3] if wildcard else segment
        next_values: list[Any] = []
        for value in values:
            if not isinstance(value, dict) or key not in value:
                raise ValueError(f"path segment not found: {segment} in {path}")
            child = value[key]
            if wildcard:
                if not isinstance(child, list):
                    raise ValueError(f"wildcard segment is not a list: {segment} in {path}")
                next_values.extend(child)
            else:
                next_values.append(child)
        values = next_values
    return values


def _flatten(values: list[Any]) -> list[Any]:
    flattened: list[Any] = []
    for value in values:
        if isinstance(value, list):
            flattened.extend(value)
        else:
            flattened.append(value)
    return flattened


def _evaluate_artifact_assertion(
    assertion: dict[str, Any],
    artifacts: dict[str, Any],
    input_text: str,
) -> tuple[bool, Any, str]:
    path = assertion.get("path")
    if not isinstance(path, str) or not path:
        return False, None, "assertion is missing a non-empty path"

    try:
        values = _resolve_path(artifacts, path)
    except ValueError as exc:
        return False, None, str(exc)

    if "equals" in assertion:
        expected = assertion["equals"]
        passed = bool(values) and all(value == expected for value in values)
        return passed, values, f"all resolved values must equal {expected!r}"

    if "never_equals" in assertion:
        forbidden = assertion["never_equals"]
        passed = bool(values) and all(value != forbidden for value in values)
        return passed, values, f"no resolved value may equal {forbidden!r}"

    if "min_length" in assertion:
        minimum = assertion["min_length"]
        if not isinstance(minimum, int) or minimum < 0:
            return False, values, "min_length must be a non-negative integer"
        lengths = [len(value) if hasattr(value, "__len__") else None for value in values]
        passed = bool(lengths) and all(length is not None and length >= minimum for length in lengths)
        return passed, lengths, f"all resolved values must have length >= {minimum}"

    if "references_resolve" in assertion:
        target_path = assertion["references_resolve"]
        if not isinstance(target_path, str) or not target_path:
            return False, values, "references_resolve must name a target artifact path"
        try:
            target_values = set(_flatten(_resolve_path(artifacts, target_path)))
        except ValueError as exc:
            return False, values, str(exc)
        references = _flatten(values)
        missing = [reference for reference in references if reference not in target_values]
        return not missing and bool(references), {"references": references, "missing": missing}, (
            f"all references must resolve in {target_path}"
        )

    if assertion.get("all_text_in_input") is True:
        snippets = _flatten(values)
        missing_text = [snippet for snippet in snippets if not isinstance(snippet, str) or snippet not in input_text]
        return not missing_text and bool(snippets), {"checked": snippets, "missing": missing_text}, (
            "every resolved text value must occur verbatim in input.text"
        )

    if "never_contains_any" in assertion:
        forbidden_phrases = assertion["never_contains_any"]
        if not isinstance(forbidden_phrases, list) or not all(isinstance(item, str) for item in forbidden_phrases):
            return False, values, "never_contains_any must be a list of strings"
        lowered_values = [str(value).lower() for value in _flatten(values)]
        hits = sorted(
            {
                phrase
                for phrase in forbidden_phrases
                if any(phrase.lower() in value for value in lowered_values)
            }
        )
        return not hits, {"forbidden_hits": hits}, "resolved text must not contain a forbidden phrase"

    return False, values, "assertion has no supported operator"


def _agent_authored_output_text(artifacts: dict[str, Any]) -> str:
    values: list[str] = []
    for path in AGENT_AUTHORED_TEXT_PATHS:
        try:
            resolved = _flatten(_resolve_path(artifacts, path))
        except ValueError:
            continue
        values.extend(str(value) for value in resolved)
    return " ".join(values)


def _build_case_artifacts(row: dict[str, Any], repo_root: Path | None) -> dict[str, Any]:
    case_input = row["input"]
    case_id = str(row["id"])
    privacy_class = str(case_input.get("privacy_class", row["privacy"]))
    source = SourceInput(
        id=case_id,
        title=str(case_input.get("title", case_id)),
        text=str(case_input.get("text", "")),
        source_type=str(case_input.get("source_type", "note")),
        source_origin=str(case_input.get("source_origin", "contract_eval_public_toy")),
        privacy_class=privacy_class,
    )
    run_id = f"contract-eval-{case_id}"
    created_at = "1970-01-01T00:00:00Z"
    synthetic_input_path = Path(f"{case_id}.md")
    artifacts = build_source_card_artifacts(source, synthetic_input_path, run_id, created_at)
    planned_paths = [Path("contract-eval") / case_id / filename for filename in [*artifacts, "run_log.json"]]
    artifacts["run_log.json"] = build_run_log(
        run_id=run_id,
        created_at=created_at,
        command=f"contract-eval:{case_id}",
        input_source_id=source.id,
        output_paths=planned_paths,
        repo_root=repo_root,
    )
    return artifacts


def run_contract_case(row: dict[str, Any], repo_root: Path | None = None) -> ContractEvalResult:
    artifacts = _build_case_artifacts(row, repo_root)
    input_text = str(row["input"].get("text", ""))
    details: list[dict[str, Any]] = []

    for section_name in ("expected_behavior", "forbidden_behavior"):
        assertions = row[section_name].get("artifact_assertions", [])
        if not isinstance(assertions, list):
            raise ValueError(f"{row['id']} {section_name}.artifact_assertions must be a list")
        for assertion in assertions:
            if not isinstance(assertion, dict):
                raise ValueError(f"{row['id']} {section_name} contains a non-object assertion")
            passed, observed, requirement = _evaluate_artifact_assertion(assertion, artifacts, input_text)
            details.append(
                {
                    "section": section_name,
                    "assertion": assertion,
                    "passed": passed,
                    "observed": observed,
                    "requirement": requirement,
                }
            )

    forbidden_phrases = row["forbidden_behavior"].get("output_text_never_contains", [])
    if not isinstance(forbidden_phrases, list) or not all(isinstance(item, str) for item in forbidden_phrases):
        raise ValueError(f"{row['id']} forbidden_behavior.output_text_never_contains must be a list of strings")
    if forbidden_phrases:
        agent_output = _agent_authored_output_text(artifacts).lower()
        hits = sorted({phrase for phrase in forbidden_phrases if phrase.lower() in agent_output})
        details.append(
            {
                "section": "forbidden_behavior",
                "assertion": {"output_text_never_contains": forbidden_phrases},
                "passed": not hits,
                "observed": {"forbidden_hits": hits},
                "requirement": "agent-authored text must not contain a forbidden phrase",
            }
        )

    if not details:
        details.append(
            {
                "section": "case_schema",
                "assertion": {},
                "passed": False,
                "observed": None,
                "requirement": "contract cases must contain at least one executable assertion",
            }
        )

    passed_count = sum(1 for detail in details if detail["passed"])
    failed_details = [detail for detail in details if not detail["passed"]]
    passed = not failed_details
    score = passed_count / len(details)
    if passed:
        notes = f"Layer 0 clause {row['layer0_clause']} passed {passed_count}/{len(details)} assertions"
    else:
        first_failure = failed_details[0]
        notes = (
            f"Layer 0 clause {row['layer0_clause']} failed assertion "
            f"{json.dumps(first_failure['assertion'], sort_keys=True)}; "
            f"observed={first_failure['observed']!r}"
        )

    return ContractEvalResult(
        id=str(row["id"]),
        task=str(row["task"]),
        passed=passed,
        score=score,
        notes=notes,
        output={
            "artifact_names": sorted(artifacts),
            "assertions_passed": passed_count,
            "assertions_total": len(details),
        },
        layer0_clause=str(row["layer0_clause"]),
        assertion_details=details,
    )


def run_contract_jsonl_eval(
    input_path: str | Path,
    output_path: str | Path | None = None,
    repo_root: Path | None = None,
) -> list[ContractEvalResult]:
    results = [run_contract_case(row, repo_root=repo_root) for row in read_contract_jsonl(input_path)]
    if output_path is not None:
        destination = Path(output_path)
        destination.parent.mkdir(parents=True, exist_ok=True)
        with destination.open("w", encoding="utf-8") as handle:
            for result in results:
                handle.write(json.dumps(result.to_dict(), ensure_ascii=False, sort_keys=True) + "\n")
    return results
