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
from chaser_agent.run_artifacts import build_run_log, write_artifact_set
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
    artifacts = build_source_card_artifacts(source, input_path, run_id, created_at)
    planned_output_paths = [run_folder / filename for filename in [*artifacts.keys(), "run_log.json"]]
    command = "python -m chaser_agent.cli source-card --input {input} --out {out}".format(
        input=input_path.as_posix(),
        out=out_root.as_posix(),
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


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="chaser-agent", description="Chaser agent local deterministic harness CLI")
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
