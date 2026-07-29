# Chaser Agent Visual Completion Evaluator

## Purpose

The Visual Completion Evaluator is the first deterministic smoke/eval seed for future Chaser Agent visual QA and computer-use completion verification.

It exists because screenshot/button/file-presence claims alone are not enough to report a task complete. The evaluator classifies collected evidence while preserving ChaseOS authority boundaries.

## Current implementation

Command:

```bash
PYTHONPATH=src .venv/bin/python -m chaser_agent.cli visual-eval \
  --input evals/datasets/golden/visual_completion_eval.jsonl \
  --out logs/runs
```

Outputs in a unique run folder:

- `visual_completion_results.jsonl`
- `run_log.json`

## Outcome vocabulary

| Outcome | Meaning |
|---|---|
| `verified_success_advisory` | Visual and non-visual evidence support the expected outcome, but the evaluator still cannot mark completion. |
| `attempted_unverified` | The agent/workflow may have attempted the task, but evidence is insufficient. Screenshot-only evidence lands here. |
| `failed` | Evidence explicitly indicates task failure. |

## Authority boundary

The evaluator is always review-only in the current slice:

- provider calls: none
- browser/computer-use: none
- fine-tuning: none
- approval consumption: none
- canonical mutation: none
- completion authority: none

`authority.can_mark_complete` remains `false` even for `verified_success_advisory`.

## Relation to the research paper

The paper *Reinforcement Learning for Computer-Use Agents with Autonomous Evaluation* argues that autonomous GUI evaluators can become useful reward signals only when evaluator error is measured and corrected.

Chaser Agent adopts the safer first step:

1. collect evidence;
2. classify the evidence deterministically;
3. preserve missing-proof reasons;
4. keep human/operator review required;
5. later add calibration cases before any model/VLM evaluator is trusted.

## Hands-on harness engineering path

1. Build deterministic metadata evaluator. ✅
2. Add golden JSONL cases. ✅
3. Add smoke tests and CLI artifacts. ✅
4. Add calibration schema and human labels. Next.
5. Add manually captured visual QA evidence. Next when Chase is ready to test.
6. Only later consider VLM evaluation, confidence calibration, or reward correction.
