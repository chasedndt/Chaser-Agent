# Chaser agent Memory Consolidation

**Status:** P0.1 IMPLEMENTED AND LOCALLY VERIFIED.

Chaser agent persists governed local memory as append-only SQLite versions:

```text
raw -> candidate -> reviewed -> promoted
                           \-> rejected
promoted -> stale | disputed | archived
stale -> reviewed | disputed | archived
disputed -> reviewed | rejected | archived
```

Raw context remains source evidence, not durable memory. A source-review run may propose a candidate. An immutable human review may accept it into `reviewed` state or reject it. Review alone never promotes. Only a governance backend may create a `promoted` version, and that transition requires the approving reviewer plus a persisted audit record.

Standalone promotion creates human-approved durable local state. It does not make a statement globally true and does not mutate ChaseOS shared canonical state.

## Persistence

- Default path: `~/.chaser-agent/chaser-agent.db`.
- An explicit database path can be supplied without `.env`.
- Tests use temporary directories.
- Databases are ignored and never created in the public repository by default.
- Each transition inserts a new version; prior versions remain queryable.
- Feedback values `useful`, `irrelevant`, `stale`, and `disputed` persist separately and do not silently change lifecycle state.

## Retrieval

P0.1 retrieval filters current records by status, scope, memory type, tags, lexical terms, and recency. The safe default returns only promoted records. No embeddings or vector database are used.

Retrieved memory must be presented separately from source claims. Any future inference influenced by retrieved memory must cite the relevant memory IDs.
