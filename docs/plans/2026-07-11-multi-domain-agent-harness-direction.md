# Chaser Agent — Multi-Domain Agent Harness Direction Plan

**Status:** future multi-domain architecture direction; bounded review-first harness today

**Governance owner:** ChaseOS

**Harness/orchestration product:** **Chaser Agent** (not “Chase Agent”)

## Naming and scope correction

All architecture references must use **Chaser Agent** for the agent harness and orchestration layer. “Chase Agent” is not the product/runtime name.

Chaser Agent is not primarily a trading agent. Trading is one governed skill/workflow family among many that Chaser Agent can learn to run through reusable skills, datasets, evals, workflow contracts, tools, and approval boundaries.

Chaser Agent lives on the operator's computer as the personal multi-layer agent harness. Its long-range purpose is to coordinate many domain capabilities without collapsing them into one unrestricted agent.

## Current truth

Chaser Agent is currently a bounded, local-first, review-first source-intelligence and harness-development repo. It is not a live trading runtime, execution gateway, risk engine, exchange adapter, production provider stack, or self-training system.

The current StrikeZone evaluation substrate has only an initial genuine thesis/scenario cohort. That infrastructure produces future training/evaluation data, but it is not literal model training and must not trigger live strategy mutation.

## Multi-domain skill and workflow model

Chaser Agent should grow as a governed library of domain packs rather than as a single-purpose agent. Each pack should have its own:

- skill and workflow contracts;
- typed inputs, outputs, and artifacts;
- source/tool allowlists;
- datasets and evaluation fixtures;
- failure taxonomy and observability;
- approval and authority ceiling;
- review cadence and rollback path;
- training/fine-tuning decision gate when evidence eventually justifies it.

Initial domain families include:

### Social media growth and control

Research, content strategy, drafting, scheduling proposals, channel analytics, audience/community workflows, brand consistency, and approval-gated publishing. Account mutation and public posting remain separately authorized capabilities.

### Trading and market intelligence

StrikeZone evidence/scenarios, normalized market signals, TradeSync paper/digital-twin state, independent risk controls, and disabled-by-default execution progression. This is one methodology/system pack, not Chaser Agent's primary identity.

### Web and UI design

Product research, information architecture, design systems, prototyping, implementation, accessibility, responsive QA, visual-completion evaluation, and approval-gated deployment.

### Source intelligence and research

The current Source Card Harness, claims/evidence separation, uncertainty, review packets, research intake, and governed memory candidates remain foundational cross-domain capabilities.

### Future packs

Additional personal, business, coding, operations, content, data, and computer-use workflows can be added only through the same skill/eval/authority discipline.

The seed registry is maintained in [`2026-07-11-domain-skill-workflow-registry.md`](2026-07-11-domain-skill-workflow-registry.md).

## Long-range role

Chaser Agent is the future multi-domain orchestration and agent-harness plane connecting governed specialist lanes. A trading workflow is one example:

```text
Chaser Agent multi-domain harness
├── source intelligence and research
├── social media strategy and governed publishing
├── web/UI design, implementation, and visual QA
├── coding and software-delivery workflows
├── personal/business operations
└── trading and market-intelligence pack
    ├── market-data agents
    ├── indicator/signal agents
    ├── StrikeZone thesis/scenario agent
    ├── independent risk agent
    ├── TradeSync simulation/paper-trading agent
    ├── disabled-by-default execution agent
    └── review/evaluation agents
```

Chaser Agent should own:

- permissions and capability boundaries;
- context assembly and task routing;
- retries, timeouts, failure taxonomy, and observability;
- source/evidence lineage;
- approval and audit handoffs;
- isolated specialist-agent coordination;
- deterministic separation of signal, thesis, trade candidate, and order objects.

Chaser Agent must not combine unrestricted research, strategy, risk, and order authority in one agent.

## System ownership map

| Plane | Owner / role |
|---|---|
| Evidence, indicators, structured market scenarios | StrikeZone Crypto |
| Simulated trade state, portfolio ledger, journal, reconciliation | TradeSync |
| Agent orchestration, permissions, planning, tool control | Chaser Agent |
| Independent exposure and execution constraints | Dedicated risk engine |
| Deterministic low-latency signals | TradingView/Pine and market-data adapters |
| Approval, audit, operator interface, canonical governance | ChaseOS |

