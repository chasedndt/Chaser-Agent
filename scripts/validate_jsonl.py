from __future__ import annotations
import argparse, json
from pathlib import Path

def validate_jsonl(path: str | Path) -> int:
    p=Path(path)
    count=0
    with p.open("r", encoding="utf-8") as f:
        for line_no,line in enumerate(f,1):
            if not line.strip():
                continue
            obj=json.loads(line)
            if not isinstance(obj, dict):
                raise ValueError(f"{p}:{line_no}: expected JSON object")
            count += 1
    return count

def main(argv: list[str] | None = None) -> int:
    parser=argparse.ArgumentParser()
    parser.add_argument("paths", nargs="+")
    args=parser.parse_args(argv)
    for path in args.paths:
        count=validate_jsonl(path)
        print(f"{path}: valid JSONL ({count} rows)")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
