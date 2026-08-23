# Chaser Agent Dataset Plan

## Current reset classification

Existing `evals/datasets/golden/*.jsonl` files are safe starter examples and smoke/schema data. Layer 0 and P0.1 behavior are now defined and deterministically tested, but these rows are still not product-quality datasets because they lack human-reviewed outputs and task-specific scoring depth.

`evals/datasets/contract/layer0_contract_seed.jsonl` now contains five executable public-safe cases for each of the six initial Layer 0 contract families: 30 cases and 154 artifact assertions. These are Codex-authored cases with `human_review_required: true` and `provenance.review_status: pending_operator_review`; they provide structural family depth but are not operator-reviewed golden data.

`evals/datasets/case_studies/` holds workflow episodes that model goals, context, evidence, dependencies, decisions, capabilities, actions, artifacts, proof, recovery, and handoff. The first MarginFlip-derived public-safe episode is structurally executable but remains `pending_operator_review` and `training_eligible: false`.

## JSONL explanation

JSONL stores one JSON object per line. It is good for examples, result logs, regression rows, review data, and future training candidates. JSONL is a format, not proof.

## Dataset classes

| Class | Purpose | Commit policy |
|---|---|---|
| Smoke/schema toy rows | Prove parsing and shape. | Commit if public/safe. |
| Layer 0 contract rows | Execute artifact assertions against behavior boundaries. | Current 30 remain pending operator review; commit reviewed status only after real review. |
| Workflow episode rows | Evaluate how an agent navigates dependencies, evidence, authority, artifacts, proof, recovery, and handoff. | Commit scrubbed candidates as pending; promote only after operator review. |
| Product-quality golden rows | Human-reviewed examples of useful behavior. | Later after review. |
| Private operator rows | Sensitive examples. | Never commit raw. |
| Regression rows | Past failures that must not return. | Commit only if scrubbed. |
| Fine-tuning candidates | Reviewed examples for possible training. | Not active. |

## Required fields for future contract rows

- `id`
- `task`
- `input`
- `expected_behavior`
- `forbidden_behavior`
- `privacy`
- `human_review_required`
- `failure_modes`

## Required workflow episode fields

- `schema_version`
- `episode_id`
- `domain`
- `goal`
- `context`
- `source_evidence`
- `capabilities`
- `candidate_reference_steps`
- `decision_points`
- `expected_artifacts`
- `forbidden_outcomes`
- `recovery_cases`
- `scoring`
- `provenance`

Split workflow data by source lineage, not by randomly distributing near-duplicate rows. Private operator cases stay local; public-safe variants require scrubbing, review, provenance, and licence checks.

## Privacy rules

Never commit secrets, raw personal logs, credentials, private datasets, account data, wallet/trading private data, cookies, tokens, or proprietary material without approval.

## Human review remains mandatory

Human review is required before any row becomes product-quality data or future training data.

## Fine-tuning boundary

Fine-tuning comes only after reviewed failure data, contract evals, privacy checks, and operator approval. P0.1 does not create training data.
