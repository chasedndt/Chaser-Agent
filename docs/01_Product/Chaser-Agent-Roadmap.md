# Chaser Agent Roadmap

This roadmap follows Layer 0 and the approved standalone-first product direction. Chaser Agent must work independently; ChaseOS integration remains optional and additive through interfaces.

## Phase 0A — scaffold already created

**Purpose:** Establish repo structure and runnable smoke checks.

**Deliverables:** docs, `src/`, `tests/`, toy JSONL, scripts, rubrics.

**Definition of done:** repo imports, JSONL parses, basic pytest passes.

**Out of scope:** product-quality behavior claims.

## Phase 0B — repo cleanup / starter artifacts retained

**Purpose:** Bring side-branch/spec work and safe starter-pack artifacts back onto `main`.

**Deliverables:** starter research/eval register and pack manifest retained under `docs/07_Research/`; branch work preserved; main pushed.

**Definition of done:** clean main, checks pass, no secrets committed.

**Out of scope:** deleting branch work or rewriting history.

## Phase 0C.0 — Layer 0 Behaviour Contract

**Purpose:** Define the product constitution before architecture or eval depth.

**Deliverables:** `Chaser-Agent-Layer-0-Behaviour-Contract.md`.

**Definition of done:** expected behavior, boundaries, and public-claim limits are explicit.

**Out of scope:** implementation.

## Phase 0C.1 — fundamentals and learning foundation

**Purpose:** Teach the foundations needed to build Chaser Agent intentionally.

**Deliverables:** AI engineering ladder, maths handout, university module linkage.

**Definition of done:** learning docs map concepts to repo work and mini-exercises.

**Out of scope:** advanced eval coding.

## Phase 0C.2 — V0 definition

**Purpose:** Define the first useful version in plain English.

**Deliverables:** V0 definition and first-principles model.

**Definition of done:** V0 loop, files, non-goals, and proof criteria are clear.

**Out of scope:** all 17 layers implemented.

## Phase 0C.3 — 17-layer architecture rewrite against Layer 0

**Purpose:** Make every layer subordinate to Layer 0.

**Deliverables:** architecture doc with Layer 0 and status/V0 relevance for each layer.

**Definition of done:** no layer claims implementation without proof.

**Out of scope:** runtime activation.

## Phase 0C.4 — existing eval/test classification only

**Purpose:** Reclassify existing tests and JSONL as smoke/schema unless they prove Layer 0 behavior.

**Deliverables:** updated eval harness and dataset docs.

**Definition of done:** product-quality evals are deferred until behavior is locked.

**Out of scope:** deepening eval implementation.


## Phase 0C.5 — V0 Blueprint Pass

**Purpose:** Lock the exact implementation-ready V0 loop before deeper eval/code work.

**Deliverables:**

- V0 Blueprint;
- V0 Source Card Schema;
- V0 Human Review Packet;
- updated Source Summary Spec;
- build log.

**Definition of done:** V0 interface, input contract, output contract, schemas, folder targets, and pass/fail criteria are defined; no provider calls added; no runtime adapters activated; no fine-tuning; no ChaseOS canonical mutation.

**Out of scope:** eval harness v0.2, provider/API integration, Hermes/OpenClaw adapters, MCP tools, browser/computer-use authority, private datasets, and model training.

**Next pass after this:** Phase 1 — Source Card Harness V0.

## Phase 1 — Source Card Harness V0

**Purpose:** Implement the first deterministic local source-card loop.

**Deliverables:**

- `src/chaser_agent/cli.py` `source-card` command;
- `src/chaser_agent/source_card.py` deterministic artifact builder;
- `src/chaser_agent/run_artifacts.py` JSON writer/run-log helpers;
- `examples/sources/toy_website_design_note.md` safe toy source;
- JSON artifacts under unique `logs/runs/source-card-.../` folders;
- tests covering artifact creation, required fields, review/promotion boundaries, JSON parsing, and missing-input failure.

**Definition of done:** source facts, inferences, uncertainty, actions, and memory candidates are separated; `review_status` is `pending_review`; `promotion_status` is `not_promoted`; run logs record no provider/API/runtime/MCP/browser/fine-tuning activity.

**Out of scope:** LLM/provider calls, Hermes/OpenClaw adapter activation, MCP tools, browser/computer-use runtime, private datasets, ChaseOS canonical mutation, and production-readiness claims.

**Status:** implemented as deterministic local V0 shape proof.

**Next pass after this:** Source Card Harness Review or Contract Eval Seeds.

## Phase 2 — Contract Evals

**Purpose:** Test Layer 0 behavior directly.

**Deliverables:** contract eval cases and result rows.

