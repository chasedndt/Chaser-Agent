# 2026-06-09 — Phase 0C Spec Deepening Pass

## Branch

```text
docs/spec-deepening-pass
```

## Purpose

Turn thin Chaser agent scaffold docs into usable development/specification documents without overclaiming implementation. This was documentation-first and eval-first. It did not activate providers, adapters, fine-tuning, UI/Studio work, private datasets, or ChaseOS canonical writeback.

## Commands run

Initial state and baseline:

```bash
git status --short --branch
git rev-parse --abbrev-ref HEAD
git rev-parse --short HEAD
git remote -v
python3 -m scripts.validate_jsonl evals/datasets/golden/*.jsonl
python3 -m pytest -q
```

Initial validation result:

```text
All six golden JSONL files valid, 3 rows each.
python3 -m pytest -q failed because system Python did not have pytest installed: No module named pytest.
```

Environment setup:

```bash
uv venv .venv --python python3
uv pip install --python .venv/bin/python -e '.[dev]'
.venv/bin/python -m pytest --version
```

Environment result:

```text
pytest 9.0.3 installed inside .venv
```

Baseline after venv:

```bash
.venv/bin/python -m scripts.validate_jsonl evals/datasets/golden/*.jsonl
PYTHONPATH=. .venv/bin/python -m pytest -q
```

Result:

```text
All six golden JSONL files valid, 3 rows each.
5 passed.
```

Post-pass validation:

```bash
.venv/bin/python -m scripts.validate_jsonl evals/datasets/golden/*.jsonl
PYTHONPATH=. .venv/bin/python -m pytest -q
grep -RInE 'Purpose: define the product concern|starter content|A core Chaser agent concept|future citation needed|repeated generic layer language' docs START_HERE.md NEXT_STEPS.md HANDOVER.md || true
```

Post-pass result:

```text
All six golden JSONL files valid, 3 rows each.
5 passed in 1.20s.
Placeholder search returned no matches.
```

## Files modified by this pass

- `START_HERE.md`
- `NEXT_STEPS.md`
- `HANDOVER.md`
- `docs/00_START_HERE.md`
- `docs/01_Product/Chaser-Agent-Product-Thesis.md`
- `docs/01_Product/Chaser-Agent-Roadmap.md`
- `docs/01_Product/Chaser-Agent-17-Layer-Architecture.md`
- `docs/02_Evals/Chaser-Agent-Dataset-Plan.md`
- `docs/03_Summary_Intelligence/Chaser-Agent-Source-Summary-Spec.md`
- `docs/04_Memory/Chaser-Agent-Memory-States.md`
- `docs/05_Runtime_Adapters/Chaser-Agent-OpenClaw-Hermes-Competitor-Map.md`
- `docs/06_Skills/Chaser-Agent-Skill-System.md`
- `docs/07_Research/Chaser-Agent-Research-Register.md`
- `docs/08_Learning/Harness-Engineering-Glossary.md`

## Files created by this pass

- `docs/07_Research/ChaseOS-Website-Alignment.md`
- `logs/build/2026-06-09-spec-deepening-pass.md`

## Placeholder wording removed

The following placeholder/thin phrases were searched and removed from the active docs set:

- `Purpose: define the product concern`
- `starter content`
- `A core Chaser agent concept`
- `future citation needed`
- `repeated generic layer language`

## No implementation code changed by this pass

This pass intentionally edited Markdown/spec/log files only. It did create a local `.venv` and install dev dependencies so pytest could run. It did not edit `src/`, `scripts/`, `tests/`, provider adapters, runtime adapters, private datasets, or ChaseOS canonical docs.

Note: the working tree already showed many pre-existing tracked modifications before this pass. This build log describes the files intentionally changed during Phase 0C.

## Artifact policy decision

`Chaser_Agent_Research_Eval_Register.xlsx` should be committed as an operator-facing planning artifact because the inspected workbook contains the research register, eval families, dataset plan, repo boundary, human rubric, dashboard, and status vocabulary needed for Chaser agent development. `PACK_MANIFEST.json` should also be committed as starter-pack provenance. Keep raw private datasets out of Git.

## Strengthened specs

- Product Thesis is now useful: yes.
- Roadmap is now actionable: yes.
- 17-layer architecture is no longer generic: yes.
- Dataset Plan is now actionable: yes.
- Source Summary Spec is now concrete enough for eval harness/source-card implementation: yes.
- Memory States are now real state definitions with transitions: yes.
- Competitor Map is stronger and does not grant adapter authority: yes.
- Skill System is stronger with lifecycle/quarantine/review/eval/rollback: yes.
- Research Register is clearer as Markdown mirror of Excel: yes.
- Website alignment placeholder was created: yes.

## Remaining gaps

- Eval harness v0.2 still needs implementation.
- Source-card harness should become stronger after result-row infrastructure exists.
- Website alignment requires manual page text or screenshots before claims can be made.
- Runtime adapters remain notes/mock targets only.
- Fine-tuning remains later and requires reviewed datasets plus approval.

## Next recommended pass

```text
Eval harness v0.2 — deterministic result rows, per-family runner support, timestamped JSONL logs, and tests for id/task/passed/score/failure_reasons/output/timestamp/runner_version.
```
