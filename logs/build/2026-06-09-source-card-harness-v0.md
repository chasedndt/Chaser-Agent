# Source Card Harness V0 Build Log — 2026-06-09

## Scope

Implemented Phase 1 — Source Card Harness V0. This pass proves the deterministic local V0 artifact loop exists without LLMs, providers, external APIs, Hermes/OpenClaw adapters, MCP, browser/computer-use, private datasets, fine-tuning/LoRA/PEFT/model training, ChaseOS canonical mutation, automatic memory promotion, or automatic action execution.

This was not an eval harness v0.2 pass.

## Branch

- Branch started on: `main`
- Branch ended on: `main`

## Required baseline checks before editing

```text
git status --short --branch
## main...origin/main

git branch --show-current
main

git log --oneline -5
f9f4666 docs: define Chaser agent V0 blueprint
0df3834 docs: align Layer 0 with control-plane learning reset
29e6b16 docs: define Chaser agent Layer 0 and V0 foundation
604bf22 chore: retain starter pack research artifacts
5a56296 merge: bring spec deepening onto main

git stash list
stash@{0}: On docs/spec-deepening-pass: pre-layer0-reset-uncommitted-work-2026-06-09

.venv/bin/python -m pytest -q
5 passed in 0.41s

.venv/bin/python -m scripts.validate_jsonl evals/datasets/golden/*.jsonl
all six golden JSONL files valid, 3 rows each
```

Stash note: `stash@{0}` existed and was not applied, deleted, or modified.

## Files created

- `examples/sources/toy_website_design_note.md`
- `src/chaser_agent/source_card.py`
- `src/chaser_agent/run_artifacts.py`
- `tests/test_source_card_harness.py`
- `logs/build/2026-06-09-source-card-harness-v0.md`

## Files modified

- `README.md`
- `START_HERE.md`
- `NEXT_STEPS.md`
- `HANDOVER.md`
- `docs/00_START_HERE.md`
- `docs/01_Product/Chaser-Agent-Roadmap.md`
- `docs/03_Summary_Intelligence/Chaser-Agent-Source-Summary-Spec.md`
- `src/chaser_agent/cli.py`
- `src/chaser_agent/schemas.py`
- `src/chaser_agent/summary/source_card.py`

## Implementation notes

- Added `python -m chaser_agent.cli source-card --input ... --out ...`.
- The command accepts local safe text/markdown files and an output root.
- It creates a unique run folder under the output root.
- It prints the run folder path.
- It exits nonzero with `error: input file not found: ...` if the input path is missing.
- It writes deterministic JSON artifacts only.
- It keeps older summary smoke-test imports working through `src/chaser_agent/summary/source_card.py`.

## Harness command used

```bash
.venv/bin/python -m chaser_agent.cli source-card --input examples/sources/toy_website_design_note.md --out logs/runs
```

## Example run folder created

```text
logs/runs/source-card-20260609T174632z-toy-website-design-note-1e92029ac4
```

## Output artifact paths

```text
logs/runs/source-card-20260609T174632z-toy-website-design-note-1e92029ac4/source_card.json
logs/runs/source-card-20260609T174632z-toy-website-design-note-1e92029ac4/claims_table.json
logs/runs/source-card-20260609T174632z-toy-website-design-note-1e92029ac4/evidence_snippets.json
logs/runs/source-card-20260609T174632z-toy-website-design-note-1e92029ac4/uncertainty_labels.json
logs/runs/source-card-20260609T174632z-toy-website-design-note-1e92029ac4/action_candidates.json
logs/runs/source-card-20260609T174632z-toy-website-design-note-1e92029ac4/memory_candidates.json
logs/runs/source-card-20260609T174632z-toy-website-design-note-1e92029ac4/human_review_packet.json
logs/runs/source-card-20260609T174632z-toy-website-design-note-1e92029ac4/run_log.json
```

The run artifacts are intentionally ignored by `.gitignore` through `logs/runs/*`; the build log records their paths as evidence.

## Artifact checks

- All artifact files existed in the example run folder.
- All artifact files parsed as JSON.
- `source_card.json` contained all required fields.
- `review_status`: `pending_review`
- `promotion_status`: `not_promoted`
- `trust_state`: `unreviewed`
- `privacy_class`: `public_toy`
- `run_log.json` recorded:
  - `provider_calls`: `none`
  - `external_api_calls`: `none`
  - `runtime_adapters`: `none`
  - `mcp_activation`: `none`
  - `browser_or_computer_use`: `none`
  - `fine_tuning_or_training`: `none`

## Tests after implementation

Focused TDD test after implementation:

```text
.venv/bin/python -m pytest tests/test_source_card_harness.py -q
2 passed in 1.57s
```

Full final validation is recorded in the final handover after this build log is written.

## What was not implemented

- No eval harness v0.2.
- No LLM/provider/API calls.
- No OpenAI/Gemini/Ollama/provider routing.
- No Hermes/OpenClaw adapter activation.
- No MCP activation.
- No browser/computer-use runtime.
- No fine-tuning, LoRA, PEFT, or model training.
- No private dataset ingestion.
- No ChaseOS canonical mutation.
- No automatic memory promotion.
- No automatic action execution.
- No production-readiness claim.

## Remaining gaps

- Source-claim extraction is simple keyword/sentence matching, not semantic intelligence.
- Contradiction detection is placeholder/empty unless future deterministic logic is added.
- Human review packet scores are intentionally unset pending operator review.
- Contract evals have not yet been seeded from the generated artifacts.
- Artifact schemas are JSON-shape practical implementations, not a strict JSON Schema file yet.

## Next recommended pass

**Source Card Harness Review** or **Contract Eval Seeds**. Review this deterministic artifact output first, then seed Layer 0 contract eval cases that catch unsupported claims, missing uncertainty, unsafe action phrasing, memory auto-promotion, and canonical-promotion overclaims. Do not jump to provider calls, runtime adapters, MCP, browser/computer-use, or fine-tuning next.
