from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, cast

from chaser_agent.chaseos_native import (
    build_chaseos_native_packet,
    build_chaseos_native_run_log,
    build_operator_handoff,
    validate_chaseos_workflow,
    write_chaseos_native_run,
)
from chaser_agent.evals.contract_runner import run_contract_jsonl_eval
from chaser_agent.evals.workflow_episode import read_workflow_episode_jsonl, run_workflow_trace_eval
from chaser_agent.run_artifacts import build_run_log, write_artifact_set
from chaser_agent.reviews.service import artifact_hashes, create_review_record
from chaser_agent.reviews.sqlite_store import SQLiteReviewStore
from chaser_agent.memory.service import reviewed_memories_from_review
from chaser_agent.memory.sqlite_store import SQLiteMemoryStore
from chaser_agent.knowledge.service import index_reviewed_run
from chaser_agent.knowledge.sqlite_store import SQLiteKnowledgeMapStore
from chaser_agent.source_card import (
    build_source_card_artifacts,
    make_run_id,
    source_input_from_file,
    utc_now_iso,
)
from chaser_agent.skillgate import (
    build_skill_gate_artifacts,
    make_skill_gate_run_id,
    utc_now_iso as skill_gate_utc_now_iso,
    write_skill_gate_run,
)
from chaser_agent.visual_completion import build_visual_eval_run


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def run_source_card_command(args: argparse.Namespace) -> int:
    input_path = Path(args.input)
    if not input_path.exists() or not input_path.is_file():
        print(f"error: input file not found: {input_path}", file=sys.stderr)
        return 2

    out_root = Path(args.out)
    created_at = utc_now_iso()
    run_id = make_run_id(input_path, created_at)
    run_folder = out_root / run_id

    source = source_input_from_file(input_path, privacy_class=args.privacy_class)
    try:
        artifacts = build_source_card_artifacts(source, input_path, run_id, created_at, profile_id=args.profile)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    planned_output_paths = [run_folder / filename for filename in [*artifacts.keys(), "run_log.json"]]
    command = "python -m chaser_agent.cli source-card --input {input} --out {out} --profile {profile}".format(
        input=input_path.as_posix(),
        out=out_root.as_posix(),
        profile=args.profile,
    )
    run_log = build_run_log(
        run_id=run_id,
        created_at=created_at,
        command=command,
        input_source_id=source.id,
        output_paths=planned_output_paths,
        repo_root=_repo_root(),
    )

    write_artifact_set(run_folder, artifacts, run_log)
    print(run_folder.as_posix())
    return 0


def run_skill_gate_command(args: argparse.Namespace) -> int:
    baseline_path = Path(args.baseline_skill)
    candidate_path = Path(args.candidate_skill)
    metrics_path = Path(args.metrics)
    for label, path in [
        ("baseline skill", baseline_path),
        ("candidate skill", candidate_path),
        ("metrics", metrics_path),
    ]:
        if not path.exists() or not path.is_file():
            print(f"error: {label} file not found: {path}", file=sys.stderr)
            return 2

    out_root = Path(args.out)
    created_at = skill_gate_utc_now_iso()
    run_id = make_skill_gate_run_id(baseline_path, created_at)
    run_folder = out_root / run_id
    try:
        artifacts, run_log = build_skill_gate_artifacts(
            baseline_path=baseline_path,
            candidate_path=candidate_path,
            metrics_path=metrics_path,
            run_id=run_id,
            created_at=created_at,
            repo_root=_repo_root(),
        )
    except (json.JSONDecodeError, ValueError) as exc:
        print(f"error: invalid skill-gate input: {exc}", file=sys.stderr)
        return 2
    write_skill_gate_run(run_folder, artifacts, run_log)
    print(run_folder.as_posix())
    return 0


