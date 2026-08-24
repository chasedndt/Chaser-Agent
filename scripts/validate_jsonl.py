from __future__ import annotations

import argparse
import glob
import json
from pathlib import Path


def validate_jsonl(path: str | Path) -> int:
    candidate = Path(path)
    count = 0
    with candidate.open("r", encoding="utf-8") as handle:
        for line_no, line in enumerate(handle, 1):
            if not line.strip():
                continue
            value = json.loads(line)
            if not isinstance(value, dict):
                raise ValueError(f"{candidate}:{line_no}: expected JSON object")
            count += 1
    return count


def expand_inputs(arguments: list[str]) -> list[Path]:
    expanded: list[Path] = []
    for argument in arguments:
        if glob.has_magic(argument):
            matches = [Path(match) for match in sorted(glob.glob(argument))]
            if not matches:
                raise FileNotFoundError(f"JSONL pattern matched no files: {argument}")
            expanded.extend(matches)
        else:
            expanded.append(Path(argument))
    return expanded


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("paths", nargs="+")
    args = parser.parse_args(argv)
    for path in expand_inputs(args.paths):
        count = validate_jsonl(path)
        print(f"{path}: valid JSONL ({count} rows)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
