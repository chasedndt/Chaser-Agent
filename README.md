# Chaser agent

**Standalone-first. Local-first. Evidence-linked. Human-governed. ChaseOS-enhanced.**

Chaser agent is an open-source agent harness for turning goals and sources into evidence-linked, reviewable work. It runs independently, learns from explicit human review, preserves approved local memory, and curates a user-owned provenance map. Optional ChaseOS integration adds shared governance, cross-runtime orchestration, shared canonical state, policy, approvals, routing, and cross-project memory.

> Chaser agent is an open-source, standalone-first, local-first agent harness that turns goals and sources into evidence-linked work, learns from human review, preserves approved memory, and curates a user-owned knowledge map. It works independently and becomes more powerful when connected to ChaseOS.

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
- [P0.1 open decisions](docs/01_Product/Chaser-Agent-P0.1-Open-Decisions.md)

## Current maturity

Chaser agent is a **P0 / pre-alpha deterministic harness foundation** with an approved P0.1 redesign under review.

Verified before P0.1 implementation:

- deterministic local Source Card Harness V0;
- source card, claims, evidence, uncertainty, action, memory-candidate, review-packet, and run-log artifacts;
- optional ChaseOS-shaped review packet with no dispatch;
- artifact-field Layer 0 contract runner;
- six public-safe contract seeds, all `pending_operator_review`;
- bounded SkillGate;
- metadata-only visual-completion evaluator;
- explicit public arXiv ingestion and separate config-only weekly research dry run;
- 33 deterministic tests;
- seven golden JSONL files with three rows each;
- one six-row Layer 0 contract seed file.

P0.1 approved target:

- domain-neutral source-review core;
- explicit workflow profiles;
- immutable local operator-review records;
- standalone local governance;
- SQLite memory lifecycle outside the repository;
- lexical/tag retrieval without embeddings;
- provenance-first SQLite knowledge map;
- optional inactive ChaseOS adapter;
- exact test-matrix export.

P0.1 implementation status must be taken from the current branch/build log, not inferred from this target list.

## Core utility

```text
goal, question, source, or bounded task
-> trust and privacy classification
-> source-grounded claims and evidence
-> separate Chaser agent inference
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

## What Chaser agent is not

Chaser agent is not currently:

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
- Never mutate ChaseOS canonical state from the standalone core.
- Keep generated run and research artifacts ignored unless separately reviewed for provenance, privacy, and licensing.

## Verification

From WSL or another POSIX shell using the repository virtual environment:

```bash
.venv/bin/python -m pytest -q
.venv/bin/python -m scripts.validate_jsonl evals/datasets/golden/*.jsonl evals/datasets/contract/*.jsonl
```

Run the deterministic source-review path:

```bash
.venv/bin/python -m chaser_agent.cli source-card \
  --input examples/sources/toy_website_design_note.md \
  --out logs/runs
```

Run the Layer 0 contract seed:

```bash
PYTHONPATH=src .venv/bin/python -m chaser_agent.cli contract-eval \
  --input evals/datasets/contract/layer0_contract_seed.jsonl \
  --out logs/runs/contract-eval-results.jsonl
```

Generated output remains review-only. The six contract rows are wiring seeds, not reviewed coverage.

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
