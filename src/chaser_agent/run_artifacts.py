from __future__ import annotations

import json
import subprocess
from functools import lru_cache
from pathlib import Path
from typing import Any

from chaser_agent.source_card import PROMOTION_WARNING


def write_json(path: Path, data: Any) -> None:
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


@lru_cache(maxsize=None)
def current_repo_commit(repo_root: Path | None = None) -> str | None:
    """Return the short HEAD hash, memoised per repo root.

    Every run log stamps the commit, and a contract-eval pass builds one run log
    per case, so this shelled out to git once per case. The hash is constant for
    the life of a process here (batch CLI invocations and test runs), so the
    lookup is cached. A long-lived process that commits mid-run would see a stale
    value; nothing in this package is long-lived, and correctness of the stamp
    within a single run is what the artifact needs.
    """
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=repo_root,
            text=True,
            capture_output=True,
            check=False,
        )
    except OSError:
        return None
    if result.returncode != 0:
        return None
    return result.stdout.strip() or None


def build_run_log(
    *,
    run_id: str,
    created_at: str,
    command: str,
    input_source_id: str,
    output_paths: list[Path],
    repo_root: Path | None = None,
) -> dict[str, Any]:
    return {
        "run_id": run_id,
        "created_at": created_at,
        "command": command,
        "repo_commit": current_repo_commit(repo_root),
        "input_source_id": input_source_id,
        "outputs": [path.as_posix() for path in output_paths],
        "provider_calls": "none",
        "external_api_calls": "none",
        "runtime_adapters": "none",
        "mcp_activation": "none",
        "browser_or_computer_use": "none",
        "fine_tuning_or_training": "none",
        "blocked_actions": [
            "No memory promotion was performed.",
            "No ChaseOS canonical truth mutation was performed.",
            "No provider/API/runtime/MCP/browser/fine-tuning action was performed.",
        ],
        "review_required": True,
        "canonical_promotion_warning": PROMOTION_WARNING,
        "notes": "Deterministic local Source Card Harness V0 run. Review-only artifact shape proof.",
    }


def write_artifact_set(run_folder: Path, artifacts: dict[str, Any], run_log: dict[str, Any]) -> list[Path]:
    run_folder.mkdir(parents=True, exist_ok=False)
    output_paths: list[Path] = []
    for filename, payload in artifacts.items():
        path = run_folder / filename
        write_json(path, payload)
        output_paths.append(path)
    run_log_path = run_folder / "run_log.json"
    write_json(run_log_path, run_log)
    output_paths.append(run_log_path)
    return output_paths
