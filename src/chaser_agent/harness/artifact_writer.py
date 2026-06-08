from pathlib import Path

def write_artifact(path: str | Path, content: str) -> Path:
    target=Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")
    return target
