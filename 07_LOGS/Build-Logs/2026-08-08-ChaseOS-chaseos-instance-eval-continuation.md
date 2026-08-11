# ChaseOS Instance Eval Continuation

- Date: 2026-08-08
- Runtime: Codex
- Session descriptor: `2026-08-08_chaseos-instance-eval-continuation`
- Branch: `codex/2026-08-08-chaseos-instance-eval-continuation`
- Phase / pass: Chaser Agent Phase 2, Session 3 contract-eval seed
- Status: PARTIAL — implementation complete for this seed pass; operator label review remains open

## Task summary

Continue from the 2026-08-02 ChaseOS instance-eval thesis by turning the approved next technical slice into executable code: run the real deterministic source-card builder, assert on artifact fields, and seed the six initial Layer 0 contract families.

## Repo-truth baseline

- Phase 1 Source Card Harness V0 was implemented and deterministic.
- The existing eval runner enforced text `must_include` / `must_not_include` only.
- `Chaser-Agent-Contract-Eval-Design.md` specified artifact-field assertions but had no runner or cases.
- Four pre-existing untracked design/research files were present and preserved as user work.
- Source-trust grading and per-instance eval inventories were research proposals, not implemented behavior.

## Files read

- `README.md`, `HANDOVER.md`, `NEXT_STEPS.md`
- Layer 0, Roadmap, As-Built Map, Contract Eval Design, Eval Harness, Dataset Plan, Eval Families, Safety Governance Evals
- V0 Source Card Schema, social publishing direction, ChaseOS website alignment, instance-eval thesis
- source-card builder, artifact/run-log code, CLI, eval runner/rubric, schemas, current tests and latest relevant build log

## Files modified

- `README.md`
- `HANDOVER.md`
- `NEXT_STEPS.md`
- `docs/01_Product/Chaser-Agent-As-Built-Map.md` (pre-existing untracked user work, updated in place)
- `docs/01_Product/Chaser-Agent-Roadmap.md`
- `docs/02_Evals/Chaser-Agent-Eval-Harness.md`
- `docs/02_Evals/Chaser-Agent-Dataset-Plan.md`
- `docs/02_Evals/Chaser-Agent-Contract-Eval-Design.md`
- `docs/research/2026-08-02-chaseos-instance-eval-thesis.md`
- `src/chaser_agent/cli.py`

## Files created

- `src/chaser_agent/evals/contract_runner.py`
- `evals/datasets/contract/layer0_contract_seed.jsonl`
- `tests/test_contract_eval_runner.py`
- this build log and the linked documentation-history, daily, and agent-activity records/indexes

## Tests run

```powershell
$env:PYTHONPATH = 'C:\Users\chaseos\Documents\Projects\chaser-agent\src'
python -m pytest tests/test_eval_runner_smoke.py tests/test_source_card_harness.py -q
python -m pytest tests/test_contract_eval_runner.py tests/test_eval_runner_smoke.py tests/test_source_card_harness.py -q
python -m chaser_agent.cli contract-eval --input evals/datasets/contract/layer0_contract_seed.jsonl --out <unique-temp-result>.jsonl
python -m pytest -q
python -m pytest -q --ignore=tests/test_weekly_research_intake_config.py
python -m scripts.validate_jsonl <all-golden-jsonl-paths> evals/datasets/contract/layer0_contract_seed.jsonl
python -m compileall -q src/chaser_agent
git diff --check
```

```bash
PYTHONPATH=src .venv/bin/python -m pytest tests/test_weekly_research_intake_config.py -q
```

## Test results

