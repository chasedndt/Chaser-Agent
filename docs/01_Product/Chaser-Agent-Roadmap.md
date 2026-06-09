# Chaser agent Roadmap

This roadmap keeps Chaser agent honest: documentation and evals first, implementation second, runtime authority later, and fine-tuning only after reviewed datasets exist.

## Phase 0A — Scaffold complete

**Purpose:** Establish the standalone repo and minimum runnable shape.

**Deliverables:** repo folders, starter docs, toy JSONL datasets, rubrics, package skeleton, scripts, tests, and build log.

**Definition of done:** repository imports, JSONL validator runs, smoke tests pass, GitHub remote exists.

**Out of scope:** production behavior, private data, provider calls, runtime autonomy.

## Phase 0B — Scaffold hardening / reference docs

**Purpose:** Add enough reference material to explain the scaffold and ChaseOS relationship.

**Deliverables:** product docs, eval docs, runtime adapter notes, memory docs, skill docs, research/learning docs.

**Definition of done:** major folders have orientation docs; no ChaseOS canonical mutation occurs.

**Out of scope:** deep implementation and adapter activation.

## Phase 0C — Spec deepening / current pass

**Purpose:** Replace thin placeholder Markdown with development-ready specifications.

**Deliverables:** expanded product thesis, actionable roadmap, concrete 17-layer architecture, dataset plan, source-summary spec, memory-state model, competitor map, skill-system spec, research-register mirror, website-alignment placeholder, and build log.

**Definition of done:** placeholder language is removed from core specs; tests/JSONL validation are recorded before and after; no implementation code is changed by this pass.

**Out of scope:** eval harness v0.2 code, providers, adapters, UI, private datasets, fine-tuning.

## Phase 1 — Source card harness

**Purpose:** Make the first wedge real: source input to source card with evidence and review metadata.

**Deliverables:** source-card schema, deterministic parser/formatter, examples, tests, source-summary eval rows.

**Definition of done:** source-card outputs include claims, evidence, uncertainty labels, contradictions, actions, and memory candidates; tests cover happy path and failure path.

**Out of scope:** LLM calls and automatic memory promotion.

## Phase 2 — Eval harness v0.2

**Purpose:** Upgrade from smoke tests to useful instrumentation.

**Deliverables:** `EvalResult` serialization, pass/fail reasons, score fields, per-family runner support, timestamped JSONL result logs under `logs/runs/`, tests for result rows.

**Definition of done:** all six current golden JSONL files can run through the deterministic eval runner and write valid result rows.

**Out of scope:** private datasets, external APIs, live provider comparisons.

## Phase 3 — Source summary engine

**Purpose:** Convert source cards into reviewable summaries and structured candidates.

**Deliverables:** summary pipeline, claims table, contradiction scan, action extraction, memory-candidate extraction, scoring criteria, examples.

**Definition of done:** source-summary outputs can be evaluated for evidence preservation, uncertainty, usefulness, and no-auto-promotion.

**Out of scope:** canonical writeback and broad agent autonomy.

## Phase 4 — Memory candidate review

**Purpose:** Build a controlled loop for memory suggestions.

**Deliverables:** raw/candidate/reviewed/promoted/stale/disputed/archive/rejected state handling, metadata requirements, review packets, tests.

**Definition of done:** Chaser agent can propose memory candidates and record review outcomes without promoting canonical ChaseOS memory.

**Out of scope:** self-directed memory mutation.

## Phase 5 — Tool/MCP mini-evals

**Purpose:** Test least-authority tool behavior before adding real tool integrations.

**Deliverables:** synthetic MCP/tool cases, resource-vs-tool classification, forbidden-write tests, schema validation checks.

**Definition of done:** tool-use evals catch overreach and schema failures without calling external services.

**Out of scope:** live MCP server authority or write tools.

## Phase 6 — Runtime adapter experiments

**Purpose:** Compare Hermes, OpenClaw, OpenAI/Codex, Ollama, and MCP lessons in bounded adapters.

**Deliverables:** adapter contracts, no-op/mock adapters, health-check shapes, failure-mode evals, authority-denial tests.

**Definition of done:** adapters remain mock or dry-run until evals prove boundaries.

**Out of scope:** live credential use, connector activation, browser control, protected-file writes.

## Phase 7 — Skill system / SkillOpt-style eval loop

**Purpose:** Treat skills as versioned, reviewed, eval-backed artifacts.

**Deliverables:** skill lifecycle, quarantine state, before/after eval harness, rollback path, source-summary skill pack tests.

**Definition of done:** skill changes require review and show measured improvement or no regression.

**Out of scope:** uncontrolled self-editing or auto-generated production skills.

## Phase 8 — Reviewed datasets and fine-tuning decision

**Purpose:** Decide whether training is justified after evidence exists.

**Deliverables:** reviewed golden/regression datasets, privacy classification, train/eval split proposal, model-risk review, fine-tuning decision memo.

**Definition of done:** operator can approve or reject fine-tuning based on dataset quality and eval evidence.

**Out of scope:** training execution unless explicitly approved later.

## Next two passes

1. Finish Phase 0C spec deepening and commit the docs/log pass.
2. Implement Phase 2 eval harness v0.2, unless a Phase 1 source-card harness gap blocks it.
