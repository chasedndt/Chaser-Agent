# 2026-08-02 — Eval Runner Forbidden-Phrase Enforcement

## Trigger

Session 2 (eval system deep dive) of the multi-session harness build. While walking the eval runner against the golden datasets, found that every golden JSONL row defines `expected.must_not_include`, but `evals/runner.py` never read the field — forbidden-behavior checks were silently unenforced. This is a live instance of the repo's own warning that "JSONL is not proof": the dataset *looked* like it tested forbidden output, and nothing did.

## RED observed

New test `test_eval_runner_fails_case_when_forbidden_phrase_appears`: a case whose output contains the literal phrase "automatic promotion" with `must_not_include: ["automatic promotion"]` returned `passed=True, score=1.0` before the fix.

## Implemented

- `evals/rubric.py`: added `find_forbidden_phrases(output_text, must_not_include)`.
- `evals/runner.py`: forbidden hit ⇒ `passed=False`, `score=0.0`, and the offending phrases named in `notes`.
- Kept the existing `requires_uncertainty_label` demotion after the forbidden check so both failure causes stack.

## Authority boundary

No provider calls, no adapters, no canonical mutation, no approval consumption. Deterministic local eval logic only.

## Verification

```bash
PYTHONPATH=src .venv/bin/python -m pytest tests/test_eval_runner_smoke.py -q
PYTHONPATH=src .venv/bin/python -m pytest -q
```

RED confirmed before fix (1 failed), GREEN after (full suite result recorded in commit).

## Note for the contract-eval pass

The fix enforces forbidden *phrases in output text*. Contract evals (roadmap Phase 2) need the stronger form from the Dataset Plan: `forbidden_behavior` (e.g. a `promotion_status` other than `not_promoted`, a missing uncertainty label, an action without `requires_approval`) checked against artifact *fields*, not just text. This pass closes the text-level hole only.
