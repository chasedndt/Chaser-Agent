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
    "chaseos_native_packet.json",
    "operator_handoff.md",
    "run_log.json",
]


def run_chaseos_native_source_card(input_path: Path, out_root: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            sys.executable,
            "-m",
            "chaser_agent.cli",
            "chaseos-native-source-card",
            "--input",
            str(input_path),
            "--out",
            str(out_root),
            "--workflow",
            "hermes_review_execute",
            "--runtime-lane",
            "chaser-agent",
        ],
        text=True,
        capture_output=True,
        check=False,
    )


def test_chaseos_native_source_card_creates_control_plane_review_packet(tmp_path: Path):
    source = tmp_path / "operator_note.md"
    source.write_text(
        "# Operator note\n\n"
        "Chaser Agent should preserve source evidence, label uncertainty, and propose actions without mutating ChaseOS canonical truth.\n"
        "A native ChaseOS handoff should include runtime lane, workflow, graph links, authority flags, and blocked actions.\n",
        encoding="utf-8",
    )
    out_root = tmp_path / "runs"

    result = run_chaseos_native_source_card(source, out_root)

    assert result.returncode == 0, result.stderr
    run_folder = Path(result.stdout.strip())
    assert run_folder.exists()
    assert run_folder.parent == out_root
    for filename in ARTIFACT_FILES:
        assert (run_folder / filename).exists(), filename

    packet = json.loads((run_folder / "chaseos_native_packet.json").read_text(encoding="utf-8"))
    assert packet["surface_id"] == "chaser_agent_chaseos_native_source_card_v0"
    assert packet["runtime_lane"] == "chaser-agent"
    assert packet["workflow"] == "hermes_review_execute"
    assert packet["review_status"] == "pending_operator_review"
    assert packet["promotion_status"] == "not_promoted"
    assert packet["chaseos_graph_links"] == ["[[HERMES]]", "[[Hermes-Runtime-Profile]]", "[[Agent-Activity-Index]]"]
    assert packet["authority"]["canonical_mutation_performed"] is False
    assert packet["authority"]["provider_call_performed"] is False
    assert packet["authority"]["runtime_dispatch_performed"] is False
    assert packet["authority"]["approval_consumed"] is False
    assert packet["recommended_agent_activity_slug"].startswith("hermes-optimus-chaser-agent-native-")

    handoff = (run_folder / "operator_handoff.md").read_text(encoding="utf-8")
    assert "# Chaser Agent ChaseOS-Native Source Card Handoff" in handoff
    assert "[[HERMES]]" in handoff
    assert "No ChaseOS canonical truth mutation was performed." in handoff
    assert "Provider calls: none" in handoff

    run_log = json.loads((run_folder / "run_log.json").read_text(encoding="utf-8"))
    assert run_log["command_family"] == "chaseos-native-source-card"
    assert run_log["provider_calls"] == "none"
    assert run_log["runtime_adapters"] == "none"
    assert run_log["review_required"] is True


def test_chaseos_native_source_card_rejects_unknown_workflow(tmp_path: Path):
    source = tmp_path / "operator_note.md"
    source.write_text("safe note", encoding="utf-8")
    out_root = tmp_path / "runs"

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "chaser_agent.cli",
            "chaseos-native-source-card",
            "--input",
            str(source),
            "--out",
            str(out_root),
            "--workflow",
            "unbounded_live_adapter",
        ],
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 2
    assert "unsupported chaseos workflow" in result.stderr.lower()
    assert not out_root.exists()
