# Chaser Agent As-Built Map

**Status:** P0.1 foundation plus provider/tool boundaries implemented on `codex/standalone-first-memory-realignment`; Layer 0 + 17-layer reconciliation and workflow-episode eval foundation added on `codex/2026-08-23-architecture-eval-floorwalk`. Not merged, released, or operator-accepted.

This page maps executable repository truth to Layer 0 plus the 17 engineering layers. The generated matrix currently inventories 21 smoke/golden-labelled rows, 30 Layer 0 contract rows with 154 assertions, and one public-safe case-study workflow episode. These results prove deterministic contracts and structural wiring, not product-quality intelligence.

## Working capabilities

| Capability | Code | Interface | Verified boundary |
|---|---|---|---|
| Domain-neutral source review | `source_card.py` | `source-card` | Heading-safe claims, evidence links, source/inference separation, no automatic authority |
| Workflow profiles | `workflows/` | `--profile` | General default; AI-engineering and website behavior isolated |
| Human review writeback | `reviews/` | `review` | 0–3 scores, corrections and decisions persist; source artifacts remain unchanged |
| Standalone governance | `governance/local.py` | Python protocol/API | Human authority; external action execution disabled; threshold proposal unenforced |
| Governed memory | `memory/` | review writeback plus Python API | Append-only versions, lifecycle validation, audited promotion, feedback |
| Local retrieval | `memory/sqlite_store.py` | Python API | Lexical, scope, type, tag, status and recency filters; promoted-only default |
| Provenance map | `knowledge/` | review writeback plus Python API | Deterministic nodes/edges and source-to-memory trace queries |
| Optional ChaseOS adapter | `integrations/chaseos/adapter.py` | Python API | Packet conversion only; inactive; dispatch raises |
| Test-matrix visibility | `scripts/export_test_matrix.py` | module/script | Exact 52 public rows with maturity and review labels |
| Layer 0 contract eval | `evals/contract_runner.py` | `contract-eval` | 30 executable cases / 154 artifact assertions, all pending operator review |
| Workflow episode eval | `evals/workflow_episode.py` | `workflow-episode-validate`, `workflow-trace-eval` | Dependencies, evidence, authority, artifacts, proof and handoff scored; human usefulness remains unreviewed |
| Provider boundary | `providers/` | Python protocol/API | Fake only; sensitive-data gate, budgets, rate/latency ceilings, quarantine and baseline comparison; no live provider |
| Tool/MCP boundary | `tools/` | Python protocol/API | Registry/grant/canonical path-and-URL scope/budget planning and fake-result quarantine; execution deliberately raises |
| Skill gate | `skillgate.py` | `skill-gate` | Bounded review packet only; no apply path |
| Visual completion evaluator | `visual_completion.py` | `visual-eval` | Evidence metadata only; cannot mark complete |

## Canonical source-review path

```text
safe local source
-> SourceInput
-> heading-safe deterministic content chunks
-> source-presented claim-type classification
-> evidence-linked claims
-> explicit WorkflowProfile inference/uncertainty/actions/memory proposals
-> seven review artifacts plus run log
-> immutable human review
-> accepted/rejected append-only memory state
-> separate governance-gated promotion
-> provenance knowledge map
```

`src/chaser_agent/source_card.py` is the sole canonical builder. `summary/source_card.py` is a documented compatibility re-export, so the smoke and contract paths no longer maintain separate implementations.

## Persistence truth

- Default database: `~/.chaser-agent/chaser-agent.db`, outside the repository.
- Explicit database paths require no `.env`; tests use temporary directories.
- Review rows are insert-only and content-hashed.
- Memory transitions append versions; they do not overwrite prior states.
- Review alone can create reviewed/rejected records for selected candidates but cannot promote them.
- Promotion requires a reviewed accepted candidate, matching human reviewer, local-governance approval, and a persisted audit.
- The graph is a relationship index; source artifacts, reviews, and memory records remain authoritative records in their own stores.

## Layer status

| # | Layer | As-built status |
|---|---|---|
| 0 | Behaviour Contract | ENFORCED for 30 current deterministic cases / 154 assertions; operator-reviewed and metamorphic coverage remains open |
| 1 | User / Operator | IMPLEMENTED CLI writeback; no UI or interactive queue |
| 2 | Standalone Operator Interface / optional ChaseOS Studio host | PARTIAL; standalone CLI and review files exist, but no local graphical interface or ChaseOS Studio adapter is built |
| 3 | Capture / Intake | PARTIAL local-file intake and separate explicit research lane |
| 4 | Source Package | IMPLEMENTED deterministic artifact set |
| 5 | Workspace / Collection | NOT BUILT beyond scope/tags |
| 6 | Retrieval / Evidence | IMPLEMENTED lexical reviewed-memory retrieval; no semantic RAG |
| 7 | Summary Intelligence | IMPLEMENTED deterministic profile-aware baseline; no model intelligence |
| 8 | Memory Consolidation | IMPLEMENTED local SQLite lifecycle and feedback |
| 9 | Knowledge Map | IMPLEMENTED local SQLite provenance nodes, edges, and queries |
| 10 | Agent Runtime / AOR | NOT BUILT |
| 11 | Harness | IMPLEMENTED deterministic runs, review, matrix export, smoke/contract tests and workflow-episode structural evals; product-quality labels remain open |
| 12 | Provider Router | BOUNDARY IMPLEMENTED; fake provider only, no SDK/network/credentials |
| 13 | Tool / MCP | BOUNDARY IMPLEMENTED; capability planning and fake results only, no execution |
| 14 | Browser / Computer Use | METADATA-EVAL ONLY; no runtime or pixel inspection |
| 15 | Runtime Memory / Repair | NOT BUILT |
| 16 | Governance / Approval | IMPLEMENTED standalone local transition policy; ChaseOS Gate consumption NOT ACTIVE |
| 17 | Extension / Skill / Forge | PARTIAL bounded SkillGate; no automatic apply or optimisation |

## Deliberately open

- Review threshold is a configurable, unenforced 12/15 proposal pending operator decision.
- Public privacy-class definitions, durable-memory UX terminology, official domain pack, and profile discovery remain undecided.
- Export/deletion, retention, and standalone/ChaseOS sync/conflict semantics remain undecided.
- HTTP/FastAPI, live providers, real MCP/tools, embeddings, browsers, autonomous loops, and training are not active.
- Human inspection of example review/memory/graph records remains the acceptance gate.