def run_chaseos_native_source_card_command(args: argparse.Namespace) -> int:
    input_path = Path(args.input)
    if not input_path.exists() or not input_path.is_file():
        print(f"error: input file not found: {input_path}", file=sys.stderr)
        return 2
    try:
        validate_chaseos_workflow(args.workflow)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    out_root = Path(args.out)
    created_at = utc_now_iso()
    run_id = make_run_id(input_path, created_at).replace("source-card-", "chaseos-native-source-card-", 1)
    run_folder = out_root / run_id
    source = source_input_from_file(input_path, privacy_class=args.privacy_class)
    artifacts = build_source_card_artifacts(source, input_path, run_id, created_at)
    source_card_artifact = cast(dict[str, Any], artifacts["source_card.json"])
    human_review_artifact = cast(dict[str, Any], artifacts["human_review_packet.json"])
    packet = build_chaseos_native_packet(
        source_card=source_card_artifact,
        human_review_packet=human_review_artifact,
        run_id=run_id,
        created_at=created_at,
        runtime_lane=args.runtime_lane,
        workflow=args.workflow,
        output_dir=run_folder,
        repo_root=_repo_root(),
    )
    artifacts["chaseos_native_packet.json"] = packet
    operator_handoff = build_operator_handoff(packet)
    planned_output_paths = [
        run_folder / filename for filename in [*artifacts.keys(), "operator_handoff.md", "run_log.json"]
    ]
    command = "python -m chaser_agent.cli chaseos-native-source-card --input {input} --out {out} --workflow {workflow}".format(
        input=input_path.as_posix(),
        out=out_root.as_posix(),
        workflow=args.workflow,
    )
    run_log = build_chaseos_native_run_log(
        run_id=run_id,
        created_at=created_at,
        command=command,
        output_paths=planned_output_paths,
        repo_root=_repo_root(),
    )
    write_chaseos_native_run(run_folder, artifacts, operator_handoff, run_log)
    print(run_folder.as_posix())
    return 0


def run_visual_eval_command(args: argparse.Namespace) -> int:
    input_path = Path(args.input)
    if not input_path.exists() or not input_path.is_file():
        print(f"error: input file not found: {input_path}", file=sys.stderr)
        return 2
    try:
        run_folder = build_visual_eval_run(input_path=input_path, out_root=Path(args.out))
    except (json.JSONDecodeError, ValueError) as exc:
        print(f"error: invalid visual eval input: {exc}", file=sys.stderr)
        return 2
    print(run_folder.as_posix())
    return 0


def run_contract_eval_command(args: argparse.Namespace) -> int:
    input_path = Path(args.input)
    if not input_path.exists() or not input_path.is_file():
        print(f"error: input file not found: {input_path}", file=sys.stderr)
        return 2
    output_path = Path(args.out)
    try:
        results = run_contract_jsonl_eval(input_path, output_path, repo_root=_repo_root())
    except (json.JSONDecodeError, ValueError) as exc:
        print(f"error: invalid contract eval input: {exc}", file=sys.stderr)
        return 2
    print(output_path.as_posix())
    return 0 if all(result.passed for result in results) else 1


def run_workflow_episode_validate_command(args: argparse.Namespace) -> int:
    input_path = Path(args.input)
    if not input_path.exists() or not input_path.is_file():
        print(f"error: input file not found: {input_path}", file=sys.stderr)
        return 2
    try:
        episodes = read_workflow_episode_jsonl(input_path)
    except (json.JSONDecodeError, ValueError) as exc:
        print(f"error: invalid workflow episode input: {exc}", file=sys.stderr)
        return 2
    print(
        json.dumps(
            {
                "input": input_path.as_posix(),
                "episodes": len(episodes),
                "reviewed": sum(
                    episode["provenance"]["review_status"] == "reviewed" for episode in episodes
                ),
                "pending_operator_review": sum(
                    episode["provenance"]["review_status"] == "pending_operator_review"
                    for episode in episodes
                ),
            },
            sort_keys=True,
        )
    )
    return 0


