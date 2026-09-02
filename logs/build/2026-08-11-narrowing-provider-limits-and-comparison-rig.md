# 2026-08-11 — Narrowing the Provider Limits + Comparison Rig

## Trigger

Chase asked for the three stated limits of a fake-only provider boundary to be patched so only the irreducible residue remains, and for the next logical step (model-assisted path plus comparison harness) to be built in the same pass.

## Limit 1 — failure modes nobody imagined

**Defect in the first design:** containment leaned on `detect_governance_claims()`, which is regex/pattern based. A blacklist is enumerable and therefore always incomplete.

**Patch:** `MERGE_WRITABLE_KEYS` whitelist plus `assert_only_whitelisted_changes()` — a full recursive diff of the artifact tree before/after merge that raises `GovernanceDrift` when any change lands outside the three writable keys, including keys nobody anticipated. Pattern detection demoted to advisory operator labelling.

**Plus property-based fuzzing:** 400 seeded-random payloads assembled from hostile fragments, forged JSON, unicode direction overrides, null bytes, format-string and path-traversal strings, oversized repeats, and empty input. The invariant is asserted for every one, and input artifacts are proven unmutated.

**Residue:** a novel attack can still produce misleading *candidate text*. Containment prevents state change; human review remains the defence against being wrong.

## Limit 2 — cost, latency, rate limits

**Patch:** new `providers/budget.py`.

- `BudgetPolicy`: prompt characters, output tokens, deadline seconds, requests per run, projected cost ceiling.
- `BudgetLedger.check_before_send()` refuses ahead of the call; tests assert `adapter.request_count == 0` after refusal, so a breach costs nothing.
- `enforce_deadline()` converts a late reply into `timeout` on the harness side — a slow provider is never a success because bytes eventually arrived.
- Per-call usage records (estimated tokens, latency, cost) and run totals stamped `token_counts_are_estimates: true`.
- Fake extended with simulated `latency_ms`, token counts, `ScriptedReply.slow()`, and `ScriptedReply.rate_limited()`; `rate_limited` added to `ProviderStatus`.

**Residue:** the real price/speed/limits are unknown until a live call — but that is now a number to fill in, not a system to build.

## Limit 3 — unknown model quality

**Patch:** `evals/comparison.py` scores model-assisted output against the deterministic baseline — statement-level grounding against source vocabulary, unsupported-statement count, uncertainty preservation, governance violations, composite `quality_score`. Governance violations or unusable output force zero.

**The calibration is the deliverable:** three outputs of *known* quality (well-grounded, partly grounded, wholly fabricated) must be ranked in that order by the ruler. An uncalibrated scale would make any later measurement of a real model meaningless.

**Residue:** whether a real model is good is unknowable until called. Whether we can tell is no longer unknown.

## Next logical step, built

`providers/assisted_review.py` — `run_assisted_review()` builds deterministic artifacts first, then treats provider output as strictly additive. Refused envelope, breached budget, timeout, refusal, or malformed output all leave the deterministic result standing with `degraded: true`. Graceful degradation is structural rather than error handling that might be forgotten.

## Tests

- `tests/test_provider_invariants_and_budget.py` — 20 tests (containment, fuzzing, ceilings, deadline, degradation).
- `tests/test_assisted_review_comparison.py` — 11 tests (grounding primitives, calibration ordering, hostile output scoring zero).

Module-scoped baseline fixture: `build_run_log` shells out to git, so the baseline is built once and deep-copied per iteration.

## Authority boundary

No live provider, no credential, no network path, no training, no ChaseOS canonical mutation, no merge to `main`.

## Verification

```bash
PYTHONPATH=src .venv/bin/python -m pytest -q
```

## Next

Remaining work before a live provider is a dataset question, not an engineering one: reviewed AI-engineering examples for the comparison to run on, and contract-eval coverage.
