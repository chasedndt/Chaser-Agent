# Chaser Agent

**Standalone-first. Local-first. Evidence-linked. Human-governed. ChaseOS-enhanced.**

Chaser Agent is a standalone-first, local-first agent harness for turning goals and sources into evidence-linked, reviewable work. Its MIT-licensed core runs independently, learns from explicit human review, preserves approved local memory, and curates a user-owned provenance map. Optional ChaseOS integration adds shared governance, cross-runtime orchestration, shared canonical state, policy, approvals, routing, and cross-project memory.

> Chaser Agent is a persistent, approval-gated agent harness for real-world personal and business workflows. It compiles sources, evidence, memory, goals, and operator preferences into contextual proposals and controlled action.

## Identity canon

- Public product name: **Chaser Agent**.
- Canonical category: **persistent approval-gated agent harness**.
- ChaseOS relationship: **Runs independently. Works best with ChaseOS.**
- Human authority: generated output, learned preference, or agent confidence never grants permanent permission.
- Visual canon: [character specification](docs/brand/chaser-agent/CHASER-AGENT-CHARACTER-CANON-AND-VISUAL-SPEC.md) and [production roadmap](docs/brand/chaser-agent/CHASER-AGENT-FULL-ASSET-ROADMAP-AND-PRODUCTION-SPEC.md).

This is product and identity canon, not a claim that the current P0.1 implementation is a continuously running production agent. Current implementation truth remains below.

## Product boundary

The MIT-licensed core must run without ChaseOS. It must not import ChaseOS, a provider SDK, MCP runtime, or browser runtime.

Deployment-scoped durable state:

```text
standalone: human-approved durable local state
ChaseOS-integrated: ChaseOS-governed shared canonical state
```

In both modes:

```text
generated output != approved truth
memory candidate != memory
action candidate != action
review packet != approval
integration packet != dispatch
agent confidence != authority
```

See:

- [Product narrative and utility](docs/01_Product/Chaser-Agent-Product-Narrative-and-Utility.md)
- [Standalone and ChaseOS architecture](docs/01_Product/Chaser-Agent-Standalone-vs-ChaseOS-Architecture.md)
- [Layer 0 Behaviour Contract](docs/01_Product/Chaser-Agent-Layer-0-Behaviour-Contract.md)
- [Layer 0 + 17-layer engineering architecture](docs/01_Product/Chaser-Agent-17-Layer-Architecture.md)
- [Case-study workflow evaluation system](docs/02_Evals/Chaser-Agent-Case-Study-Workflow-Eval-System.md)
- [P0.1 open decisions](docs/01_Product/Chaser-Agent-P0.1-Open-Decisions.md)

## Current maturity

Chaser Agent is a **P0.1 / pre-alpha standalone deterministic harness** on the review branch. The implementation is locally verified but not merged or released; promotion terminology and operator acceptance remain open.

Verified P0.1 implementation:

- domain-neutral deterministic Source Card Harness with explicit workflow profiles;
- source card, claims, evidence, uncertainty, action, memory-candidate, review-packet, and run-log artifacts;
- immutable human-review records in SQLite;
- accepted/rejected memory-candidate writeback with append-only lifecycle history;
- governance-gated local promotion and audit records;
- lexical, scope, type, tag, status, and recency memory retrieval without embeddings;
- SQLite provenance nodes, edges, and source-to-memory trace queries;
- optional inactive ChaseOS proposal adapter with no dispatch;
- artifact-field Layer 0 contract runner;
- 30 public-safe Layer 0 contract cases with 154 executable assertions, all `pending_operator_review`;
- structural case-study workflow episodes and deterministic trace scoring for dependencies, evidence, authority, artifacts, proof, and handoff;
- bounded SkillGate;
- metadata-only visual-completion evaluator;
- explicit public arXiv ingestion and separate config-only weekly research dry run;
- seven golden JSONL files with three rows each;
- one 30-row Layer 0 contract dataset;
- one public-safe MarginFlip-derived workflow episode and candidate structural trace, both explicitly non-golden pending operator review;
- generated [current test matrix](docs/02_Evals/Chaser-Agent-Current-Test-Matrix.md) with exact values and honest maturity labels.

Passing tests prove deterministic contracts and structural checks, not product-quality intelligence. Layer 0 cases and case-study episodes remain pending operator review until the operator supplies labels and corrections.

## Core utility

```text
goal, question, source, or bounded task
-> trust and privacy classification
-> source-grounded claims and evidence
-> separate Chaser Agent inference
-> uncertainty and contradiction status
-> safe action candidates
-> relevant reviewed-memory retrieval
-> memory candidates
-> human review and correction
-> governance-controlled durable state
-> provenance-first knowledge map
```

The deterministic implementation remains a reference baseline, test oracle, fallback, and auditable comparison point. Models may be introduced later only behind provider-neutral interfaces and reviewed eval/data policy.

## Domain-neutral profiles

Domain behaviour belongs in a workflow profile, never in the default core.