**Definition of done:** tests catch auto-promotion, unsupported claims, missing uncertainty, and unsafe actions.

**Out of scope:** broad benchmark claims.

**Status:** STRUCTURAL COVERAGE IMPLEMENTED / OPERATOR REVIEW OPEN. The deterministic artifact-field runner now executes 30 public-safe cases: five per initial Layer 0 family and 154 assertions. All remain `pending_operator_review`; countable family depth is not operator-reviewed golden data. Source-trust grading, metamorphic variants, per-domain packs, and product-quality labels remain open.

## Phase 2.5 — Case-Study Workflow Episodes

**Purpose:** Evaluate how an agent navigates real multi-step work rather than only scoring isolated output fields or phrases.

**Deliverables:** `workflow_episode.v1`; dependency/cycle validation; capability, evidence, artifact, proof, recovery, and handoff contracts; deterministic workflow-trace scoring; private/public/held-out/adversarial/regression separation; and a first public-safe MarginFlip-derived candidate episode.

**Definition of done:** workflow episodes validate and replay; dependency, authority, forbidden-outcome, and completion-proof defects fail; unreviewed rows cannot claim product-quality golden maturity.

**Status:** V1 STRUCTURAL FOUNDATION IMPLEMENTED on `codex/2026-08-23-architecture-eval-floorwalk`. The MarginFlip episode and candidate trace remain `pending_operator_review` and `training_eligible: false`.

**Next pass after this:** operator scoring of the three representative source-review runs and correction of the MarginFlip candidate workflow.

## P0.1 — Standalone Core, Review, Memory, and Knowledge Foundations

**Purpose:** Make the open-source core independently useful without ChaseOS while preserving human governance and deterministic auditability.

**Deliverables:**

- protocol boundaries for governance, review, memory, knowledge map, and workflow profiles;
- domain-neutral source-review builder;
- general, AI-engineering research, and website-design profiles;
- immutable local human-review records;
- local governance with no external side effects;
- SQLite memory lifecycle outside the repository;
- lexical/tag retrieval without embeddings;
- SQLite provenance map;
- optional inactive ChaseOS adapter;
- exact test-matrix export and honest maturity labels.

**Definition of done:** the package runs without ChaseOS, profile leakage tests pass, review and governed memory persist across process restart, invalid transitions fail, source-to-memory provenance resolves, all databases remain outside the repository by default, and the full existing suite/JSONL validation remains green.

**Out of scope:** FastAPI/UI, live providers/models, RAG embeddings/vector databases, MCP/tools/browser execution, autonomous loops, public actions, credentials, ChaseOS Gate consumption, and training.

**Status:** IMPLEMENTED on `codex/standalone-first-memory-realignment` with later provider/tool boundary and brand/security commits. The exact current dataset inventory is generated in `docs/02_Evals/Chaser-Agent-Current-Test-Matrix.md`. Operator acceptance, merge, release, product-quality labels, threshold terminology, and lifecycle-policy decisions remain open.

## Phase 3 — Model-Assisted Source Intelligence

**Purpose:** Compare the deterministic baseline with provider-neutral model-assisted review after P0.1 and reviewed examples exist.

**Deliverables:** provider-neutral envelope, deterministic fake adapter, budget/rate/latency ceilings, hostile-output quarantine, and comparison rig first; then a separately approved provider evaluation and reviewed workflow examples.

**Definition of done:** a separately approved read-only provider improves reviewed held-out cases over the deterministic baseline without authority drift and within declared cost/latency budgets.

**Out of scope:** canonical promotion or provider activation without operator approval.

**Status:** BOUNDARY IMPLEMENTED / LIVE PROVIDER INACTIVE. Fake-provider and comparison paths exist; no provider SDK, credentials, or network inference is active.

## Phase 4 — Memory Quality, Export, and Optional Sync

**Purpose:** Deepen the P0.1 local memory foundation after terminology, retention, export/deletion, and optional ChaseOS sync decisions.

**Deliverables:** reviewed quality policy, lifecycle feedback, export/deletion semantics, and separately approved sync/conflict rules.

**Definition of done:** no candidate becomes durable without governance and no local/shared conflict resolves silently.

**Out of scope:** auto-memory or automatic ChaseOS synchronisation.

## Phase 5 — Tool/MCP Mini-Evals

**Purpose:** Measure least-authority tool behavior before real tools.

**Deliverables:** synthetic resource/tool/prompt cases.

**Definition of done:** forbidden writes and schema misuse are caught.

**Out of scope:** live MCP write authority.