def run_workflow_trace_eval_command(args: argparse.Namespace) -> int:
    episode_path = Path(args.episodes)
    trace_path = Path(args.traces)
    for label, path in (("episode", episode_path), ("trace", trace_path)):
        if not path.exists() or not path.is_file():
            print(f"error: {label} file not found: {path}", file=sys.stderr)
            return 2
    output_path = Path(args.out)
    try:
        results = run_workflow_trace_eval(episode_path, trace_path, output_path)
    except (json.JSONDecodeError, ValueError) as exc:
        print(f"error: invalid workflow trace eval input: {exc}", file=sys.stderr)
        return 2
    print(output_path.as_posix())
    return 0 if all(result.passed for result in results) else 1


def run_review_command(args: argparse.Namespace) -> int:
    run_folder = Path(args.run_folder)
    if not run_folder.is_dir():
        print(f"error: run folder not found: {run_folder}", file=sys.stderr)
        return 2
    before_hashes = artifact_hashes(run_folder)
    try:
        review = create_review_record(
            run_folder,
            reviewer_id=args.reviewer_id,
            scores=(
                args.source_fidelity_score,
                args.inference_separation_score,
                args.uncertainty_handling_score,
                args.action_usefulness_score,
                args.memory_safety_score,
            ),
            decision=args.decision,
            reviewer_notes=args.reviewer_notes,
            corrected_claims=tuple(args.corrected_claim),
            corrected_inferences=tuple(args.corrected_inference),
            accepted_action_ids=tuple(args.accept_action),
            rejected_action_ids=tuple(args.reject_action),
            accepted_memory_ids=tuple(args.accept_memory),
            rejected_memory_ids=tuple(args.reject_memory),
        )
        store = SQLiteReviewStore(args.database)
        store.add(review)
        memory_records = reviewed_memories_from_review(SQLiteMemoryStore(args.database), run_folder, review)
        graph_counts = index_reviewed_run(SQLiteKnowledgeMapStore(args.database), run_folder, review, memory_records)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    if before_hashes != artifact_hashes(run_folder):
        print("error: original run artifacts changed during review", file=sys.stderr)
        return 3
    print(
        json.dumps(
            {
                "review_id": review.review_id,
                "run_id": review.run_id,
                "decision": review.decision,
                "total_score": review.total_score,
                "database_path": str(store.database_path),
                "original_artifacts_unchanged": True,
                "memory_promotion": "not_performed",
                "memory_records_created": [record.memory_id for record in memory_records],
                "knowledge_map_entries": graph_counts,
            },
            sort_keys=True,
        )
    )
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="chaser-agent", description="Chaser Agent local deterministic harness CLI")
    subparsers = parser.add_subparsers(dest="command")

    source_card = subparsers.add_parser(
        "source-card",
        help="Build deterministic V0 source-card review artifacts from a local safe text/markdown input.",
    )
    source_card.add_argument("--input", required=True, help="Local safe text/markdown source file.")
    source_card.add_argument("--out", required=True, help="Output root directory for unique run folders.")
    source_card.add_argument(
        "--privacy-class",
        default="public_toy",
        help="Privacy class to stamp on artifacts; defaults to public_toy for the Phase 1 toy harness.",
    )
    source_card.add_argument(
        "--profile",
        default="general_source_review",
        help="Workflow profile ID; defaults to general_source_review.",
    )
    source_card.set_defaults(func=run_source_card_command)

    skill_gate = subparsers.add_parser(
        "skill-gate",
        help="Build a review-only SkillOpt-style gate packet for a candidate SKILL.md patch.",
    )
    skill_gate.add_argument("--baseline-skill", required=True, help="Existing SKILL.md file; never modified by this command.")
    skill_gate.add_argument("--candidate-skill", required=True, help="Candidate SKILL.md file to evaluate as a review-only patch.")
    skill_gate.add_argument("--metrics", required=True, help="JSON metrics with baseline_score, candidate_score, held_out_split_id, edit_count, verifier.")
    skill_gate.add_argument("--out", required=True, help="Output root directory for unique review packet folders.")
    skill_gate.set_defaults(func=run_skill_gate_command)

    chaseos_native = subparsers.add_parser(
        "chaseos-native-source-card",
        help="Build Source Card artifacts plus a ChaseOS-native control-plane handoff packet.",
    )
    chaseos_native.add_argument("--input", required=True, help="Local safe text/markdown source file.")
    chaseos_native.add_argument("--out", required=True, help="Output root directory for unique run folders.")
    chaseos_native.add_argument(
        "--workflow",
        default="hermes_review_execute",
        help="Approved ChaseOS workflow label to stamp on the packet.",
    )
    chaseos_native.add_argument(
        "--runtime-lane",
        default="chaser-agent",
        help="Runtime/product lane label to stamp on the packet.",
    )
    chaseos_native.add_argument(
        "--privacy-class",
        default="public_toy",
        help="Privacy class to stamp on artifacts; defaults to public_toy.",
    )
    chaseos_native.set_defaults(func=run_chaseos_native_source_card_command)

    visual_eval = subparsers.add_parser(
        "visual-eval",
        help="Run deterministic review-only visual/computer-use completion evals over JSONL evidence cases.",
    )
    visual_eval.add_argument("--input", required=True, help="JSONL file of visual completion evidence cases.")
    visual_eval.add_argument("--out", required=True, help="Output root directory for unique visual eval run folders.")
    visual_eval.set_defaults(func=run_visual_eval_command)

    contract_eval = subparsers.add_parser(
        "contract-eval",
        help="Run deterministic Layer 0 artifact assertions over public-safe contract cases.",
    )
    contract_eval.add_argument("--input", required=True, help="JSONL file of Layer 0 contract cases.")
    contract_eval.add_argument("--out", required=True, help="JSONL destination for assertion-level eval results.")
    contract_eval.set_defaults(func=run_contract_eval_command)

    workflow_episode_validate = subparsers.add_parser(
        "workflow-episode-validate",
        help="Validate case-study workflow episodes without treating unreviewed rows as golden data.",
    )
    workflow_episode_validate.add_argument("--input", required=True, help="Workflow episode JSONL file.")
    workflow_episode_validate.set_defaults(func=run_workflow_episode_validate_command)

    workflow_trace_eval = subparsers.add_parser(
        "workflow-trace-eval",
        help="Score workflow traces for ordering, evidence, authority, artifacts, proof, and handoff structure.",
    )
    workflow_trace_eval.add_argument("--episodes", required=True, help="Validated workflow episode JSONL file.")
    workflow_trace_eval.add_argument("--traces", required=True, help="Workflow trace JSONL file to score.")
    workflow_trace_eval.add_argument("--out", required=True, help="JSONL destination for deterministic results.")
    workflow_trace_eval.set_defaults(func=run_workflow_trace_eval_command)

    review = subparsers.add_parser(
        "review",
        help="Persist an immutable human review for an existing source-card run without changing its artifacts.",
    )
    review.add_argument("run_folder", help="Existing source-card run folder.")
    review.add_argument("--database", help="SQLite database path; defaults to ~/.chaser-agent/chaser-agent.db.")
    review.add_argument("--reviewer-id", required=True, help="Stable local identifier for the human reviewer.")
    for option in (
        "source-fidelity-score",
        "inference-separation-score",
        "uncertainty-handling-score",
        "action-usefulness-score",
        "memory-safety-score",
    ):
        review.add_argument(f"--{option}", required=True, type=int, choices=range(4))
    review.add_argument("--decision", required=True, choices=("pass", "needs_revision", "fail"))
    review.add_argument("--reviewer-notes", default="")
    review.add_argument("--corrected-claim", action="append", default=[])
    review.add_argument("--corrected-inference", action="append", default=[])
    review.add_argument("--accept-action", action="append", default=[])
    review.add_argument("--reject-action", action="append", default=[])
    review.add_argument("--accept-memory", action="append", default=[])
    review.add_argument("--reject-memory", action="append", default=[])
    review.set_defaults(func=run_review_command)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if not hasattr(args, "func"):
        parser.print_help()
        return 0
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
