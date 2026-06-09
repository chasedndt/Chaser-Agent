# Chaser agent

**Chaser agent** is a governed, source-intelligence and harness-development repo derived from ChaseOS.

ChaseOS remains the parent operating system/control plane and canonical governance owner. Chaser agent is the focused product/runtime implementation and learning/eval lab. It is not a foundation model, not production-ready autonomy, and not a replacement for ChaseOS canonical truth.

## Current phase

Current work has completed **Phase 1 — Source Card Harness V0**:

1. Layer 0 Behaviour Contract defines the product constitution;
2. V0 Definition and Blueprint define the first review-first loop;
3. Source Card Harness V0 runs locally and deterministically without LLM/provider/API calls;
4. generated artifacts are review-only and land under `logs/runs/<run_id>/`;
5. current JSONL files remain smoke/schema unless they directly prove Layer 0 behavior;
6. the next pass should be Source Card Harness Review or Contract Eval Seeds, not provider/runtime/MCP/fine-tuning work.

## First useful V0 loop

```text
safe source input
→ source card
→ claims
→ uncertainty
→ action candidates
→ memory candidates
→ human review
→ no automatic canonical promotion
```

## Repo safety rules

- Do not commit `.env`, secrets, credentials, private datasets, or raw personal logs.
- Do not push without explicit operator approval.
- Do not mutate ChaseOS canonical docs from this repository.
- Do not activate provider/API/browser/runtime adapters by default.
- Do not claim production readiness.

## Local verification

```bash
cd /mnt/c/Users/chaseos/Documents/Projects/chaser-agent
.venv/bin/python -m scripts.validate_jsonl evals/datasets/golden/*.jsonl
.venv/bin/python -m pytest -q
```

## Run Source Card Harness V0

```bash
cd /mnt/c/Users/chaseos/Documents/Projects/chaser-agent
.venv/bin/python -m chaser_agent.cli source-card --input examples/sources/toy_website_design_note.md --out logs/runs
```

The command prints a unique run folder containing `source_card.json`, `claims_table.json`, `evidence_snippets.json`, `uncertainty_labels.json`, `action_candidates.json`, `memory_candidates.json`, `human_review_packet.json`, and `run_log.json`. Outputs are deterministic, local, and review-only.

## Start reading

Read `START_HERE.md`, then `docs/00_START_HERE.md`.