**Status:** CAPABILITY BOUNDARY IMPLEMENTED / EXECUTION INACTIVE. Registration, grants, target scopes, call budgets, fake results, and hostile-result quarantine exist. The execution method deliberately raises.

## Phase 6 — Runtime Adapter Experiments

**Purpose:** Mock/dry-run adapter lessons from Hermes, OpenClaw, Codex, OpenAI, and local models.

**Deliverables:** adapter contracts and denial tests.

**Definition of done:** no live authority exists without approval.

**Out of scope:** activation.

## Phase 6A — Standalone Persistent HTTP Runtime

**Purpose:** Turn the on-demand deterministic harness into a restart-safe local service without adding live model or tool authority.

**Learning focus:** processes, loopback networking, ports, HTTP semantics, run/session state machines, idempotency, concurrency, cancellation, event streaming, rate limiting, backpressure, health/readiness, persistence, and observability.

**Deliverables:** architecture decision; loopback-only configurable listener; durable run/session ledger; submit/status/cancel/review surfaces; bounded event stream; restart/replay tests; authentication and request-size/rate limits.

**Definition of done:** deterministic source review can be submitted over HTTP, survives restart, rejects duplicate requests safely, exposes honest state, and preserves approval boundaries. The service remains useful without ChaseOS.

**Out of scope:** public internet exposure, live providers/tools, autonomous external effects, multi-tenant hosting, and default dependence on Redis, Celery, Docker, or Kubernetes.

**Status:** NOT STARTED. No framework or port has been selected. The operator receives a networking/server fundamentals recap before the architecture decision and implementation exercise.

## Phase 6B — Context Continuity and Runtime Repair

**Purpose:** Preserve long-horizon work without treating an ever-growing chat transcript as memory.

**Deliverables:** context compiler, token/context budget, checkpoint summaries, reviewed-memory retrieval, provenance references, pause/resume, retry ceilings, crash recovery, stale-context detection, and duplicate-effect prevention.

**Definition of done:** held-out long-horizon episodes resume with the right evidence and decisions, report omitted context, and never truncate or repeat authority-bearing actions silently.

**Status:** NOT STARTED; depends on Phase 6A run/session persistence and Layer 15 recovery contracts.

## Phase 7 — Skill System / SkillOpt-style loop

**Purpose:** Make skills evaluated and reviewable.

**Deliverables:** quarantine, before/after evals, rollback.

**Definition of done:** skill edits are measured and reversible.

**Out of scope:** uncontrolled self-editing.

**Status:** first bounded foothold implemented as `skill-gate`: a deterministic local review packet generator for candidate `SKILL.md` patches. It checks strict held-out improvement, bounded edit budget, protected slow-state preservation, and closed authority flags without mutating baseline skills.

**Next pass after this:** connect `skill-gate` to real skill-specific fixture suites and richer diff summaries before any approval-consuming apply path.

## Phase 8 — reviewed datasets and fine-tuning decision

**Purpose:** Decide whether training is justified.

**Deliverables:** reviewed datasets, privacy classification, decision memo.

**Definition of done:** operator can approve/reject fine-tuning based on evidence.

**Out of scope:** training unless separately approved.

## Phase 9 — Future multi-domain agent-harness direction

**Purpose:** Define Chaser Agent as the governed, computer-local, multi-domain orchestration harness. Trading is one skill/workflow family alongside source intelligence, social-media growth/control, web and UI design, coding, business operations, and future personal workflows.

**Deliverables:** multi-domain skill/workflow registry; current repository/system map; per-domain inputs/outputs/tools/datasets/evals/authority contracts; shared permission/audit model; and bounded domain plans. The trading pack additionally covers normalized signal/thesis/candidate/order contracts, TradeSync digital-twin integration, an independent risk-engine contract, and disabled-by-default execution levels.

**Definition of done:** no domain pack becomes Chaser Agent's primary identity; each skill family has isolated authority and eval gates; each authority level is separately operator-approved; agent reasoning cannot override risk or governance; review loops cannot self-authorize; and implementation existence never implies live authority.

**Out of scope:** unrestricted multi-tool autonomy, current live orders, unapproved social publishing/account mutation, production deployment without approval, exchange/wallet credentials, silent self-training, canonical-memory mutation, or production-autonomy claims.

**Plan:** [`docs/plans/2026-07-11-multi-domain-agent-harness-direction.md`](../plans/2026-07-11-multi-domain-agent-harness-direction.md) · [`docs/plans/2026-07-11-domain-skill-workflow-registry.md`](../plans/2026-07-11-domain-skill-workflow-registry.md)

**Current status:** future governed multi-domain track. Immediate work remains bounded V0 source-intelligence, eval, skill, and harness foundations.
