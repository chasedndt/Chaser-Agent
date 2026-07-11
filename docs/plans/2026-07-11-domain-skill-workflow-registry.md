# Chaser Agent Domain Skill and Workflow Registry

**Registry status:** planning seed; no authority granted by inclusion

**Harness:** Chaser Agent, computer-local and ChaseOS-governed

## Registry contract

A domain pack is a reusable Chaser Agent capability bundle. Every pack must eventually declare:

- domain and pack ID;
- problem and intended operator outcome;
- skill/workflow contracts;
- typed inputs and outputs;
- tools, sources, and deny rules;
- datasets and fixture provenance;
- eval suites and readiness thresholds;
- memory/context behavior;
- failure taxonomy and observability;
- approval and authority ceiling;
- rollback/disable path;
- review cadence;
- training or fine-tuning decision status.

A pack's presence in this registry means **planned or bounded**, not activated.

## Seed packs

### `source_intelligence_v0`

- **Purpose:** evidence-preserving source cards, claims, uncertainty, action/memory candidates, and review packets.
- **Current state:** bounded deterministic V0 foundation.
- **Authority:** local/review-only.
- **Role:** cross-domain intake and evidence substrate.

### `social_growth_control_v0`

- **Purpose:** public-safe research, content strategy, human-voice drafts, media QA, channel analytics, audience/community workflows, and approval-gated publishing.
- **Current state:** future governed track; ChaseOS X is an initial pilot, not the product identity.
- **Authority:** research/draft/review only until separate action approval contracts exist.
- **Plan:** `2026-07-11-social-publishing-harness-direction.md`.

### `trading_market_intelligence_v0`

- **Purpose:** StrikeZone evidence/scenarios, normalized signals, TradeSync paper/digital-twin state, independent risk checks, and governed evaluation.
- **Current state:** observation and evaluation-data foundation.
- **Authority:** no live trading, exchange, wallet, or credential action.
- **Identity rule:** one domain methodology, not Chaser Agent's primary purpose.

### `web_ui_design_v0`

- **Purpose:** product research, information architecture, design systems, prototypes, frontend implementation, responsive/accessibility checks, visual-completion evaluation, and approval-gated deployment.
- **Current state:** planned domain pack; visual-completion evaluator work may supply shared fixtures and gates.
- **Authority:** local build/test/preview by default; deploy/publish requires separate approval.

### `software_delivery_v0`

- **Purpose:** repository inspection, planning, TDD, debugging, code review, CI diagnosis, handoff, and governed branch/PR workflows.
- **Current state:** planned consolidation of existing bounded engineering methods.
- **Authority:** repo-scoped; merge/deploy/release separately gated.

### `business_operations_v0`

- **Purpose:** bounded research, deliverable preparation, lead/workflow operations, commercial review packets, and approval routing.
- **Current state:** future pack family.
- **Authority:** no unsupervised outreach, payment, account, or public action.

### `personal_computer_workflows_v0`

- **Purpose:** local files, notes, planning, computer-use, and operator assistance on the user's computer.
- **Current state:** future personal harness family.
- **Authority:** least-privilege, task-scoped, inspectable, and reversible.

## Shared learning progression

```text
method/source intake
→ reviewed workflow contract
→ fixtures and datasets
→ deterministic or shadow implementation
→ held-out evals
→ private operator review
→ bounded skill activation
→ outcome observation
→ governed improvement proposal
→ optional training decision after evidence
```

No pack may silently retrain itself, mutate policy, expand tools, publish, deploy, move money, or promote memory because an outcome was observed.

## Next registry action

Create the current repository/system map, then define the shared `domain_pack_v1` schema and instantiate it for source intelligence, social media, trading, and web/UI design without activating new authority.
