
# Chaser agent Handover

## Current phase

Source Card Harness V0 implemented. The repo is ready for **Source Card Harness Review** or **Contract Eval Seeds**.

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

Source Card Harness V0 validation:

```text
.venv/bin/python -m pytest -q        # all tests pass
.venv/bin/python -m scripts.validate_jsonl evals/datasets/golden/*.jsonl  # all six valid, 3 rows each
```

Run the harness:

```bash
.venv/bin/python -m chaser_agent.cli source-card --input examples/sources/toy_website_design_note.md --out logs/runs
```

The command prints a unique run folder under `logs/runs/` with `source_card.json`, `claims_table.json`, `evidence_snippets.json`, `uncertainty_labels.json`, `action_candidates.json`, `memory_candidates.json`, `human_review_packet.json`, and `run_log.json`. These are deterministic local review artifacts, not LLM/provider output and not canonical truth.

Detailed pass record: `logs/build/2026-06-09-source-card-harness-v0.md`.

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

**Source Card Harness Review** or **Contract Eval Seeds.** Review the deterministic Source Card Harness V0 artifacts first, then seed contract evals from that behavior. Do not start eval harness v0.2, fine-tuning, provider calls, broad adapters, MCP tooling, browser runtime, private datasets, or ChaseOS canonical mutation before the harness output has been reviewed.
