# Chaser agent Roadmap

This roadmap restarts the thinking order from Layer 0. Evals and implementation deepen only after expected behavior is defined.

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

**Purpose:** Teach the foundations needed to build Chaser agent intentionally.

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

## Phase 3 — Source Summary Engine

**Purpose:** Improve the source-summary loop with richer review packets.

**Deliverables:** claims/evidence/contradiction/action/memory output pipeline.

**Definition of done:** outputs are useful under human review.

**Out of scope:** canonical promotion.

## Phase 4 — Memory Candidate Review

**Purpose:** Build a safe candidate/review workflow.

**Deliverables:** memory states, review packets, transition tests.

**Definition of done:** no candidate becomes canonical without governance.

**Out of scope:** auto-memory.

## Phase 5 — Tool/MCP Mini-Evals

**Purpose:** Measure least-authority tool behavior before real tools.

**Deliverables:** synthetic resource/tool/prompt cases.

**Definition of done:** forbidden writes and schema misuse are caught.

**Out of scope:** live MCP write authority.

## Phase 6 — Runtime Adapter Experiments

**Purpose:** Mock/dry-run adapter lessons from Hermes, OpenClaw, Codex, OpenAI, and local models.

**Deliverables:** adapter contracts and denial tests.

**Definition of done:** no live authority exists without approval.

**Out of scope:** activation.

## Phase 7 — Skill System / SkillOpt-style loop

**Purpose:** Make skills evaluated and reviewable.

**Deliverables:** quarantine, before/after evals, rollback.

**Definition of done:** skill edits are measured and reversible.

**Out of scope:** uncontrolled self-editing.

## Phase 8 — reviewed datasets and fine-tuning decision

**Purpose:** Decide whether training is justified.

**Deliverables:** reviewed datasets, privacy classification, decision memo.

**Definition of done:** operator can approve/reject fine-tuning based on evidence.

**Out of scope:** training unless separately approved.
