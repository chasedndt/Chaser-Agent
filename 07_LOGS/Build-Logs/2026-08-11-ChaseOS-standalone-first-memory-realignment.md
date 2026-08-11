# Chaser agent Standalone-First Memory Realignment

- Date: 2026-08-11
- Runtime: Codex
- Session descriptor: `2026-08-11_standalone-first-memory-realignment`
- Branch: `codex/standalone-first-memory-realignment`
- Starting commit: `57c3d836b93d1de0faeb91d50c7fb83104c0c7ae`
- Phase / pass: P0.1 standalone core, review, memory, provenance, and eval visibility
- Status: IMPLEMENTATION COMPLETE AND LOCALLY VERIFIED on the review branch; operator acceptance, merge, and release remain open

## Task summary

Continue from the operator's standalone-first master redesign handover, reconcile inherited work safely, implement the P0.1 standalone foundations without provider/tool/runtime expansion, keep ChaseOS optional, prove deterministic behavior, align current-truth documentation, create logical commits, and push the review branch without merging.

## Repo-truth baseline

- Local `HEAD`, `main`, and `origin/main` began at `57c3d83` with inherited tracked Phase 2 and audit/handover changes.
- The inherited suite passed 33 tests; seven golden JSONL files contained 3 rows each and the contract seed contained 6 valid rows.
- The primary builder mixed domain-neutral artifact assembly with website-design keywords and fixed design outputs.
- Human-review scores were placeholders; no review store, governed memory store, retrieval system, or working knowledge map existed.
- Runtime adapters were inactive stubs and the existing ChaseOS-shaped packet did not dispatch.
- One historical stash existed and was preserved unchanged.

## Files read

- The full operator handover attachment and prior continuation attachment.
- Root product/setup/handover documents, product architecture and roadmap files, source-card/eval/memory/learning docs, current build/daily/history records, code, tests, datasets, examples, Git state, remote refs, ignored-state classification, stash state, and disk state.
- The research workbook remained read-only and was not used as an authority source for P0.1 decisions.

## Files modified

- Root truth and usage: `README.md`, `START_HERE.md`, `NEXT_STEPS.md`, `HANDOVER.md`, `.gitignore`, `pyproject.toml`.
- Canonical behavior: `src/chaser_agent/source_card.py`, `src/chaser_agent/summary/source_card.py`, `src/chaser_agent/cli.py`, existing memory compatibility files, and Chaser agent prose in the existing ChaseOS/SkillGate surfaces.
- Product/eval/summary/memory/learning docs under `docs/00_START_HERE.md`, `docs/01_Product/`, `docs/02_Evals/`, `docs/03_Summary_Intelligence/`, `docs/04_Memory/`, and `docs/08_Learning/`.
- Existing review/adapter tests where behavior or product naming changed.
- Linked build, documentation-history, daily, and index files.

## Files created

- `src/chaser_agent/core/` protocol boundaries.
- `src/chaser_agent/workflows/` with general, AI-engineering research, and website-design profiles.
- `src/chaser_agent/governance/`, `src/chaser_agent/reviews/`, `src/chaser_agent/memory/`, and `src/chaser_agent/knowledge/` implementations.
- `src/chaser_agent/integrations/chaseos/` inactive proposal adapter and shared persistence defaults.
- Tests for profiles/core boundaries, review writeback, memory lifecycle/retrieval, knowledge-map provenance, and test-matrix export.
- `scripts/export_test_matrix.py` and `docs/02_Evals/Chaser-Agent-Current-Test-Matrix.md`.
- Exact source handover and starting-file classification under `docs/99_HANDOVERS/`.
- This build log, linked documentation-history note, and Codex agent-activity record.

## Tests run

Baseline:

```bash
wsl.exe bash -lc 'cd /mnt/c/Users/chaseos/Documents/Projects/chaser-agent && timeout 300s .venv/bin/python -m pytest -q && .venv/bin/python -m scripts.validate_jsonl evals/datasets/golden/*.jsonl evals/datasets/contract/*.jsonl'
```

Focused implementation suites were run after each layer, including:

```bash
.venv/bin/python -m pytest -q tests/test_workflow_profiles.py tests/test_source_card_harness.py tests/test_contract_eval_runner.py tests/test_summary_schema.py
.venv/bin/python -m pytest -q tests/test_review_workflow.py tests/test_memory_store.py
.venv/bin/python -m pytest -q tests/test_knowledge_map.py tests/test_memory_store.py tests/test_review_workflow.py
.venv/bin/python -m pytest -q tests/test_test_matrix_export.py tests/test_jsonl_datasets.py tests/test_contract_eval_runner.py
```

Final implementation gate:

```bash
wsl.exe bash -lc 'cd /mnt/c/Users/chaseos/Documents/Projects/chaser-agent && timeout 300s .venv/bin/python -m pytest -q && .venv/bin/python -m scripts.validate_jsonl evals/datasets/golden/*.jsonl evals/datasets/contract/*.jsonl'
```

Documentation and affected-surface gate:

```text
PowerShell relative Markdown-link scan
git diff --check
.venv/bin/python -m pytest -q tests/test_chaseos_native_packet.py tests/test_workflow_profiles.py tests/test_review_workflow.py tests/test_memory_store.py tests/test_knowledge_map.py tests/test_test_matrix_export.py
```

One attempted combined WSL inline-import command failed at shell parsing before any test launched. It was split into the successful bounded gates above.

## Test results