The risk engine remains independent and cannot be overridden through prompts or Chaser Agent reasoning.

## Authority progression

```text
Level 0 — observation only                     (current)
Level 1 — structured trade candidates
Level 2 — paper trading / digital twin
Level 3 — shadow live trading, no orders sent
Level 4 — human-approved live orders
Level 5 — bounded autonomous execution
```

Every level requires a separate evidence-backed, operator-approved contract. No level inherits authority merely because implementation exists.

## Architectural workstreams

### A. Market-data plane

Prefer stable APIs/WebSockets for execution-critical prices, trades, order books, liquidations, funding, open interest, volatility, macro state, and exchange health. Keep browser research such as YouTube, X, Grok, Perplexity, and TradingView Ideas outside low-latency decision paths.

### B. Signal normalization

Define immutable, versioned signal objects with source, asset, timeframe, observation/expiry times, conditions, invalidation, evidence lineage, and `trade_instruction: false`. Preserve strict object boundaries:

```text
signal ≠ thesis ≠ trade candidate ≠ order
```

### C. Scenario and policy plane

Use StrikeZone structured scenarios for regime, activation, invalidation, no-trade filters, conflicts, and cross-market dependencies. Do not convert ambiguous prose into executable conditions.

### D. Paper-trading digital twin

Before execution authority, model entry delay, spread, fees, slippage, partial/missed fills, funding, leverage, liquidation distance, stops/targets, latency, rejections, concurrent exposure, and correlated BTC/ETH/SOL risk. TradeSync is the intended trade-state and reconciliation substrate.

### E. Independent risk engine

Future contracts must cover maximum account/day risk, leverage, position size, correlated exposure, open-position count, volatility sizing, funding limits, event blackout, stale data, venue health, mandatory invalidation, and a global kill switch.

### F. Execution gateway

Keep disabled until separately approved. Shadow mode records the exact order candidate that would have been submitted but sends nothing. Human approval precedes any live order stage.

### G. Evaluation and learning

Build datasets, diagnostics, offline experiments, feature/source contribution studies, and governed parameter-change proposals. Do not silently update live strategy parameters after individual outcomes.

- 3.5-day loop: operational reliability, freshness, binding, simulator, transport, and data health.
- Weekly loop: descriptive scenario aging, source/indicator research, cost-aware strategy experiments, and approval-gated proposals.
- Neither loop may expand its own authority.

## Cadence model

| Cadence | Work |
|---|---|
| Sub-second to seconds | Price, order book, trades, exchange health |
| 30 seconds–5 minutes | Indicators, funding/OI deltas, volatility, risk state, candidate evaluation |
| 15–60 minutes | Scenario/technical/liquidity/macro refresh |
| Daily | Director thesis and source synthesis |
| 3.5 days | Operational QA |
| Weekly | Scenario aging and governed methodology research |

## Repository plan integration

This direction is a long-range architecture track, not the immediate V0 implementation pass. The current next work remains Source Card Harness Review / Contract Eval Seeds and existing bounded eval/harness improvements.

Before advancing toward trading levels, create a current repository/system map covering:

- Chaser Agent modules and capability boundaries;
- StrikeZone indicators, scenarios, and webhook payloads;
- TradeSync data model and simulation surfaces;
- market-data and research adapters;
- risk contracts and kill-switch ownership;
- execution adapters and disabled/active states;
- storage, lineage, and deployment topology;
- ChaseOS and Discord control-plane routes.

## Non-negotiable gates

- No live trades, exchange/wallet actions, or credentials in current phases.
- No public/member publishing without approval.
- No execution-critical dependency on browser research.
- No autonomous source/confidence/methodology mutation.
- No model-training claim without reviewed datasets and an approved training decision.
- No risk-engine override by Chaser Agent or any specialist agent.
- No execution activation without explicit ChaseOS/operator approval and audit evidence.
