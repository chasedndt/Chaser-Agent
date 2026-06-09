# Start Here — Chaser agent

Chaser agent is the first standalone development lane for the Chaser agent product/runtime and eval lab.

## Current phase

**Phase 0C — Spec Deepening + Repo Truth Pass.**

The repo now has scaffold code, toy JSONL eval datasets, starter skills, tests, and expanded specification docs. It is still not production autonomy, not a provider/API integration, not a fine-tuning project, and not a ChaseOS canonical-truth owner.

## First thing to read

1. `README.md` — repo purpose and safety rules.
2. `NEXT_STEPS.md` — current build queue.
3. `docs/01_Product/Chaser-Agent-Product-Thesis.md` — product framing.
4. `docs/01_Product/Chaser-Agent-17-Layer-Architecture.md` — full layer map and status labels.
5. `docs/03_Summary_Intelligence/Chaser-Agent-Source-Summary-Spec.md` — first product wedge.
6. `docs/02_Evals/Chaser-Agent-Dataset-Plan.md` — dataset/privacy/eval rules.

## First build wedge

Do not try to implement all 17 layers at once. The first real build remains:

```text
input source
→ source card
→ claims
→ evidence snippets
→ uncertainty labels
→ actions
→ memory candidates
→ JSONL eval
→ human review
→ run log
```

## Local verification

From WSL:

```bash
cd /mnt/c/Users/chaseos/Documents/Projects/chaser-agent
.venv/bin/python -m scripts.validate_jsonl evals/datasets/golden/*.jsonl
PYTHONPATH=. .venv/bin/python -m pytest -q
```

If `.venv` does not exist, create it with `uv venv .venv --python python3` and install `uv pip install --python .venv/bin/python -e '.[dev]'`.

## Governance reminder

ChaseOS remains the parent control plane and canonical governance owner. Chaser agent can propose, evaluate, and log. It does not silently promote canonical memory, mutate ChaseOS docs, or activate runtime authority.
