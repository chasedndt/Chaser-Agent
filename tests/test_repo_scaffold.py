from pathlib import Path

def test_package_imports():
    import chaser_agent
    assert chaser_agent.__version__ == "0.1.0"

def test_expected_scaffold_paths_exist():
    for rel in ["README.md", "START_HERE.md", "docs/02_Evals", "evals/datasets/golden", "tests"]:
        assert Path(rel).exists(), rel
