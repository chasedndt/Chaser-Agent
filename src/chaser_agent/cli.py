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


def run_serve_command(args: argparse.Namespace) -> int:
    from chaser_agent.local_http import create_server, load_or_create_token

    requested_data_dir = Path(args.data_dir)
    if requested_data_dir.is_symlink():
        print("error: HTTP data directory must not be a symlink", file=sys.stderr)
        return 2
    data_dir = requested_data_dir.resolve()
    if data_dir.is_relative_to(_repo_root().resolve()):
        print("error: HTTP data directory must be outside the source repository", file=sys.stderr)
        return 2
    if not 1 <= args.port <= 65535:
        print("error: port must be between 1 and 65535", file=sys.stderr)
        return 2
    try:
        token, token_path = load_or_create_token(data_dir)
        server = create_server(
            data_dir=data_dir,
            token=token,
            port=args.port,
            allowed_origins=tuple(args.allowed_origin),
            voice_library=Path(args.voice_library) if args.voice_library else None,
        )
    except (OSError, ValueError) as exc:
        print(f"error: local HTTP startup failed: {exc}", file=sys.stderr)
        return 2
    print(f"Chaser Agent local API: http://127.0.0.1:{server.server_port}/v1/health")
    print(f"Bearer token file: {token_path}")
    print("Review-only. No provider, tool, computer-use, or memory-promotion authority.")
    print("Local Pocket Alba voice: configured" if server.voice else "Local Pocket Alba voice: not configured")
    try:
        server.serve_forever(poll_interval=0.25)
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


def run_hud_command(args: argparse.Namespace) -> int:
    from chaser_agent.hud_window import HudWindow

    if not args.preview and not args.data_dir:
        print("error: --data-dir is required outside synthetic preview mode", file=sys.stderr)
        return 2
    if not 1 <= args.port <= 65535:
        print("error: port must be between 1 and 65535", file=sys.stderr)
        return 2
    requested_data_dir = Path(args.data_dir) if args.data_dir else None
    if requested_data_dir is not None and requested_data_dir.is_symlink():
        print("error: HUD data directory must not be a symlink", file=sys.stderr)
        return 2
    token_file = requested_data_dir / "control-token" if requested_data_dir else None
    if token_file is not None and (token_file.is_symlink() or not token_file.is_file()):
        print("error: local bearer-token file is missing or is a symlink", file=sys.stderr)
        return 2
    window = HudWindow(port=args.port, token_file=token_file, preview=args.preview)
    print("Synthetic HUD preview; no executor connected." if args.preview else "HUD waiting for a computer-use session.")
    window.run()
    return 0


