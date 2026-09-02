# Chaser Agent Standalone Memory Architecture

**Layer:** 8 (Memory Consolidation) · **Status:** implemented in P0.1 · **Code:** `src/chaser_agent/memory/`

## What "standalone memory" means

Chaser Agent can remember approved information **without ChaseOS installed**. In standalone mode the human operator is the approval authority and promoted memory becomes *approved durable local state* — user-owned, on the user's machine.

Promotion does **not** mean the statement is globally or objectively true. It means: a candidate was reviewed, the operator accepted it, local governance allowed the transition, and provenance was preserved.

> Naming note: whether locally promoted memory is publicly called "canonical memory" or "approved durable memory" remains an open operator decision (§24.7 of the redesign handover). This document uses *approved durable local state*.

## Memory categories

| Category | Contents | P0.1 |
|---|---|---|
| Working | Current run/session context; may be temporary | Implicit |
| Episodic | Reviewed records of prior runs, decisions, outcomes, feedback | Supported |
| Semantic | Reviewed durable facts, preferences, concepts, project truths, operator constraints | Supported |
| Procedural | Reviewed skills, workflows, operating instructions | Supported |
| Runtime/repair | Failures, retries, rollbacks, adapter incidents | Not active (no execution yet) |

## The lifecycle

```text
raw -> candidate -> reviewed -> promoted -> stale / disputed -> archived
                         \-> rejected
```

Enforced in `memory/lifecycle.py` as an explicit finite-state machine (`VALID_TRANSITIONS`). This is a maths concept made literal — see [Maths for Chaser Agent](../08_Learning/Maths-For-Chaser-Agent.md) on finite-state machines and sets.

Rules encoded in code, not just prose:

- a run may create a candidate (`create()` rejects any status other than `raw`/`candidate`);
- review may accept or reject a candidate;
- **only a governance backend may promote** — `transition()` refuses `promoted` without an approved audit record naming `approved_by`;
- `reviewed` and `promoted` require `reviewed_at` and `reviewer_id`;
- `archived` and `rejected` are terminal (empty transition sets);
- invalid transitions raise `ValueError` naming the attempted move.

## Record schema

`MemoryRecord` (frozen dataclass) carries content plus full provenance: `memory_id`, `memory_type`, `content`, `status`, `scope`, `privacy_class`, `stability`, `confidence`, `source_refs`, `claim_refs`, `run_id`, timestamps, `reviewer_id`, `supersedes`, `tags`, `metadata_json`. Validation rejects impossible states (e.g. promoted memory with no `promoted_at`).

## Append-only storage

`SQLiteMemoryStore` uses standard-library SQLite with a `memory_versions` table keyed by `(memory_id, version)`. **Transitions insert a new version rather than updating a row.** `get()` returns the latest version; `history()` returns the full chain. Nothing is silently overwritten (Principle 12), and `record_hash` is `UNIQUE`, so an identical duplicate insert fails.

Promotions additionally write to `governance_audits`, so every promoted memory has an audit record identifying who approved it.

### Location

Default `~/.chaser-agent/chaser-agent.db` (configurable via `persistence.prepare_database_path`). The database lives **outside the repository** by default and `*.db` is git-ignored — user state is never committed. Tests use temporary directories.

## Retrieval (P0.1: lexical, no embeddings)

`retrieve()` filters on **status** (default: `promoted` only), **scope**, **memory_type**, **tags**, and lexical term matching over content and tags, ordered by recency with a `limit`. Deliberately no vector embeddings — that is a later pass with its own maths (cosine similarity, recall@K, MRR).

Retrieved memory must be displayed separately from source claims, and any inference influenced by memory should reference the relevant memory IDs. Memory is context, not evidence.

## Memory feedback

The operator can mark retrieved memory `useful` · `irrelevant` · `stale` · `disputed` via `add_feedback()`, persisted in `memory_feedback`. This is how retrieval quality becomes measurable over time.

## Memory is not model training

Principle 6. Memory changes available **context and state**. Fine-tuning changes **model weights**. Promoting a memory teaches the system nothing about language; it makes an approved fact retrievable. Conflating the two is the most common conceptual error in agent design.

## Open operator decisions

Export and deletion policy for local memory (§24.17), retention policy for review records (§24.18), and synchronisation/conflict semantics between standalone memory and ChaseOS memory (§24.15–16) remain unresolved. See [ChaseOS Optional Integration](../05_Runtime_Adapters/Chaser-Agent-ChaseOS-Optional-Integration.md).
