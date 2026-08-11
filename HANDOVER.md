# Chaser agent Handover

## Approved product direction

Chaser agent is standalone-first and ChaseOS-enhanced. Standalone users must be able to run deterministic source review, persist immutable human review, govern approved durable local memory, and query provenance without ChaseOS installed.

ChaseOS remains the optional integrated control plane for shared governance, policy, approval, orchestration, routing, shared canonical state, and cross-project memory.

## Active branch

```text
codex/standalone-first-memory-realignment
```

Do not merge automatically.

## Starting truth

- Starting commit: `57c3d836b93d1de0faeb91d50c7fb83104c0c7ae`.
- Phase 1 deterministic Source Card Harness: implemented shape proof.
- Phase 2 contract eval: partial, six pending-review seeds.
- Baseline before P0.1: 33 tests passed; the current P0.1 branch passes 55 tests and all golden/contract JSONL validation.
- One historical stash remains preserved and must not be applied or deleted automatically.
- Ignored run and research artifacts remain local and unpublished.

## P0.1 implementation now on the review branch

- domain-neutral core and workflow profiles;
- local governance protocols;
- immutable review records;
- standalone SQLite memory lifecycle;
- lexical/tag retrieval;
- SQLite knowledge map;
- optional inactive ChaseOS adapter;
- exact test-matrix export;
- documentation and learning reconciliation;
- exact 27-row test matrix at `docs/02_Evals/Chaser-Agent-Current-Test-Matrix.md`.

Logical implementation commits are recorded in the final build log. The branch is not merged or released.

## Authority boundary

P0.1 is provider-free, tool-free, browser-free, service-free, and training-free. It may persist human review and governance-approved local memory. It may not let generated output approve itself, execute external actions, dispatch ChaseOS work, or mutate original run artifacts.

## Required reading

1. `docs/01_Product/Chaser-Agent-Product-Narrative-and-Utility.md`
2. `docs/01_Product/Chaser-Agent-Layer-0-Behaviour-Contract.md`
3. `docs/01_Product/Chaser-Agent-Standalone-vs-ChaseOS-Architecture.md`
4. `docs/01_Product/Chaser-Agent-P0.1-Open-Decisions.md`
5. `docs/99_HANDOVERS/2026-08-11-CHASER_AGENT_STANDALONE_FIRST_MASTER_REDESIGN_HANDOVER.md`

## Next decision gate

The operator must inspect the review-flow, memory-lifecycle, and provenance demonstrations before promotion semantics are considered accepted. The proposed 12/15 threshold remains configurable and unenforced.