def run_voice_mode_command(args: argparse.Namespace) -> int:
    from chaser_agent.local_stt import OfflineTranscriber, read_pcm_wav, record_once

    if not args.sample_wav and not 0.5 <= args.seconds <= 12:
        print("error: microphone capture must be 0.5–12 seconds", file=sys.stderr)
        return 2
    if args.speak_ack and not args.data_dir:
        print("error: --speak-ack requires --data-dir for the running local voice service", file=sys.stderr)
        return 2

    def optional_ack(result: dict[str, object]) -> None:
        if not args.speak_ack or result["status"] != "draft_unverified":
            return
        from chaser_agent.voice_ack import speak_ack

        try:
            voice_id = speak_ack(data_dir=Path(args.data_dir), port=args.port)
            print(f"Fixed local acknowledgement played ({voice_id}); it was not an agent answer.")
        except (OSError, ValueError, RuntimeError, TimeoutError) as exc:
            print(f"Voice acknowledgement unavailable: {exc}", file=sys.stderr)

    try:
        transcriber = OfflineTranscriber(Path(args.model_dir))
    except (OSError, ValueError, ImportError, RuntimeError) as exc:
        print(f"error: offline speech input unavailable: {exc}", file=sys.stderr)
        return 2
    print("Offline voice input ready. Transcripts are drafts; no agent action or provider call occurs.")
    if args.sample_wav:
        try:
            result = transcriber.transcribe(read_pcm_wav(Path(args.sample_wav)))
        except (OSError, ValueError, RuntimeError) as exc:
            print(f"error: test WAV could not be transcribed: {exc}", file=sys.stderr)
            return 2
        print(json.dumps(result, ensure_ascii=False))
        optional_ack(result)
        return 0
    while True:
        try:
            choice = input("Press Enter to record one take, or q then Enter to quit: ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            print("\nVoice input closed; microphone inactive.")
            return 0
        if choice == "q":
            print("Voice input closed; microphone inactive.")
            return 0
        if choice:
            print("Unknown choice; microphone inactive.")
            continue
        print(f"MICROPHONE ACTIVE for up to {args.seconds:g} seconds. Ctrl+C cancels this take.", flush=True)
        try:
            pcm = record_once(args.seconds, device=args.device)
        except KeyboardInterrupt:
            print("\nMICROPHONE OFF. Take discarded.")
            continue
        except Exception as exc:
            print(f"MICROPHONE OFF. Capture discarded ({type(exc).__name__}).", file=sys.stderr)
            continue
        print("MICROPHONE OFF. Transcribing locally...", flush=True)
        try:
            result = transcriber.transcribe(pcm)
        except Exception as exc:
            print(f"error: transcription failed ({type(exc).__name__})", file=sys.stderr)
            continue
        print(json.dumps(result, ensure_ascii=False))
        print("Review the draft. No tool, computer-use or memory action was dispatched.")
        optional_ack(result)


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

    serve = subparsers.add_parser(
        "serve",
        help="Run the deterministic review-only HTTP API on 127.0.0.1 (default port 8765).",
    )
    serve.add_argument("--data-dir", required=True, help="Explicit local runtime directory outside the repository.")
    serve.add_argument("--port", type=int, default=8765, help="Fixed loopback port; fail if occupied (default 8765).")
    serve.add_argument(
        "--allowed-origin",
        action="append",
        default=[],
        help="Optional exact http://127.0.0.1:<port> browser origin for a future local client.",
    )
    serve.add_argument(
        "--voice-library",
        help="Optional operator-approved local Pocket Alba speech library; no model download or provider call.",
    )
    serve.set_defaults(func=run_serve_command)

    hud = subparsers.add_parser(
        "hud",
        help="Open the local desktop HUD; stays hidden until a computer-use session is observed.",
    )
    hud.add_argument("--data-dir", help="Same local runtime directory used by the serve command.")
    hud.add_argument("--port", type=int, default=8765, help="Loopback API port (default 8765).")
    hud.add_argument("--preview", action="store_true", help="Show an explicit synthetic HUD replay without control authority.")
    hud.set_defaults(func=run_hud_command)
    voice_mode = subparsers.add_parser(
        "voice-mode", help="Explicit push-to-talk offline transcription; transcripts never dispatch actions.",
    )
    voice_mode.add_argument("--model-dir", required=True, help="Pinned local model directory with stt-model.json receipt.")
    voice_mode.add_argument("--seconds", type=float, default=5.0, help="Microphone capture length, 0.5–12 seconds (default 5).")
    voice_mode.add_argument("--device", type=int, help="Optional PortAudio input-device number; default system device.")
    voice_mode.add_argument("--sample-wav", help="Transcribe a local PCM test WAV without opening the microphone.")
    voice_mode.add_argument("--speak-ack", action="store_true", help="Play a fixed Pocket Alba acknowledgement; never send transcript text.")
    voice_mode.add_argument("--data-dir", help="Data directory of a separately running local voice-enabled HTTP service.")
    voice_mode.add_argument("--port", type=int, default=8765, help="Port of the local voice-enabled HTTP service (default 8765).")
    voice_mode.set_defaults(func=run_voice_mode_command)
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
