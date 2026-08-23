# Build Log — Layer Architecture and Case-Study Workflow Evals

**Date:** 2026-08-23

**Branch:** `codex/2026-08-23-architecture-eval-floorwalk`

**Worktree:** `E:\ChaseOSBuilds\chaser-agent-architecture-evals-2026-08-23`

**Base:** `398f6ea`

**Status:** implementation and documentation complete in isolated worktree; operator review, commit, merge, and release remain open.

## Repo-truth delta

- The previous architecture document named all layers but repeated generic text and understated implemented memory, graph, provider-boundary, tool-boundary, and harness truth.
- The roadmap and README still reported 55 tests and six contract rows despite the current 30-case / 154-assertion Layer 0 dataset.
- Existing golden-labelled JSONL rows remained smoke/schema seeds; no schema represented a real multi-step operator workflow.
- Layer 10 HTTP/runtime work remained unbuilt and had no stage-specific fundamentals or acceptance map.

## Changes

- Rebuilt `Chaser-Agent-17-Layer-Architecture.md` as a Layer 0 + Layers 1-17 map with:
  - an 18-level pyramid;
  - end-to-end runtime/data-flow graph;
  - responsibility, durable output, fundamentals, current truth, and next proof for every layer;
  - seven engineering/learning stages with manual operator exercises;
  - explicit HTTP, rate-limit, context continuity, repair, and external-tool gates.
- Added `workflow_episode.v1` validation and deterministic workflow-trace evaluation.
- Added CLI commands `workflow-episode-validate` and `workflow-trace-eval`.
- Added a public-safe MarginFlip-derived marketing-foundation episode and candidate trace.
- Added dependency-cycle, evidence, capability, approval, artifact, completion-proof, handoff, hard-failure, and non-golden review-state checks.
- Added the case-study eval-system design, expanded eval-family taxonomy, dataset partitioning, roadmap stages, learning links, and current as-built truth.
- Added a score-ready operator floor-walk for the three existing representative runs.
- Regenerated the exact current test matrix: 9 files / 52 rows = 21 smoke/golden-labelled rows + 30 contract rows + 1 workflow episode.

## Authority and safety boundaries preserved

- No provider SDK, provider call, MCP client, tool execution, browser control, server, port, Agent Bus action, ChaseOS canonical mutation, account action, DNS change, publication, spend, credential use, memory promotion, or training occurred.
- The MarginFlip episode is `pending_operator_review`, `training_eligible: false`, and planning-only.
- The original C: worktree's visual reconstruction changes and preserved stash were not modified.
- No canonical ChaseOS files were changed.

## Verification

Passed:

```text
python -m pytest -q -p no:cacheprovider tests/test_workflow_episode_evals.py
8 passed

python -m pytest -q -p no:cacheprovider \
  tests/test_workflow_episode_evals.py \
  tests/test_test_matrix_export.py \
  tests/test_jsonl_datasets.py
11 passed

PYTHONPATH=src python -m pytest -q -p no:cacheprovider \
  tests/test_workflow_episode_evals.py \
  tests/test_test_matrix_export.py \
  tests/test_jsonl_datasets.py \
  tests/test_brand_canon_conformance.py \
  tests/test_no_private_data_tracked.py
28 passed

PYTHONPATH=src python -m pytest -q -p no:cacheprovider \
  --ignore=tests/test_weekly_research_intake_config.py
197 passed

python -m scripts.validate_jsonl <all eval dataset JSONL paths>
9 files valid / 52 rows

workflow-episode-validate
1 episode valid / 1 pending operator review / 0 reviewed

workflow-trace-eval
candidate trace passed structural score 1.0; explicitly not operator-reviewed golden data
```

Environment-limited checks:

- Windows full suite with `PYTHONPATH=src`: 201 passed, 2 failed. Both failures are pre-existing Windows path-separator behaviour in `weekly_research_intake_dry_run.py`, where `str(Path(...))` produces backslashes but the manifest lookup uses forward-slash keys.
- WSL full-suite attempt from the E: worktree exceeded the 240-second command limit before emitting buffered output. No task-owned pytest/WSL process remained afterward.

These two environment observations are not treated as passing evidence and were not repaired because they are outside this bounded architecture/eval pass.

## Operator gates and next safe action

1. Score the three existing source-review runs using `logs/review/2026-08-23-operator-floor-walk.md`.
2. Review the MarginFlip episode's dependency order, decision owners, ranking criteria, artifacts, forbidden outcomes, and recovery cases.
3. Convert corrections into immutable review records and regression rows.
4. Only then decide whether the candidate episode is eligible for a reviewed benchmark partition.
5. HTTP/server architecture remains a later Layer 10 decision and is not activated by this work.
