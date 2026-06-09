# Chaser agent Dataset Plan

## Current reset classification

Existing `evals/datasets/golden/*.jsonl` files are safe starter examples and smoke/schema data. They are not yet product-quality eval datasets because Layer 0 and V0 behavior are only now being defined.

## JSONL explanation

JSONL stores one JSON object per line. It is good for examples, result logs, regression rows, review data, and future training candidates. JSONL is a format, not proof.

## Dataset classes

| Class | Purpose | Commit policy |
|---|---|---|
| Smoke/schema toy rows | Prove parsing and shape. | Commit if public/safe. |
| Layer 0 contract rows | Prove behavior boundaries. | Next after V0 loop. |
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

## Privacy rules

Never commit secrets, raw personal logs, credentials, private datasets, account data, wallet/trading private data, cookies, tokens, or proprietary material without approval.

## Human review remains mandatory

Human review is required before any row becomes product-quality data or future training data.

## Fine-tuning boundary

Fine-tuning comes only after reviewed failure data, contract evals, privacy checks, and operator approval. Phase 0C does not create training data.
