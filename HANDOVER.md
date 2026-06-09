# Chaser agent Handover

## Current phase

Layer 0 Ground-Up Reset Pass.

## Branch

`main`

## Repo path

- Windows: `C:\Users\chaseos\Documents\Projects\chaser-agent`
- WSL: `/mnt/c/Users/chaseos/Documents/Projects/chaser-agent`

## What changed conceptually

The repo is no longer ordered around eval scaffolding first. The correct order is:

1. Layer 0 Behaviour Contract;
2. V0 Definition;
3. First-principles product model;
4. Product Thesis and Roadmap;
5. 17-layer architecture subordinate to Layer 0;
6. learning/maths/university foundations;
7. evals only after behavior definition.

## Baseline results

Before Layer 0 edits:

```text
PYTHONPATH=. .venv/bin/python -m pytest -q        # 5 passed
.venv/bin/python -m scripts.validate_jsonl evals/datasets/golden/*.jsonl  # all six valid, 3 rows each
```

Post-pass results are recorded in `logs/build/2026-06-09-layer0-ground-up-reset.md`.

## Starter artifacts

The Excel research/eval register and pack manifest were retained on `main` under:

- `docs/07_Research/Chaser_Agent_Research_Eval_Register.xlsx`
- `docs/07_Research/PACK_MANIFEST.json`

## Next recommended pass

Chaser agent V0 Blueprint Pass. Do not start fine-tuning, provider calls, broad adapters, or more eval deepening before the V0 loop is locked.
