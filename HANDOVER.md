
# Chaser agent Handover

## Current phase

V0 Blueprint Pass complete. The repo is ready for **Phase 1 — Source Card Harness V0**.

## Branch

`main`

## Repo path

- Windows: `C:\Users\chaseos\Documents\Projects\chaser-agent`
- WSL: `/mnt/c/Users/chaseos/Documents/Projects/chaser-agent`

## Reading order

1. `docs/01_Product/Chaser-Agent-Layer-0-Behaviour-Contract.md`
2. `docs/01_Product/Chaser-Agent-V0-Definition.md`
3. `docs/01_Product/Chaser-Agent-V0-Blueprint.md`
4. `docs/01_Product/Chaser-Agent-From-First-Principles.md`
5. `docs/01_Product/Chaser-Agent-Product-Thesis.md`
6. `docs/01_Product/Chaser-Agent-Roadmap.md`
7. `docs/01_Product/Chaser-Agent-17-Layer-Architecture.md`
8. `docs/03_Summary_Intelligence/Chaser-Agent-V0-Source-Card-Schema.md`
9. `docs/02_Evals/Chaser-Agent-V0-Human-Review-Packet.md`
10. `docs/03_Summary_Intelligence/Chaser-Agent-Source-Summary-Spec.md`

## What changed conceptually

The repo is no longer ordered around eval scaffolding first. The correct order is:

1. Layer 0 Behaviour Contract;
2. V0 Definition;
3. V0 Blueprint;
4. first-principles product model;
5. Product Thesis and Roadmap;
6. 17-layer architecture subordinate to Layer 0;
7. learning/maths/university foundations;
8. Source Card Harness V0 implementation;
9. contract evals only after behavior can be produced.

## Baseline results

Latest V0 Blueprint Pass validation:

```text
PYTHONPATH=. .venv/bin/python -m pytest -q        # 5 passed
.venv/bin/python -m scripts.validate_jsonl evals/datasets/golden/*.jsonl  # all six valid, 3 rows each
```

Detailed pass record: `logs/build/2026-06-09-v0-blueprint-pass.md`.

## Starter artifacts

The Excel research/eval register and pack manifest remain on `main` under:

- `docs/07_Research/Chaser_Agent_Research_Eval_Register.xlsx`
- `docs/07_Research/PACK_MANIFEST.json`

## Stash note

`stash@{0}` exists from earlier work:

```text
stash@{0}: On docs/spec-deepening-pass: pre-layer0-reset-uncommitted-work-2026-06-09
```

It was not applied or deleted during the V0 Blueprint Pass. It needs a future stash-audit pass before any reuse.

## Next recommended pass

**Phase 1 — Source Card Harness V0.** Implement the source-card loop locally and deterministically from the V0 Blueprint. Do not start eval harness v0.2, fine-tuning, provider calls, broad adapters, MCP tooling, browser runtime, private datasets, or ChaseOS canonical mutation before the harness exists.
