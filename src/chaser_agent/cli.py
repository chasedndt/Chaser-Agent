from __future__ import annotations

import argparse
import sys
from pathlib import Path

from chaser_agent.run_artifacts import build_run_log, write_artifact_set
from chaser_agent.source_card import (
    build_source_card_artifacts,
    make_run_id,
    source_input_from_file,
    utc_now_iso,
)


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