- Baseline: 33 passed; all 27 JSONL rows valid.
- Pre-closeout full suite: 55 passed in 60.16 seconds.
- Final verbose full suite after all code/document changes: 55 passed in 320.79 seconds. A preceding 300-second rerun timed out without a reported test failure; the verbose run showed broad WSL/mounted-filesystem latency rather than a single stuck or failing test.
- Final JSONL validation: seven golden files x 3 rows plus one contract file x 6 rows valid.
- Final affected-surface suite: 24 passed in 72.44 seconds.
- Generated matrix: 8 files, 27 rows, exact exporter/committed-file parity.
- Markdown relative links: all checked targets resolved.
- `git diff --check`: passed.
- Repeated staged secret-pattern scans: no credential-like matches.

## Verification evidence

- `general_source_review` is the default; AI-engineering and website behavior lives in explicit profile modules.
- Markdown headings are excluded from claims, source-presented claim types avoid unearned `fact` labels, and the compatibility builder delegates to the canonical implementation.
- Review records validate five 0–3 scores and explicit decisions, are insert-only/content-hashed, and leave original run-artifact hashes unchanged.
- Accepted/rejected candidate decisions produce append-only memory versions; review does not promote.
- Promotion requires reviewed state, a matching accepted candidate, the human operator identity, and a persisted governance audit.
- Retrieval is lexical/tag/scope/type/status/recency based and defaults to promoted state; no embedding dependency exists.
- Knowledge nodes/edges use deterministic UUID identities and source-to-memory traces resolve through claim and evidence nodes.
- The optional ChaseOS adapter is outside the core package, is inactive, stamps all authority false, and raises on dispatch.
- The core-boundary test finds no ChaseOS import in `src/chaser_agent/core/`.

## What changed

- Reframed the product as standalone-first and ChaseOS-enhanced without erasing its ChaseOS origin.
- Replaced design-specific default behavior with a domain-neutral canonical builder and non-authorising profiles.
- Made human review a real persisted writeback surface.
- Added governed local memory, feedback, safe retrieval, and provenance graph foundations using Python standard-library SQLite.
- Exposed exact eval seed values and maturity so rows are not mistaken for achieved scores.
- Reconciled inherited tracked truth into a committed baseline before implementation.

## What did not change

- No FastAPI/web UI, provider/local model, RAG embeddings/vector database, MCP/tool/browser runtime, autonomous loop, training/fine-tuning, public action, payment, trade, deployment, credential operation, or ChaseOS canonical mutation was introduced.
- No generated run/research artifact, local database, cache, private dataset, workbook, `.env`, credential, or ignored artifact was committed.
- The historical stash was not applied, changed, or deleted.
- No merge occurred.

## What remains unverified

- Human usefulness of generated review artifacts and operator acceptance of example review/memory/graph records.
- Final 12/15 threshold, privacy-class definitions, durable-state terminology, official domain pack, and profile discovery.
- Local export/deletion and retention semantics; standalone/ChaseOS synchronization and conflict rules.
- Product-quality and adversarial eval coverage beyond six pending-review wiring seeds.
- Live ChaseOS Gate consumption and every deliberately excluded provider/tool/runtime surface.

## Logical commits

- `7caf7ac` reconcile inherited local truth state.
- `356741d` realign standalone-first product documentation.
- `9d15a58` add protocols, profiles, and neutral builder.
- `0a4196b` persist immutable human reviews and local governance.
- `cdcbcb1` add governed local memory lifecycle and retrieval.
- `4dd847f` add provenance map and inactive ChaseOS adapter.
- `7411883` export exact eval seed matrix.
- `4670c10` record P0.1 as-built documentation truth.
- `f636135` add linked standalone P0.1 session records.

## Process and storage closeout

- C: before implementation/test work: approximately 13.96 GiB / 5.87% free.
- Pre-log closeout snapshot: 13.54 GiB / 5.70% free, above the 10 GiB and 5% gates.
- Final pre-handover snapshot: 13.23 GiB / 5.56% free, still above both gates.
- `chaseos audit storage --apply --require-headroom`: attempted, but unavailable because `chaseos` was not found on `PATH`.
- No server, browser, benchmark, model worker, or long-running helper was started. WSL test processes completed under bounded timeouts.
- A post-test PID recheck confirmed the wrapper Bash/WSL processes observed during the check had exited; no owned repo/test helper remained.
- No cache, generated artifact, source, user data, governed state, or evidence was deleted.

## Push verification

- `codex/standalone-first-memory-realignment` was pushed to `origin` and configured as its upstream.
- The live remote branch matched local `f636135192e0d93bc6a2009549bb9c24b339a68e` before this final log-only closeout update.
- No merge or pull request was created.

## Remaining open loops

1. Operator-inspect a representative immutable review, reviewed memory history, promotion audit, and provenance trace.
2. Decide or revise the open P0.1 terminology/policy items.
3. Add reviewed product-quality cases before any intelligence or training claim.
4. Decide whether to merge the review branch; do not merge automatically.
5. Restore the project-native storage-audit command separately.

## Next recommended pass

An operator-led P0.1 acceptance pass using a safe local source and explicit temporary/configured database. If accepted, record threshold/lifecycle decisions and only then consider a provider-neutral fake adapter plus reviewed AI-engineering cases.

## Linked records

- [Documentation history](../../99_ARCHIVE/Documentation-History/2026-08-11_standalone-first-memory-realignment.md)
- [Daily note](../Daily/2026-08-11.md)
- [Agent activity](../Agent-Activity/2026-08-11-codex-standalone-first-memory-realignment.md)
- [Master redesign handover](../../docs/99_HANDOVERS/2026-08-11-CHASER_AGENT_STANDALONE_FIRST_MASTER_REDESIGN_HANDOVER.md)
- [As-built map](../../docs/01_Product/Chaser-Agent-As-Built-Map.md)
- [Current test matrix](../../docs/02_Evals/Chaser-Agent-Current-Test-Matrix.md)
- [P0.1 open decisions](../../docs/01_Product/Chaser-Agent-P0.1-Open-Decisions.md)