P0.1 profiles:

- `general_source_review` — default, conservative, source-neutral;
- `ai_engineering_research_review` — technical claims, methods, limitations, baselines, eval and RFC questions;
- `website_design_review` — hierarchy, contrast, spacing, readability, restraint, user intent, and missing visual proof.

Profiles shape analysis only. They cannot grant permissions, call providers/tools, execute actions, or promote memory.

## What Chaser Agent is not

Chaser Agent is not currently:

- a foundation model;
- production autonomy;
- a finished personal AI;
- a website-design, media-generation, or trading-execution agent;
- a public FastAPI service or web UI;
- a live provider router;
- a semantic RAG/vector system;
- a live MCP/tool registry;
- a browser/computer-use runtime;
- an autonomous planner/executor;
- a fine-tuning, LoRA, or PEFT pipeline;
- all 17 layers implemented.

## Safety rules

- Never commit `.env`, credentials, tokens, private keys, private datasets, raw personal logs, or local SQLite state.
- Never infer authority from a workflow profile, skill, adapter, provider, or confidence score.
- Never auto-promote a memory candidate.
- Never mutate original run artifacts during review or correction.
- Never activate providers, tools, MCP, browsers, public actions, payments, trading, deployment, or model training in P0.1.
- Treat URL tool scopes as exact scheme, host, effective port, and canonical path boundaries; a string prefix is never authority.
- Never mutate ChaseOS canonical state from the standalone core.
- Keep generated run and research artifacts ignored unless separately reviewed for provenance, privacy, and licensing.

## Verification

From WSL or another POSIX shell using the repository virtual environment:

```bash
.venv/bin/python -m pytest -q
.venv/bin/python -m scripts.validate_jsonl evals/datasets/golden/*.jsonl evals/datasets/contract/*.jsonl evals/datasets/case_studies/public_pending/*.jsonl
```

Run the deterministic source-review path:

```bash
.venv/bin/python -m chaser_agent.cli source-card \
  --input examples/sources/toy_website_design_note.md \
  --out logs/runs \
  --profile website_design_review
```

Persist a human review into an explicit local database without modifying the run folder:

```bash
.venv/bin/python -m chaser_agent.cli review logs/runs/<run-id> \
  --database /safe/local/path/chaser-agent.db \
  --reviewer-id <local-operator-id> \
  --source-fidelity-score 3 \
  --inference-separation-score 3 \
  --uncertainty-handling-score 2 \
  --action-usefulness-score 2 \
  --memory-safety-score 3 \
  --decision pass
```

The default database is `~/.chaser-agent/chaser-agent.db`. Review may create reviewed/rejected memory records for explicitly selected candidate IDs, but it never promotes them.

Run the Layer 0 contract seed:

```bash
PYTHONPATH=src .venv/bin/python -m chaser_agent.cli contract-eval \
  --input evals/datasets/contract/layer0_contract_seed.jsonl \
  --out logs/runs/contract-eval-results.jsonl
```

Generated output remains review-only. The 30 contract rows provide executable family depth, not operator-reviewed golden data.

Validate and structurally score a public-safe case-study workflow episode:

```bash
PYTHONPATH=src .venv/bin/python -m chaser_agent.cli workflow-episode-validate \
  --input evals/datasets/case_studies/public_pending/marginflip_marketing_foundation.jsonl

PYTHONPATH=src .venv/bin/python -m chaser_agent.cli workflow-trace-eval \
  --episodes evals/datasets/case_studies/public_pending/marginflip_marketing_foundation.jsonl \
  --traces evals/traces/public_pending/marginflip_marketing_foundation_candidate.jsonl \
  --out logs/runs/marginflip-workflow-trace-results.jsonl
```

## Separate research-intake lane

The weekly dry run validates local YAML configuration only:

```bash
.venv/bin/python scripts/weekly_research_intake_dry_run.py --out logs/runs
```

Public arXiv ingestion is a separate explicit command:

```bash
PYTHONPATH=. .venv/bin/python -m research_intake.ingest \
  --max-results 25 \
  --query 'cat:cs.AI AND (agent OR harness OR tool use)' \
  --out research_intake/data
```

It writes ignored local raw/normalized artifacts. Neither lane calls a model provider, implements candidates, promotes memory, or grants execution authority.

## Read next

1. [Start Here](START_HERE.md)
2. [Layer 0](docs/01_Product/Chaser-Agent-Layer-0-Behaviour-Contract.md)
3. [Product narrative](docs/01_Product/Chaser-Agent-Product-Narrative-and-Utility.md)
4. [Standalone architecture](docs/01_Product/Chaser-Agent-Standalone-vs-ChaseOS-Architecture.md)
5. [V0 Definition](docs/01_Product/Chaser-Agent-V0-Definition.md)
6. [V0 Blueprint](docs/01_Product/Chaser-Agent-V0-Blueprint.md)
7. [Roadmap](docs/01_Product/Chaser-Agent-Roadmap.md)
