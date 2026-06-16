from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError as exc:  # pragma: no cover - environment guard
    raise SystemExit("PyYAML is required for research intake config validation") from exc


REQUIRED_CONFIGS = [
    Path("research_intake/sources.yaml"),
    Path("research_intake/queries.yaml"),
    Path("research_intake/ranking.yaml"),
    Path("research_intake/cron_proposal.yaml"),
]


def utc_stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def load_yaml(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle) or {}


def validate_sources(config: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    policy = config.get("run_policy", {})
    control = config.get("control_plane", {})
    sources = config.get("sources", {})
    if policy.get("require_eval_gate") is not True:
        errors.append("run_policy.require_eval_gate must be true")
    if policy.get("live_candidate_implementation_enabled") is not False:
        errors.append("live_candidate_implementation_enabled must remain false in Phase 1")
    if "canonical_promotion" not in control.get("blocked_actions", []):
        errors.append("control_plane.blocked_actions must include canonical_promotion")
    if not sources.get("arxiv_api", {}).get("enabled"):
        errors.append("arxiv_api must be enabled for Phase 1A/1B")
    return errors


def validate_queries(config: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if not config.get("arxiv_queries"):
        errors.append("at least one arxiv query is required")
    if not config.get("positive_terms"):
        errors.append("positive_terms are required for scoring/ranking")
    return errors


def validate_ranking(config: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    weights = config.get("score_weights", {})
    total = sum(float(value) for value in weights.values())
    if round(total, 5) != 1.0:
        errors.append(f"score_weights must sum to 1.0, got {total}")
    if "expands_security_or_tool_permissions_without_controls" not in config.get("penalties", {}):
        errors.append("security/tool permission expansion penalty is required")
    return errors


def build_manifest(repo_root: Path) -> dict[str, Any]:
    loaded = {str(path): load_yaml(repo_root / path) for path in REQUIRED_CONFIGS}
    errors: list[str] = []
    errors.extend(validate_sources(loaded["research_intake/sources.yaml"]))
    errors.extend(validate_queries(loaded["research_intake/queries.yaml"]))
    errors.extend(validate_ranking(loaded["research_intake/ranking.yaml"]))
    proposed = loaded["research_intake/cron_proposal.yaml"].get("proposed_jobs", {})
    if not proposed:
        errors.append("cron_proposal.yaml must contain proposed_jobs")

    enabled_sources = [
        name
        for name, source in loaded["research_intake/sources.yaml"].get("sources", {}).items()
        if isinstance(source, dict) and source.get("enabled") is True
    ]
    arxiv_queries = loaded["research_intake/queries.yaml"].get("arxiv_queries", [])

    return {
        "status": "pass" if not errors else "fail",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "phase": "phase_1a_deterministic_config_dry_run",
        "control_plane": {
            "parent": "ChaseOS",
            "authority": "research artifacts only",
            "no_canonical_promotion": True,
            "no_candidate_implementation": True,
            "no_provider_or_credential_activation": True,
            "live_cron_activation": "not_performed_by_this_script",
        },
        "validated_configs": [str(path) for path in REQUIRED_CONFIGS],
        "enabled_sources": enabled_sources,
        "arxiv_query_count": len(arxiv_queries),
        "proposed_cron_jobs": sorted(proposed),
        "errors": errors,
    }


def write_digest(run_dir: Path, manifest: dict[str, Any]) -> None:
    lines = [
        "# Weekly Research Intake Dry Run",
        "",
        f"- Status: `{manifest['status']}`",
        f"- Phase: `{manifest['phase']}`",
        f"- Created: `{manifest['created_at']}`",
        f"- Enabled sources: {', '.join(manifest['enabled_sources']) or 'none'}",
        f"- arXiv query count: {manifest['arxiv_query_count']}",
        f"- Proposed cron jobs: {', '.join(manifest['proposed_cron_jobs']) or 'none'}",
        "",
        "## Control-plane boundary",
        "",
        "This dry run validates local config only. It does not fetch network sources, call providers, activate credentials, create branches, open PRs, merge changes, or promote ChaseOS canonical truth.",
    ]
    if manifest["errors"]:
        lines.extend(["", "## Errors", ""])
        lines.extend(f"- {error}" for error in manifest["errors"])
    run_dir.joinpath("digest.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def make_unique_run_dir(out_root: Path, base_name: str) -> Path:
    candidate = out_root / base_name
    if not candidate.exists():
        return candidate
    for index in range(1, 1000):
        candidate = out_root / f"{base_name}-{index:03d}"
        if not candidate.exists():
            return candidate
    raise FileExistsError(f"could not allocate unique run directory for {base_name}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate Weekly Research Intake Phase 1A config and write a local run artifact.")
    parser.add_argument("--out", default="logs/runs", help="Output root for dry-run artifact folder.")
    args = parser.parse_args()

    repo_root = Path.cwd()
    manifest = build_manifest(repo_root)
    base_name = f"weekly-research-intake-dry-run-{utc_stamp()}"
    run_dir = make_unique_run_dir(Path(args.out), base_name)
    run_dir.mkdir(parents=True, exist_ok=False)
    run_dir.joinpath("manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_digest(run_dir, manifest)
    print(run_dir.as_posix())
    return 0 if manifest["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