- Baseline targeted run with documented `PYTHONPATH`: 4 passed.
- Contract + regression targeted run: 8 passed.
- Contract CLI: exit 0; all 6 cases passed all 28 assertions.
- Deliberate mutation test: changing `promotion_status` to `approved_elsewhere` caused a named `no_auto_promotion` failure with the bad observed value.
- Native full suite: 31 passed, 2 failed due to an existing Windows/POSIX path-key mismatch in `weekly_research_intake_dry_run.py`.
- The intended WSL run of the affected weekly-research file: 6 passed.
- Final native suite excluding only that POSIX-specific file: 27 passed.
- Together, the final native 27 and WSL 6 cover all 33 collected tests in their working environments.
- All 7 golden datasets and the 6-row contract dataset passed JSONL validation.
- Python compile and `git diff --check` passed. Git reported only expected LF-to-CRLF checkout warnings for tracked Markdown/Python files.

## Verification evidence

- The runner calls `build_source_card_artifacts`, not the placeholder summary shim.
- Results contain the `EvalResult` core fields plus `layer0_clause` and assertion-level details.
- Foreign-key assertions resolve claim/evidence/action references.
- Evidence text is checked verbatim against the case input.
- Injection text cannot change review, promotion, approval, or provider-call fields.
- Contract cases are stamped `human_review_required: true` and `pending_operator_review`.

## What changed

- Added a separate contract runner so smoke/schema datasets retain their old meaning.
- Added field assertion operators for equality, forbidden equality, minimum length, reference resolution, evidence grounding, and scoped forbidden text.
- Added a fail-closed CLI command that returns non-zero when any case fails.
- Added one public-safe wiring case for each initial Layer 0 family.
- Updated current-truth docs from “designed, not built” to “PARTIAL seed implementation.”

## What did not change

- No provider, API, adapter, MCP, browser, computer-use, public action, memory promotion, or ChaseOS canonical mutation was enabled.
- The original text eval runner and golden smoke/schema datasets were not reclassified or silently changed.
- Source-trust grading, per-instance packs, operator UI, product-quality scoring, and training remain unbuilt.
- The pre-existing social-publishing plan remained untouched; the three relevant untracked thesis/design/as-built truth surfaces were updated in place.

## What remains unverified

- Operator acceptance of the six labels, failure modes, and expected behaviors.
- Coverage: one case per family is only seed wiring, not the target of at least five reviewed cases.
- Metamorphic, replay, and real-failure regression corpora.
- General source-trust registry, Admiralty grading, policy floors, and per-instance overrides.

## Process and storage closeout

- C: free space before build/test work: 13.88 GiB (5.84%).
- A timed-out WSL baseline left exact owned PIDs 12916 and 27916; both were stopped by exact PID and verified gone before continuing.
- No server, browser, benchmark, model worker, or listener was started.
- `chaseos audit storage --apply --require-headroom`: HEALTHY, 13.704 GiB free, 0 superseded candidates, 0 deleted; current/rollback packages retained.
- C: free space after closeout: 13.70 GiB (5.76%).
- Final read-only process check found no WSL/Python/pytest process owned by this repo session.
- One small CLI result remains under the OS temp directory because the exact-file cleanup command was blocked before execution by shell policy; it is not in the repo and contains only public-toy assertion results.

## Remaining open loops

1. Operator-review the six seed rows.
2. Expand each family toward at least five reviewed cases.
3. Add regression, injection-corpus, metamorphic, and replay cases.
4. Merge externally expanded research before implementing source-trust grades.

## Next recommended pass

Operator review of `evals/datasets/contract/layer0_contract_seed.jsonl`, followed by a bounded family-expansion pass. Do not combine that review with live provider/tool authority.

## Linked records

- [Documentation history](../../99_ARCHIVE/Documentation-History/2026-08-08_chaseos-instance-eval-continuation.md)
- [Daily note](../Daily/2026-08-08.md)
- [Agent activity](../Agent-Activity/2026-08-08-codex-chaseos-instance-eval-continuation.md)
- [Contract eval design](../../docs/02_Evals/Chaser-Agent-Contract-Eval-Design.md)
- [Instance eval thesis](../../docs/research/2026-08-02-chaseos-instance-eval-thesis.md)
