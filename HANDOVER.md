# Chaser agent Handover

## Current branch

```text
docs/spec-deepening-pass
```

## Current repo path

```text
C:\Users\chaseos\Documents\Projects\chaser-agent
/mnt/c/Users/chaseos/Documents/Projects/chaser-agent
```

## Current phase

Phase 0C — Chaser agent Spec Deepening + Repo Truth Pass.

This pass is documentation-first. It deepens scaffold specs so future Hermes/Codex/Claude Code work can build from repo truth instead of chat context.

## Tests and validation recorded

Initial system-python attempt:

```text
python3 -m scripts.validate_jsonl evals/datasets/golden/*.jsonl  # passed for all six golden files
python3 -m pytest -q                                             # failed: No module named pytest
```

Environment repair:

```text
uv venv .venv --python python3
uv pip install --python .venv/bin/python -e '.[dev]'
```

Baseline after WSL venv creation:

```text
.venv/bin/python -m scripts.validate_jsonl evals/datasets/golden/*.jsonl  # all six files valid, 3 rows each
PYTHONPATH=. .venv/bin/python -m pytest -q                                # 5 passed
```

Post-pass validation should match the same commands.

## Files expanded in Phase 0C

- `docs/01_Product/Chaser-Agent-Product-Thesis.md`
- `docs/01_Product/Chaser-Agent-Roadmap.md`
- `docs/01_Product/Chaser-Agent-17-Layer-Architecture.md`
- `docs/02_Evals/Chaser-Agent-Dataset-Plan.md`
- `docs/03_Summary_Intelligence/Chaser-Agent-Source-Summary-Spec.md`
- `docs/04_Memory/Chaser-Agent-Memory-States.md`
- `docs/05_Runtime_Adapters/Chaser-Agent-OpenClaw-Hermes-Competitor-Map.md`
- `docs/06_Skills/Chaser-Agent-Skill-System.md`
- `docs/07_Research/Chaser-Agent-Research-Register.md`

## Files created in Phase 0C

- `docs/07_Research/ChaseOS-Website-Alignment.md`
- `logs/build/2026-06-09-spec-deepening-pass.md`

## Files lightly updated

- `START_HERE.md`
- `NEXT_STEPS.md`
- `HANDOVER.md`

## Artifact policy

Commit `Chaser_Agent_Research_Eval_Register.xlsx` as the operator-facing research/eval register. Commit `PACK_MANIFEST.json` as provenance for the starter pack. Keep private raw datasets out of Git.

## Remaining gaps

- Eval harness v0.2 still needs implementation.
- Source-card harness should become stronger after eval result rows exist.
- Website alignment still requires manual page text or screenshots.
- Runtime adapters remain notes/mock targets only.
- Fine-tuning remains explicitly later.

## Exact next recommended pass

```text
Eval harness v0.2 — deterministic result rows, per-family runner support, timestamped JSONL logs, and tests for id/task/passed/score/failure_reasons/output/timestamp/runner_version.
```
