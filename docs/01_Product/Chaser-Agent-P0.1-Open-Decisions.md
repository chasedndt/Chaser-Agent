# Chaser Agent P0.1 Open Decisions

**Status:** OPERATOR DECISION REQUIRED. These items are intentionally not resolved by implementation.

| ID | Decision | P0.1 treatment until decided |
|---|---|---|
| P01-D01 | Final human-review pass threshold | Configurable proposal: total >= 12/15, no score below 2, no critical safety failure |
| P01-D02 | Exact `public` definition | Preserve current labels; do not infer permission from label alone |
| P01-D03 | Exact `scrubbed` definition | Require explicit operator classification |
| P01-D04 | Exact `internal_safe` definition | Local-only; no publication assumption |
| P01-D05 | Exact `private` definition | Local-only and excluded from public fixtures |
| P01-D06 | Exact `secret` definition | Always blocked from review/memory artifacts |
| P01-D07 | Public UX term: canonical memory or approved durable memory | Use `approved durable local state` in P0.1 docs/UI |
| P01-D08 | First official domain pack | Implement AI-engineering as an available profile, not the declared official first pack |
| P01-D09 | Post-P0.1 profile discovery/package mechanism | Static built-in registry only |
| P01-D10 | FastAPI in V1 or V1.5 | Not built |
| P01-D11 | First provider | Not selected |
| P01-D12 | First RAG corpus | Not selected; no embeddings/index in P0.1 |
| P01-D13 | First read-only tool | Not selected; no tool registry execution |
| P01-D14 | Sandbox architecture | Not selected; execution forbidden |
| P01-D15 | Standalone-to-ChaseOS memory synchronisation | Packet boundary only; no sync |
| P01-D16 | Standalone/ChaseOS memory conflict resolution | No automatic resolution |
| P01-D17 | Local-memory export/deletion policy | Architecture records user ownership; command semantics deferred |
| P01-D18 | Review-record retention policy | Immutable local records; deletion/retention command deferred |

Any new unresolved decision must be added here rather than silently embedded in code.
