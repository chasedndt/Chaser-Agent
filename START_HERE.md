# Start Here — Chaser agent

Start with Layer 0. Do not start with eval implementation.

Read in this order:

1. `docs/01_Product/Chaser-Agent-Layer-0-Behaviour-Contract.md`
2. `docs/01_Product/Chaser-Agent-V0-Definition.md`
3. `docs/01_Product/Chaser-Agent-From-First-Principles.md`
4. `docs/01_Product/Chaser-Agent-Product-Thesis.md`
5. `docs/01_Product/Chaser-Agent-Roadmap.md`
6. `docs/01_Product/Chaser-Agent-17-Layer-Architecture.md`
7. `docs/08_Learning/AI-Engineering-Learning-Map.md`
8. `docs/08_Learning/Maths-For-Chaser-Agent.md`
9. `docs/08_Learning/University-Module-Linkage.md`
10. `docs/03_Summary_Intelligence/Chaser-Agent-Source-Summary-Spec.md`

## Current truth

The repo exists and tests run, but existing JSONL/tests are smoke/schema checks unless they test Layer 0 behavior. The next work is V0 blueprint planning and then Source Card Harness V0.

## Verification

```bash
.venv/bin/python -m scripts.validate_jsonl evals/datasets/golden/*.jsonl
PYTHONPATH=. .venv/bin/python -m pytest -q
```
