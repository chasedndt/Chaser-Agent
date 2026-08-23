from pathlib import Path

from scripts.export_test_matrix import export_test_matrix


DATASET_ROOT = Path("evals/datasets")
COMMITTED_MATRIX = Path("docs/02_Evals/Chaser-Agent-Current-Test-Matrix.md")


def test_export_includes_every_seed_exact_assertions_and_honest_maturity(tmp_path: Path):
    output = tmp_path / "matrix.md"

    counts = export_test_matrix(DATASET_ROOT, output)
    text = output.read_text(encoding="utf-8")

    # Counts follow the datasets rather than freezing them: the exporter must
    # report exactly what is on disk, so growing coverage is not a test failure.
    assert counts["files"] >= 9
    assert counts["golden_cases"] == 21
    assert counts["contract_cases"] >= 30
    assert counts["workflow_episode_cases"] >= 1
    assert counts["cases"] == (
        counts["golden_cases"] + counts["contract_cases"] + counts["workflow_episode_cases"]
    )
    assert "`source_card_001`" in text
    assert "`contract_evidence_001`" in text
    assert "`marginflip_marketing_foundation_plan_001`" in text
    assert '"references_resolve"' in text
    assert "GENERIC SMOKE SEED ONLY" in text
    assert "EXECUTABLE WORKFLOW EPISODE SEED" in text
    assert "they are not achieved model scores" in text


def test_committed_matrix_matches_exporter(tmp_path: Path):
    output = tmp_path / "matrix.md"
    export_test_matrix(DATASET_ROOT, output)

    assert COMMITTED_MATRIX.read_text(encoding="utf-8") == output.read_text(encoding="utf-8")
