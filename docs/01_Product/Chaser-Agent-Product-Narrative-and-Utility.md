# Chaser Agent Product Narrative and Utility

**Status:** APPROVED product direction for P0.1.

## Canonical statement

> Chaser Agent is an open-source, standalone-first, local-first agent harness that turns goals and sources into evidence-linked work, learns from human review, preserves approved memory, and curates a user-owned knowledge map. It works independently and becomes more powerful when connected to ChaseOS.

## Core utility

Chaser Agent should help a human turn a goal, question, source, or bounded task into work that remains inspectable over time. Its core job is to preserve evidence and provenance while making review, correction, memory, and later governed execution possible.

The domain-neutral loop is:

```text
goal, question, source, or bounded task
-> trust and privacy classification
-> source-grounded claims and evidence
-> separate agent inference
-> uncertainty and contradiction status
-> safe action candidates
-> relevant reviewed-memory retrieval
-> memory candidates
-> human review and correction
-> governance-controlled durable state
-> provenance-first knowledge map
```

## What the core is excellent at first

P0.1 is a deterministic, CLI-first reference implementation for source review and human-governed local state. It is intentionally provider-free and tool-free. Its first quality target is not eloquent prose; it is the ability to answer:

- What did the source say?
- Which evidence supports each claim?
- What did Chaser Agent infer?
- What remains uncertain or unevaluated?
- Which reviewed memory influenced the output?
- What did the human accept, correct, or reject?
- Which durable record resulted?
- How can that record be traced back to its source, run, and review?

## Open-source position

The independent core is MIT-licensed, self-hostable, modifiable, redistributable, and usable without ChaseOS. The core must not acquire a proprietary runtime dependency.

Future hosted services, managed connectors, enterprise policy packs, premium providers, and proprietary ChaseOS layers must remain separable from the open-source core.

## ChaseOS relationship

Chaser Agent originated from ChaseOS governance and source-intelligence work. ChaseOS remains the optional integrated control plane for shared policy, approvals, cross-runtime orchestration, shared canonical state, and cross-project memory.

Standalone mode does not imitate all of ChaseOS. It implements only the local human-governed foundations needed for an independent product. ChaseOS integration is additive and stays behind an adapter boundary.

## Domain profiles

The core is domain-neutral. AI-engineering research, website design, trading research, business research, university learning, media work, cybersecurity, and repository review belong in explicit workflow profiles or skill packs.

P0.1 profiles:

- `general_source_review` — default, conservative, source-neutral;
- `ai_engineering_research_review` — research claims, limitations, baselines, eval and RFC questions;
- `website_design_review` — hierarchy, contrast, spacing, readability, restraint, user intent, and missing visual evidence.

A profile shapes analysis. It never grants permissions.

## Honest current positioning

The repository currently proves a deterministic source-card shape, selected Layer 0 invariants, a bounded SkillGate, metadata-only visual evaluation, and separate public-research ingestion. P0.1 adds standalone review/memory/knowledge foundations on a review branch.

It does not prove production autonomy, semantic intelligence, private-data safety, live provider/tool governance, browser execution, model training, or all 17 layers.

## Public non-goals

Chaser Agent is not currently a foundation model, production autonomous operator, finished personal AI, website-design agent, trading executor, media-generation agent, public API service, provider router, semantic RAG system, MCP runtime, browser worker, or fine-tuning pipeline.
