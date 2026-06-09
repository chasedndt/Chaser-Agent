import json
import subprocess
import sys
from pathlib import Path


ARTIFACT_FILES = [
    "source_card.json",
    "claims_table.json",
    "evidence_snippets.json",
    "uncertainty_labels.json",
    "action_candidates.json",
    "memory_candidates.json",
    "human_review_packet.json",
    "run_log.json",
]

REQUIRED_SOURCE_CARD_FIELDS = [
    "source_id",
    "source_title",
    "source_type",
    "source_origin",
    "privacy_class",
    "trust_state",
    "source_summary",
    "source_claims",
    "chaser_agent_inferences",
    "uncertainty_labels",
    "contradiction_notes",
    "action_candidates",
    "memory_candidates",
    "review_status",
    "promotion_status",
    "created_at",
    "run_id",
]


def run_source_card(input_path: Path, out_root: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            sys.executable,
            "-m",
            "chaser_agent.cli",
            "source-card",
            "--input",
            str(input_path),
            "--out",
            str(out_root),
        ],
        text=True,
        capture_output=True,
        check=False,
    )


def test_source_card_cli_creates_review_only_json_artifacts(tmp_path: Path):
    source = tmp_path / "toy_website_design_note.md"
    source.write_text(
        "# Toy website design note\n\n"
        "The hero section text is white. Dark mode and contrast may matter. "
        "Important keywords need subtle emphasis. Overdecorated styling can hurt readability. "
        "Current design best practice favours hierarchy, spacing, contrast, restraint, and user intent.\n",
        encoding="utf-8",
    )
    out_root = tmp_path / "runs"

    result = run_source_card(source, out_root)

    assert result.returncode == 0, result.stderr
    run_folder = Path(result.stdout.strip())
    assert run_folder.exists()
    assert run_folder.parent == out_root

    parsed = {}
    for filename in ARTIFACT_FILES:
        artifact_path = run_folder / filename
        assert artifact_path.exists(), filename
        parsed[filename] = json.loads(artifact_path.read_text(encoding="utf-8"))

    source_card = parsed["source_card.json"]
    for field in REQUIRED_SOURCE_CARD_FIELDS:
        assert field in source_card
    assert source_card["review_status"] == "pending_review"
    assert source_card["promotion_status"] == "not_promoted"
    assert source_card["trust_state"] == "unreviewed"
    assert source_card["privacy_class"] == "public_toy"
    assert source_card["source_claims"]
    assert source_card["chaser_agent_inferences"]
    assert source_card["uncertainty_labels"]
    assert source_card["action_candidates"]
    assert source_card["memory_candidates"]

    all_artifacts_text = json.dumps(parsed).lower()
    assert "canonical promotion approved" not in all_artifacts_text
    assert "promoted" not in [candidate.get("promotion_status") for candidate in source_card["memory_candidates"]]
    assert parsed["run_log.json"]["provider_calls"] == "none"
    assert parsed["run_log.json"]["external_api_calls"] == "none"
    assert parsed["run_log.json"]["runtime_adapters"] == "none"


def test_source_card_cli_missing_input_fails_cleanly(tmp_path: Path):
    missing = tmp_path / "missing.md"
    out_root = tmp_path / "runs"

    result = run_source_card(missing, out_root)

    assert result.returncode != 0
    assert "input file not found" in result.stderr.lower()
    assert not out_root.exists()
