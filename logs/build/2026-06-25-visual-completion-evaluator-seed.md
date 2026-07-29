# 2026-06-25 — Visual Completion Evaluator Seed

## Runtime

Hermes Optimus under ChaseOS / Chaser Agent approval-gated development lane.

## Trigger

Chase marked the autonomous computer-use evaluation paper as mandatory implementation for ChaseOS / Chaser Agent hands-on harness engineering, with smoke tests/evals and future visual QA prep.

## Implemented

- Added RED/GREEN tests for visual completion evaluation.
- Added deterministic provider-free evaluator module: `src/chaser_agent/visual_completion.py`.
- Added CLI command: `chaser-agent visual-eval` / `python -m chaser_agent.cli visual-eval`.
- Added golden eval seed: `evals/datasets/golden/visual_completion_eval.jsonl`.
- Added implementation plan: `docs/plans/2026-06-25-visual-completion-evaluator-harness.md`.
- Added eval doc: `docs/02_Evals/Chaser-Agent-Visual-Completion-Evaluator.md`.

## Authority boundary

No provider calls, no browser/computer-use activation, no fine-tuning, no approval consumption, no canonical mutation, no public/customer/payment action.

## Verification

Focused test:

```bash
PYTHONPATH=src .venv/bin/python -m pytest tests/test_visual_completion_evaluator.py -q
```

Result:

```text
4 passed
```

JSONL validation:

```bash
.venv/bin/python -m scripts.validate_jsonl evals/datasets/golden/*.jsonl
```

Result:

```text
evals/datasets/golden/visual_completion_eval.jsonl: valid JSONL (3 rows)
```

CLI smoke:

```bash
rm -rf /tmp/chaser-visual-eval-smoke && \
PYTHONPATH=src .venv/bin/python -m chaser_agent.cli visual-eval \
  --input evals/datasets/golden/visual_completion_eval.jsonl \
  --out /tmp/chaser-visual-eval-smoke
```

Result folder:

```text
/tmp/chaser-visual-eval-smoke/visual-completion-eval-20260625T222010Z-090e79a1cb
```

Generated:

```text
run_log.json
visual_completion_results.jsonl
```

Full repo tests:

```bash
PYTHONPATH=src .venv/bin/python -m pytest -q
```

Result:

```text
27 passed in 15.22s
```

## Next

- Add calibration schema and human-labelled visual QA cases.
- Prepare manual screenshot/DOM/file evidence capture workflow when Chase is ready for visual QA testing.
