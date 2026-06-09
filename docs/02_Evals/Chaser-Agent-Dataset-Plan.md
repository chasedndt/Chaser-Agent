# Chaser agent Dataset Plan

Datasets are the evidence base for Chaser agent behavior. They must be small, reviewable, privacy-aware, and connected to evals before they become candidates for training.

## Why JSONL

JSONL stores one JSON object per line. It is easy to append, diff, validate, stream, sample, and split into train/eval sets later. Chaser agent uses JSONL for golden eval cases, result logs, human-review rows, and future fine-tuning candidates.

## Dataset classes

| Class | Purpose | Location | Commit policy |
|---|---|---|---|
| Safe toy datasets | Tiny synthetic examples for scaffolding and smoke tests. | `evals/datasets/golden/*.jsonl` while toy-sized. | Commit allowed. |
| Public golden datasets | Scrubbed public examples with stable expected behavior. | `evals/datasets/golden/`. | Commit allowed after review. |
| Private operator datasets | Sensitive tasks, private notes, market examples, or user-specific logs. | `evals/datasets/private/` or local ignored path. | Never commit raw private data. |
| Regression datasets | Failure cases that must not reappear. | `evals/datasets/regression/` when created. | Commit only if public/scrubbed. |
| Fine-tuning candidates | High-quality reviewed input/output examples. | future `datasets/training_candidates/` or private store. | Do not create yet; strict review required. |

## Folder structure

```text
evals/datasets/golden/      # public/scrubbed golden eval rows
evals/datasets/private/     # ignored/private guidance only, no raw dumps
evals/datasets/regression/  # future scrubbed failure cases
evals/rubrics/              # YAML or Markdown scoring rubrics
logs/runs/                  # timestamped eval outputs, no secrets
```

## Required JSONL fields

Minimum fields for eval rows:

- `id`: stable case identifier;
- `task`: eval family or task name;
- `input`: source text, prompt, or structured source packet;
- `expected`: required output properties, not always exact text;
- `rubric`: rubric identifier or scoring notes;
- `privacy`: public, scrubbed, private, sensitive, or secret;
- `failure_modes`: known ways the system could fail;
- `human_review_required`: boolean for judgement-heavy cases.

Result rows should include:

- `id`;
- `task`;
- `passed`;
- `score`;
- `failure_reasons`;
- `output`;
- `timestamp`;
- `runner_version`.

## Privacy rules

Never commit:

- `.env` files, credentials, tokens, cookies, SSH keys, API keys;
- raw personal logs or private Discord/Telegram/DM exports;
- account-specific trading data, wallet details, PnL, or private business records;
- proprietary docs without explicit approval;
- screenshots or browser captures containing private identifiers unless scrubbed and approved.

## Human review labels

Use these labels in registers and future review rows:

- `needs_source_review`;
- `accepted_signal`;
- `rejected_signal`;
- `converted_to_spec`;
- `converted_to_eval`;
- `dataset_candidate`;
- `training_candidate_later`;
- `archived`.

## Deletion / removal process

If a dataset row is unsafe, wrong, private, or no longer allowed:

1. remove it from the JSONL file;
2. record why in the build log or private review note;
3. add a scrubbed replacement if the eval coverage is still needed;
4. never preserve the sensitive value in Git history intentionally;
5. rotate credentials if a secret was ever committed.

## Connection to future LoRA / PEFT / fine-tuning

Fine-tuning candidates come only after:

- source data is classified;
- evals catch known failures;
- examples are human-reviewed;
- privacy rules are satisfied;
- training/eval splits are planned;
- an operator approves the fine-tuning decision.

Phase 0C does not create training data.
