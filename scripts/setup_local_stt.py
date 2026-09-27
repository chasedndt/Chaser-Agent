"""Explicit one-time anonymous download of a pinned local English STT model."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path

from chaser_agent.local_stt import MODEL_FILES, MODEL_REPO, MODEL_REVISION


def main() -> int:
    parser = argparse.ArgumentParser(description="Install the optional pinned local STT model")
    parser.add_argument("--output", required=True, type=Path, help="Model directory outside the source repository")
    parser.add_argument("--accept-download", action="store_true", help="Explicitly allow the one-time model download")
    args = parser.parse_args()
    if not args.accept_download:
        parser.error("--accept-download is required; normal voice mode never downloads")
    output = args.output.resolve()
    repo = Path(__file__).resolve().parents[1]
    if output.is_relative_to(repo) or args.output.is_symlink():
        parser.error("Model output must be a real directory outside the repository")
    receipt = output / "stt-model.json"
    if receipt.exists() or receipt.is_symlink():
        parser.error("A model receipt already exists; refusing to overwrite it")
    os.environ["HF_HUB_DISABLE_IMPLICIT_TOKEN"] = "1"
    from huggingface_hub import snapshot_download

    snapshot_download(
        MODEL_REPO, revision=MODEL_REVISION, local_dir=output,
        allow_patterns=list(MODEL_FILES), token=False,
    )
    hashes = {}
    for name in MODEL_FILES:
        with (output / name).open("rb") as stream:
            hashes[name] = hashlib.file_digest(stream, "sha256").hexdigest()
    payload = {"schema_version": 1, "source_repo": MODEL_REPO, "revision": MODEL_REVISION,
               "license": "mit", "files": hashes}
    with receipt.open("x", encoding="utf-8") as stream:
        json.dump(payload, stream, indent=2)
        stream.write("\n")
    print(f"Local STT model verified: {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
