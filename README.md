# Chaser agent

**Chaser agent** is a governed, source-intelligence and harness-development repo derived from ChaseOS.

ChaseOS remains the parent operating system/control plane and canonical governance owner. Chaser agent is the focused product/runtime implementation and learning/eval lab. It is not a foundation model, not production-ready autonomy, and not a replacement for ChaseOS canonical truth.

## Current phase

Current work starts from **Layer 0**:

1. define the Layer 0 Behaviour Contract / Product Constitution;
2. define Chaser agent V0;
3. define the first-principles model;
4. align the 17 layers to Layer 0;
5. build learning/maths foundations;
6. treat current JSONL/tests as smoke/schema checks until contract evals exist.

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
PYTHONPATH=. .venv/bin/python -m pytest -q
```

## Start reading

Read `START_HERE.md`, then `docs/00_START_HERE.md`.
