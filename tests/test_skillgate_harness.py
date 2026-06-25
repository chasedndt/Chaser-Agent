import json
import subprocess
import sys
from pathlib import Path


ARTIFACT_FILES = [
    "skill_gate_packet.json",
    "skill_patch_review.json",
    "run_log.json",
]


def run_skill_gate(baseline: Path, candidate: Path, metrics: Path, out_root: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            sys.executable,
            "-m",
            "chaser_agent.cli",
            "skill-gate",
            "--baseline-skill",
            str(baseline),
            "--candidate-skill",
            str(candidate),
            "--metrics",
            str(metrics),
            "--out",
            str(out_root),
        ],
        text=True,
        capture_output=True,
        check=False,
    )


def write_skill(path: Path, body: str) -> None:
    path.write_text(body, encoding="utf-8")


def write_metrics(path: Path, *, baseline_score: float, candidate_score: float, edit_count: int = 4) -> None:
    path.write_text(
        json.dumps(
            {
                "baseline_score": baseline_score,
                "candidate_score": candidate_score,
                "held_out_split_id": "toy-heldout-v0",
                "edit_count": edit_count,
                "verifier": "deterministic-toy-fixture",
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )


def test_skill_gate_cli_creates_review_packet_for_strict_heldout_improvement(tmp_path: Path):
    baseline = tmp_path / "baseline.SKILL.md"
    candidate = tmp_path / "candidate.SKILL.md"
    metrics = tmp_path / "metrics.json"
    out_root = tmp_path / "runs"

    write_skill(
        baseline,
        "# Source Card Review\n\n"
        "<!-- CHASER:SLOW-STATE:BEGIN -->\n"
        "Never promote memory automatically.\n"
        "<!-- CHASER:SLOW-STATE:END -->\n\n"
        "Summarize source claims.\n",
    )
    write_skill(
        candidate,
        "# Source Card Review\n\n"
        "<!-- CHASER:SLOW-STATE:BEGIN -->\n"
        "Never promote memory automatically.\n"
        "<!-- CHASER:SLOW-STATE:END -->\n\n"
        "Summarize source claims, cite evidence, and label uncertainty before proposing actions.\n",
    )
    write_metrics(metrics, baseline_score=0.62, candidate_score=0.79, edit_count=4)
    baseline_before = baseline.read_text(encoding="utf-8")

    result = run_skill_gate(baseline, candidate, metrics, out_root)

    assert result.returncode == 0, result.stderr
    assert baseline.read_text(encoding="utf-8") == baseline_before
    run_folder = Path(result.stdout.strip())
    assert run_folder.exists()
    assert run_folder.parent == out_root

    parsed = {}
    for filename in ARTIFACT_FILES:
        artifact_path = run_folder / filename
        assert artifact_path.exists(), filename
        parsed[filename] = json.loads(artifact_path.read_text(encoding="utf-8"))

    packet = parsed["skill_gate_packet.json"]
    assert packet["decision"] == "candidate_patch_reviewable"
    assert packet["acceptance_policy"] == "strict_held_out_improvement_only"
    assert packet["baseline_score"] == 0.62
    assert packet["candidate_score"] == 0.79
    assert packet["score_delta"] == 0.17
    assert packet["protected_section_preserved"] is True
    assert packet["bounded_edit_budget_passed"] is True
    assert packet["review_status"] == "pending_operator_review"
    assert packet["write_performed"] is False
    assert packet["autonomous_skill_mutation"] is False
    assert parsed["run_log.json"]["provider_calls"] == "none"
    assert parsed["run_log.json"]["external_api_calls"] == "none"
    assert parsed["run_log.json"]["runtime_adapters"] == "none"


def test_skill_gate_rejects_ties_and_protected_section_changes(tmp_path: Path):
    baseline = tmp_path / "baseline.SKILL.md"
    candidate = tmp_path / "candidate.SKILL.md"
    metrics = tmp_path / "metrics.json"
    out_root = tmp_path / "runs"

    write_skill(
        baseline,
        "# Skill\n\n"
        "<!-- CHASER:SLOW-STATE:BEGIN -->\n"
        "Human approval is required.\n"
        "<!-- CHASER:SLOW-STATE:END -->\n\n"
        "Fast guidance.\n",
    )
    write_skill(
        candidate,
        "# Skill\n\n"
        "<!-- CHASER:SLOW-STATE:BEGIN -->\n"
        "Human approval is optional.\n"
        "<!-- CHASER:SLOW-STATE:END -->\n\n"
        "Fast guidance with extra detail.\n",
    )
    write_metrics(metrics, baseline_score=0.70, candidate_score=0.70, edit_count=2)

    result = run_skill_gate(baseline, candidate, metrics, out_root)

    assert result.returncode == 0, result.stderr
    run_folder = Path(result.stdout.strip())
    packet = json.loads((run_folder / "skill_gate_packet.json").read_text(encoding="utf-8"))
    assert packet["decision"] == "candidate_patch_rejected"
    assert packet["strict_improvement_passed"] is False
    assert packet["protected_section_preserved"] is False
    assert "Candidate score must strictly improve held-out validation score." in packet["rejection_reasons"]
    assert "Protected slow-state section changed." in packet["rejection_reasons"]
    assert packet["write_performed"] is False



def test_chaser_skillgate_preflight_blocks_sentinel_do_not_install_report(tmp_path: Path):
    from chaser_agent.skillgate import build_agent_skills_sentinel_preflight

    package = tmp_path / "package"
    package.mkdir()
    report_path = tmp_path / "sentinel-report.json"
    report_path.write_text(
        json.dumps({
            "surface_id": "chaseos_agent_skills_sentinel",
            "verdict": "do_not_install",
            "risk_score": 92,
            "artifact": {"path": package.as_posix(), "sha256": "abc123"},
            "report_artifact": {"report_sha256": "def456"},
            "authority": {"skill_execution_performed": False, "runtime_dispatch_performed": False},
        }),
        encoding="utf-8",
    )

    preflight = build_agent_skills_sentinel_preflight(package_path=package, sentinel_report_path=report_path)

    assert preflight["decision"] == "activation_blocked"
    assert preflight["sentinel_verdict"] == "do_not_install"
    assert preflight["report_path"] == report_path.as_posix()
    assert preflight["package_path"] == package.as_posix()
    assert preflight["authority"]["package_execution_performed"] is False
    assert preflight["authority"]["activation_performed"] is False


def test_chaser_skillgate_preflight_holds_safe_report_for_allowlist_promotion(tmp_path: Path):
    from chaser_agent.skillgate import build_agent_skills_sentinel_preflight

    package = tmp_path / "package"
    package.mkdir()
    report_path = tmp_path / "sentinel-report.json"
    report_path.write_text(
        json.dumps({
            "surface_id": "chaseos_agent_skills_sentinel",
            "verdict": "safe",
            "risk_score": 0,
            "artifact": {"path": package.as_posix(), "sha256": "abc123"},
            "report_artifact": {"report_sha256": "def456"},
            "authority": {"skill_execution_performed": False, "runtime_dispatch_performed": False},
        }),
        encoding="utf-8",
    )

    preflight = build_agent_skills_sentinel_preflight(package_path=package, sentinel_report_path=report_path)

    assert preflight["decision"] == "awaiting_allowlist_promotion"
    assert preflight["sentinel_verdict"] == "safe"
    assert preflight["activation_allowed"] is False
    assert preflight["required_next_step"] == "operator_gate_allowlist_decision"
