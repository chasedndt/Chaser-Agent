# 2026-06-09 — Chaser agent Layer 0 Ground-Up Reset

## Starting branch

```text
docs/spec-deepening-pass
```

The repo started on the side branch with additional unstaged tracked modifications. Those unstaged changes were preserved with a Git stash before returning to `main`:

```text
stash@{0}: On docs/spec-deepening-pass: pre-layer0-reset-uncommitted-work-2026-06-09
```

## Main sync / Prompt A result

`main` was pulled from GitHub, prior spec-deepening work was merged onto `main`, safe starter artifacts were moved under `docs/07_Research/`, baseline checks passed, and `main` was pushed.

Starter artifacts retained:

- `docs/07_Research/Chaser_Agent_Research_Eval_Register.xlsx`
- `docs/07_Research/PACK_MANIFEST.json`

Prompt A commit:

```text
604bf22 chore: retain starter pack research artifacts
```

## Layer 0 baseline tests

Before Layer 0 edits:

```bash
PYTHONPATH=. .venv/bin/python -m pytest -q
.venv/bin/python -m scripts.validate_jsonl evals/datasets/golden/*.jsonl
```

Result:

```text
5 passed
all six golden JSONL files valid, 3 rows each
```

## Files created

- `docs/01_Product/Chaser-Agent-Layer-0-Behaviour-Contract.md`
- `docs/01_Product/Chaser-Agent-V0-Definition.md`
- `docs/01_Product/Chaser-Agent-From-First-Principles.md`
- `logs/build/2026-06-09-layer0-ground-up-reset.md`

## Files modified

- `README.md`
- `START_HERE.md`
- `NEXT_STEPS.md`
- `HANDOVER.md`
- `docs/00_START_HERE.md`
- `docs/01_Product/Chaser-Agent-Product-Thesis.md`
- `docs/01_Product/Chaser-Agent-Roadmap.md`
- `docs/01_Product/Chaser-Agent-17-Layer-Architecture.md`
- `docs/02_Evals/Chaser-Agent-Eval-Harness.md`
- `docs/02_Evals/Chaser-Agent-Dataset-Plan.md`
- `docs/03_Summary_Intelligence/Chaser-Agent-Source-Summary-Spec.md`
- `docs/08_Learning/AI-Engineering-Learning-Map.md`
- `docs/08_Learning/Maths-For-Chaser-Agent.md`
- `docs/08_Learning/University-Module-Linkage.md`

## What was reclassified

Existing tests and JSONL files were reclassified as smoke/schema checks unless they explicitly test Layer 0 behavior. JSONL is documented as a data format, not proof by itself. Product-quality evals are deferred until V0 expected behavior is locked.

## What was not implemented

- no provider/API calls;
- no Hermes/OpenClaw adapter activation;
- no browser/computer-use runtime;
- no fine-tuning or LoRA;
- no private dataset ingestion;
- no ChaseOS canonical mutation;
- no broad runtime autonomy;
- no deeper eval implementation.

## Post-pass tests

```bash
.venv/bin/python -m scripts.validate_jsonl evals/datasets/golden/*.jsonl
PYTHONPATH=. .venv/bin/python -m pytest -q
```

Result:

```text
all six golden JSONL files valid, 3 rows each
5 passed in 0.60s
```

## Remaining gaps

- The exact V0 source-card implementation blueprint is not yet written.
- Contract evals do not yet exist.
- Existing toy JSONL rows are not product-quality proof.
- Website alignment still needs manual page text or screenshots.
- The pre-reset side-branch unstaged work remains preserved in `stash@{0}` and should be reviewed before deletion.

## Next recommended pass

```text
Chaser agent V0 Blueprint Pass
```

Goal: lock the implementation-ready V0 loop:

```text
source input
→ safe intake
→ source card
→ claims
→ uncertainty
→ action candidates
→ memory candidates
→ human review
→ no automatic canonical promotion
```
