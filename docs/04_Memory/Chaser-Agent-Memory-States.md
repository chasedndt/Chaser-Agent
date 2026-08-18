# Chaser Agent Memory States

These states prevent raw context from becoming durable truth without evidence, review, and governance.

| State | Meaning | Creation or transition authority | Allowed next states |
|---|---|---|---|
| `raw` | Unprocessed source context; not durable memory | intake/import | `candidate` |
| `candidate` | Source-grounded memory proposal | deterministic run or operator | `reviewed`, `rejected` |
| `reviewed` | Human-inspected and accepted candidate | immutable human review | `promoted`, `rejected` |
| `promoted` | Approved durable local state | governance backend with approving reviewer and audit | `stale`, `disputed`, `archived` |
| `stale` | Previously approved but likely outdated | explicit lifecycle decision | `reviewed`, `disputed`, `archived` |
| `disputed` | Conflicting or challenged record retained for provenance | explicit lifecycle decision | `reviewed`, `rejected`, `archived` |
| `archived` | Preserved but inactive terminal record | explicit lifecycle decision | none |
| `rejected` | Explicitly declined terminal record | human review or lifecycle decision | none |

## Minimum record

Every record carries `memory_id`, type, content, status, scope, privacy class, stability, confidence, source/claim references, run identity, creation/review/promotion timestamps, reviewer, supersession links, tags, and metadata.

## Enforced boundaries

- `candidate -> promoted` and `raw -> promoted` are invalid.
- Promotion requires reviewed status and an approved governance audit.
- Promotion identifies the approving human reviewer.
- Original candidate and reviewed versions remain in history.
- Rejected and archived records cannot be promoted.
- A superseding record links to prior memory; it does not overwrite it.

Standalone local promotion and ChaseOS shared canonical promotion are different deployment-scoped decisions. P0.1 implements the former. The optional ChaseOS adapter remains inactive and cannot dispatch.
