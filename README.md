# Chaser agent

**Chaser agent** is a governed, eval-backed AI runtime and content-intelligence system derived from ChaseOS.

ChaseOS remains the parent operating system, governance layer, memory/control plane, and current source of truth. The `chaser-agent` repository is the focused product/runtime implementation and eval lab where source summaries, memory candidates, adapter notes, and harness behavior can be developed without mutating ChaseOS canonical truth.

## Current status
This repository is a scaffold only. It contains starter documentation, safe toy JSONL golden datasets, a minimal importable Python package, a deterministic source-card stub, and smoke tests. It does **not** claim production implementation, model training, autonomous operation, external API integration, or canonical writeback.

## First local commands
```bash
cd /mnt/c/Users/chaseos/Documents/Projects/chaser-agent
python -m scripts.validate_jsonl evals/datasets/golden/source_card_summary_eval.jsonl
python -m pytest -q
```
If `pytest` is missing, create a virtual environment first and install dependencies inside it only:
```bash
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -e .[dev]
python -m pytest -q
```

## Repo safety rules
- Do not commit `.env`, secrets, credentials, private datasets, or raw personal logs.
- Do not push to GitHub without explicit operator approval.
- Do not mutate ChaseOS canonical docs from this repository.
- Roadmap, memory, skill, or policy changes are suggestions until reviewed.

## Eval-first development
A Chaser agent feature is not considered real until it has an eval, a failure mode, and a regression check. Fine-tuning, LoRA, PEFT, and model editing come only after golden datasets exist, eval failures are understood, and human review confirms patterns.
