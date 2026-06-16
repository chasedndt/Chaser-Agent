from pathlib import Path

import yaml

from scripts.weekly_research_intake_dry_run import build_manifest, make_unique_run_dir


def test_weekly_research_intake_configs_are_control_plane_bounded():
    root = Path(__file__).resolve().parents[1]
    manifest = build_manifest(root)

    assert manifest["status"] == "pass"
    assert manifest["control_plane"]["no_canonical_promotion"] is True
    assert manifest["control_plane"]["no_candidate_implementation"] is True
    assert manifest["control_plane"]["no_provider_or_credential_activation"] is True
    assert "arxiv_api" in manifest["enabled_sources"]
    assert manifest["arxiv_query_count"] >= 1


def test_weekly_research_intake_ranking_weights_sum_to_one():
    root = Path(__file__).resolve().parents[1]
    ranking = yaml.safe_load(root.joinpath("research_intake/ranking.yaml").read_text(encoding="utf-8"))

    assert round(sum(ranking["score_weights"].values()), 5) == 1.0
    assert ranking["penalties"]["expands_security_or_tool_permissions_without_controls"] == -30


def test_weekly_research_intake_dry_run_uses_unique_folder_when_stamp_collides(tmp_path):
    first = make_unique_run_dir(tmp_path, "weekly-research-intake-dry-run-fixed")
    first.mkdir()

    second = make_unique_run_dir(tmp_path, "weekly-research-intake-dry-run-fixed")

    assert second.name == "weekly-research-intake-dry-run-fixed-001"
