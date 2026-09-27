# Chaser Agent As-Built Map

**Status:** P0.1 IMPLEMENTED AND LOCALLY VERIFIED on `codex/standalone-first-memory-realignment`; not merged, released, or operator-accepted.

This page maps executable repository truth to the 17-layer architecture. The full suite passed 55 tests on 2026-08-11, and all 21 golden plus 6 contract JSONL rows validated. Those results prove deterministic contracts and wiring, not product-quality intelligence.

2026-09-27 engineering addendum: the isolated `codex/2026-09-27-standalone-http-foundation` worktree has a local-only, bearer-protected review API (`local_http.py`; [contract and threat model](../05_Runtime_Adapters/Chaser-Agent-Local-HTTP.md)). It creates pending source-card runs from public/toy text and retrieves their exact source and artifacts. It has no LLM provider, autonomous tool, or public network authority. This addendum does not change the older P0.1 branch's status or claim that HTTP is merged.

The isolated loopback listener now caps simultaneous client handlers at 16 and rejects excess connections with `503`, alongside its separate authenticated POST rate limit. This is bounded local transport hardening, not public-service readiness or a cure for the existing broad-ACL runtime.

A read-only `doctor` CLI now reports runtime-directory/token/run ACL states and whether the configured loopback port can bind at check time. It makes no data, token or permission changes and cannot claim the service launched; the current E: runtime reports three broad-ACL blockers.

Further engineering in the same isolated worktree adds optional local Pocket Alba speech-out jobs with a prewarmed worker, and an executor-gated HUD bridge plus synthetic desktop preview. A second warm reply was measured end-to-end at 4.52 seconds on this machine. The HUD now has tested button-request, pending-state and matching-acknowledgement wiring with a fake executor; the normal CLI attaches no executor. This does **not** supply real computer control, human listening acceptance, or a complete two-way conversational voice mode.

Later on 2026-09-27, the same isolated worktree added an [opt-in offline voice-input CLI](../05_Runtime_Adapters/Chaser-Agent-Local-Voice-Input.md). It locally transcribed a public/toy WAV using a pinned, receipt-verified faster-whisper tiny English model on E:. Interactive microphone code opens only after Enter, but live operator microphone behavior is not verified. A fixed Pocket Alba acknowledgement can be requested separately; it is not a task answer. These additions do not activate a reasoning model, agent actions, computer use or full-duplex voice.

The next security and voice-status slice makes the HUD and optional voice client check private runtime/token ACLs before credential use. `voice-mode --speak-status` can answer only a few exact read-only health/HUD questions with bounded speech text. Its HTTP and playback path is mocked in tests; no live reply or microphone acceptance is claimed. The existing runtime remains refused until operator-approved ACL repair and token rotation.

The `desktop` CLI then combined the loopback API and a visible idle HUD under one foreground lifecycle. A synthetic screenshot shows the port and disabled controls, and a real loopback lifecycle test verifies that the launcher stops only its own server. The actual E: runtime remains ACL-blocked; no real computer-use executor or voice conversation was added.

An optional desktop push-to-talk panel now loads the pinned offline STT model asynchronously, paints the microphone indicator before a click-triggered bounded take, supports cancellation, and shows an unverified in-memory draft. Speak status remains a separate exact read-only action with mocked HTTP/audio proof. The optional E: model loaded successfully without opening the microphone; no operator recording, audible reply, real executor or general conversational model was verified.

The local Pocket Alba job API now accepts a token-protected cancellation request for the exact active take and records a marker that suppresses late audio after restart. The HUD exposes Cancel reply and prevents a new Talk take while a reply is pending. Fake-worker recovery and synthetic visual tests pass; actual speech interruption and already-started playback remain unverified on a real device.

For HUD replies, an optional output-only stream now writes roughly 50 ms PCM16 or IEEE-float32 WAV chunks and aborts pending buffers on cancellation. Mocked output tests and the installed environment's 24 kHz mono/int16 and float32 settings checks pass. Audible output and real stop latency remain unverified; the fixed CLI acknowledgement retains its earlier blocking Windows playback.

The HUD bridge also permits the identical in-process executor to reconnect an uncertain, nonterminal session without discarding pending control state. A different executor object cannot claim it, old report callbacks stay invalid, and controls remain disabled until a fresh higher-sequence event arrives. This is fake-executor lifecycle proof only; no real computer-use adapter or process-crash recovery is present.

Synthetic layout QA then exposed fixed-size clipping at simulated 200%-style Tk scaling; scale-aware sizing and a scrollable small-screen container corrected the inspected captures. These are rendered local checks, not live high-DPI or accessibility acceptance.

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
| Test-matrix visibility | `scripts/export_test_matrix.py` | module/script | Exact 27 public rows with maturity and review labels |
| Layer 0 contract eval | `evals/contract_runner.py` | `contract-eval` | Six executable artifact-assertion seeds, all pending operator review |
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
| 0 | Behaviour Contract | VERIFIED for current deterministic assertions; coverage remains PARTIAL |
| 1 | User / Operator | IMPLEMENTED CLI writeback; no UI or interactive queue |
| 2 | Studio / Interface | NOT BUILT; CLI and files only |
| 3 | Capture / Intake | PARTIAL local-file intake and separate explicit research lane |
| 4 | Source Package | IMPLEMENTED deterministic artifact set |
| 5 | Workspace / Collection | NOT BUILT beyond scope/tags |
| 6 | Retrieval / Evidence | IMPLEMENTED lexical reviewed-memory retrieval; no semantic RAG |
| 7 | Summary Intelligence | IMPLEMENTED deterministic profile-aware baseline; no model intelligence |
| 8 | Memory Consolidation | IMPLEMENTED local SQLite lifecycle and feedback |
| 9 | Knowledge Map | IMPLEMENTED local SQLite provenance nodes, edges, and queries |
| 10 | Agent Runtime / AOR | NOT BUILT |
| 11 | Harness | IMPLEMENTED deterministic runs, review, matrix export, smoke and contract tests; product evals remain PARTIAL |
| 12 | Provider Router | NOT BUILT; legacy stubs only |
| 13 | Tool / MCP | NOT BUILT; stub/docs only |
| 14 | Browser / Computer Use | METADATA-EVAL ONLY; no runtime or pixel inspection |
| 15 | Runtime Memory / Repair | NOT BUILT |
| 16 | Governance / Approval | IMPLEMENTED standalone local transition policy; ChaseOS Gate consumption NOT ACTIVE |
| 17 | Extension / Skill / Forge | PARTIAL bounded SkillGate; no automatic apply or optimisation |

## Deliberately open

- Review threshold is a configurable, unenforced 12/15 proposal pending operator decision.
- Public privacy-class definitions, durable-memory UX terminology, official domain pack, and profile discovery remain undecided.
- Export/deletion, retention, and standalone/ChaseOS sync/conflict semantics remain undecided.
- FastAPI, providers, embeddings, tools, browsers, autonomous loops, and training are not part of P0.1.
- Human inspection of example review/memory/graph records remains the acceptance gate.
