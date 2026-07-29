# Visual Completion Evaluator Harness Implementation Plan

> **For Hermes:** Use test-driven-development skill for every code slice. This lane is mandatory for Chaser Agent hands-on harness engineering, but remains proof-mode until visual QA authority is separately granted.

**Goal:** Build a deterministic, review-only visual/computer-use completion evaluator that turns task evidence into smoke/eval artifacts before any live browser/computer-use, provider calls, RL, or fine-tuning.

**Architecture:** Start with a local metadata evaluator over JSONL cases. It classifies evidence as `verified_success_advisory`, `attempted_unverified`, or `failed`, records missing proof, and keeps `can_mark_complete=false`. Later visual QA can replace or augment metadata summaries with screenshot/DOM/file probes while preserving the same output contract.

**Tech Stack:** Python stdlib, pytest, JSONL golden evals, existing `chaser_agent.cli` command surface.

---

## Current truth boundary

- Chaser Agent currently has Source Card Harness V0 and ChaseOS-native review packet V0.
- Existing tests are smoke/schema unless they prove Layer 0 behavior.
- This lane intentionally does **not** activate provider/API calls, browser/computer-use runtime, MCP, private datasets, fine-tuning, canonical mutation, or production-readiness claims.
- The evaluator is advisory: it can prepare evidence and recommendations, but cannot consume approvals or mark completion.

## Implemented seed slice

### Task 1: RED — visual completion evaluator tests

**Objective:** Capture the ChaseOS proof rule in tests before implementation: screenshot-only proof is attempted/unverified; multi-source evidence is advisory success; explicit failure stays failed.

**Files:**
- Create: `tests/test_visual_completion_evaluator.py`

**Verification command:**

```bash
PYTHONPATH=src .venv/bin/python -m pytest tests/test_visual_completion_evaluator.py -q
```

**Observed RED:** failed with `ModuleNotFoundError: No module named 'chaser_agent.visual_completion'`.

### Task 2: GREEN — deterministic evaluator module and CLI

**Objective:** Implement the minimal local evaluator and `visual-eval` CLI that writes JSONL results plus a no-authority run log.

**Files:**
- Create: `src/chaser_agent/visual_completion.py`
- Modify: `src/chaser_agent/cli.py`

**Verification command:**

```bash
PYTHONPATH=src .venv/bin/python -m pytest tests/test_visual_completion_evaluator.py -q
```

**Observed GREEN:** `4 passed`.

### Task 3: Golden eval seed

**Objective:** Add a reusable JSONL eval dataset for the first visual completion cases.

**Files:**
- Create: `evals/datasets/golden/visual_completion_eval.jsonl`

**Cases:**
1. screenshot-only export -> `attempted_unverified`
2. screenshot + file + content proof -> `verified_success_advisory`
3. explicit form validation failure -> `failed`

---

## Next TDD slices

### Task 4: Add golden dataset CLI smoke test

Write a failing test that runs:

```bash
PYTHONPATH=src .venv/bin/python -m chaser_agent.cli visual-eval \
  --input evals/datasets/golden/visual_completion_eval.jsonl \
  --out logs/runs
```

Expected artifacts:
- `visual_completion_results.jsonl`
- `run_log.json`
- run log authority flags all `none`

### Task 5: Add calibration schema seed

Add a calibration JSONL shape for future visual QA:

```json
{"case_id":"...","human_label":"success|failure|uncertain","evaluator_outcome":"...","false_positive_risk":"low|medium|high","false_negative_risk":"low|medium|high"}
```

Do not implement reward correction yet. First prove we can store calibration evidence.

### Task 6: Add visual QA artifact contract

Define a future screenshot/DOM/file probe artifact schema:

```json
{
  "task_id": "...",
  "instruction": "...",
  "expected_outcome": "...",
  "screenshots": [],
  "dom_checks": [],
  "file_checks": [],
  "content_checks": [],
  "operator_review_required": true
}
```

### Task 7: Human visual QA prep

When Chase is ready to manually test visual QA, use this evaluator as the contract:

1. Capture screenshot/DOM/file evidence manually or through a bounded local probe.
2. Convert evidence into the JSONL case format.
3. Run `visual-eval`.
4. Compare evaluator outcome to Chase's human label.
5. Record false positives/false negatives before trusting automation.

---

## Acceptance criteria before live visual QA

- Focused visual evaluator tests pass.
- Full repo test suite passes or unrelated failures are documented.
- Golden dataset validates as JSONL.
- CLI run creates artifacts under `logs/runs/`.
- Every run log keeps provider/browser/fine-tuning/canonical authority closed.
- Human-labelled calibration cases exist before model/VLM evaluation is introduced.

## Explicit non-goals for this slice

- No PPO/RL.
- No model training.
- No VLM provider call.
- No autonomous browser/computer control.
- No canonical ChaseOS mutation.
- No completion authority without operator/Gate review.
