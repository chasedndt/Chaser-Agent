import json
import subprocess
import sys
from pathlib import Path

from chaser_agent.visual_completion import evaluate_visual_completion


def test_screenshot_only_completion_stays_attempted_unverified():
    case = {
        "case_id": "screenshot-only-export",
        "instruction": "Export the report and verify the file exists.",
        "expected_outcome": "A report file exists and contains the requested fields.",
        "evidence": [
            {
                "type": "screenshot",
                "label": "final_screen",
                "summary": "The export dialog shows a green success-looking banner.",
            }
        ],
    }

    result = evaluate_visual_completion(case)

    assert result["outcome"] == "attempted_unverified"
    assert result["authority"]["can_mark_complete"] is False
    assert "non_visual_confirmation" in result["missing_evidence"]
    assert "Screenshot-only evidence cannot prove desired outcome" in result["rationale"]


def test_multisource_evidence_can_be_verified_but_remains_advisory():
    case = {
        "case_id": "export-with-file-and-content-proof",
        "instruction": "Export the report and verify the file exists.",
        "expected_outcome": "A report file exists and contains the requested fields.",
        "evidence": [
            {
                "type": "screenshot",
                "label": "final_screen",
                "summary": "The app shows export complete for report.csv.",
                "supports_expected_outcome": True,
            },
            {
                "type": "file_check",
                "label": "exported_report_exists",
                "summary": "report.csv exists in the expected output folder.",
                "supports_expected_outcome": True,
            },
            {
                "type": "content_check",
                "label": "exported_report_schema",
                "summary": "report.csv contains name, status, and updated_at columns.",
                "supports_expected_outcome": True,
            },
        ],
    }

    result = evaluate_visual_completion(case)

    assert result["outcome"] == "verified_success_advisory"
    assert result["confidence"] >= 0.85
    assert result["authority"]["can_mark_complete"] is False
    assert result["authority"]["requires_operator_review"] is True
    assert result["evidence_used"] == ["final_screen", "exported_report_exists", "exported_report_schema"]


def test_failed_evidence_is_classified_as_failed_with_operator_review():
    case = {
        "case_id": "failed-form-submit",
        "instruction": "Submit the intake form.",
        "expected_outcome": "The form is submitted and a confirmation page is visible.",
        "evidence": [
            {
                "type": "screenshot",
                "label": "final_screen",
                "summary": "The form shows a validation error and remains on the edit page.",
                "indicates_failure": True,
            }
        ],
    }

    result = evaluate_visual_completion(case)

    assert result["outcome"] == "failed"
    assert result["authority"]["can_mark_complete"] is False
    assert result["recommended_action"] == "fix_or_escalate"
    assert "final_screen" in result["evidence_used"]


def test_visual_eval_cli_writes_jsonl_results_and_run_log(tmp_path: Path):
    dataset = tmp_path / "visual_cases.jsonl"
    output_dir = tmp_path / "visual_eval_run"
    cases = [
        {
            "case_id": "screenshot-only-export",
            "instruction": "Export the report and verify the file exists.",
            "expected_outcome": "A report file exists and contains the requested fields.",
            "evidence": [{"type": "screenshot", "label": "final_screen", "summary": "Success banner is visible."}],
        },
        {
            "case_id": "export-with-file-and-content-proof",
            "instruction": "Export the report and verify the file exists.",
            "expected_outcome": "A report file exists and contains the requested fields.",
            "evidence": [
                {"type": "screenshot", "label": "final_screen", "summary": "Export complete is visible.", "supports_expected_outcome": True},
                {"type": "file_check", "label": "export_exists", "summary": "report.csv exists.", "supports_expected_outcome": True},
                {"type": "content_check", "label": "schema_matches", "summary": "columns match expected schema.", "supports_expected_outcome": True},
            ],
        },
    ]
    dataset.write_text("\n".join(json.dumps(case) for case in cases) + "\n", encoding="utf-8")

    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "chaser_agent.cli",
            "visual-eval",
            "--input",
            str(dataset),
            "--out",
            str(output_dir),
        ],
        text=True,
        capture_output=True,
        check=False,
    )

    assert completed.returncode == 0, completed.stderr
    run_folder = Path(completed.stdout.strip())
    assert run_folder.exists()
    results_path = run_folder / "visual_completion_results.jsonl"
    run_log_path = run_folder / "run_log.json"
    assert results_path.exists()
    assert run_log_path.exists()

    results = [json.loads(line) for line in results_path.read_text(encoding="utf-8").splitlines()]
    assert [result["case_id"] for result in results] == [case["case_id"] for case in cases]
    assert results[0]["outcome"] == "attempted_unverified"
    assert results[1]["outcome"] == "verified_success_advisory"

    run_log = json.loads(run_log_path.read_text(encoding="utf-8"))
    assert run_log["authority"]["provider_calls"] == "none"
    assert run_log["authority"]["browser_or_computer_use"] == "none"
    assert run_log["authority"]["fine_tuning"] == "none"
    assert run_log["authority"]["canonical_mutation"] == "none"
