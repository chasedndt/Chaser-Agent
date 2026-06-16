# Chaser Agent

**Source intelligence. Review-first artifacts. Human-governed memory.**

Chaser Agent is a governed, local-first source-intelligence and harness-development repo derived from ChaseOS. It turns safe source inputs into structured review artifacts that separate what the source says, what the agent infers, what remains uncertain, what actions might follow, and what memory candidates may be worth human review.

ChaseOS remains the parent operating system/control plane and canonical governance owner. Chaser Agent is the focused product/runtime implementation and learning lab. It is not a foundation model, not production-ready autonomy, not a canonical truth engine, and not a replacement for ChaseOS.

---

## What is Chaser Agent?

Chaser Agent is the first focused agent product lane extracted from the broader ChaseOS control-plane work. Its current job is deliberately small: build a trustworthy source-to-review loop before adding live providers, runtime adapters, browser authority, fine-tuning, or autonomous execution.

The core idea is simple: an agent should not turn sources into a confident blob of prose. It should preserve evidence, label uncertainty, distinguish claims from inferences, propose next actions without taking them, and leave memory/canonical promotion to the human-governed ChaseOS layer.

## Why Chaser Agent exists

Modern AI workflows often collapse too many things into one answer: source facts, model guesses, recommended actions, memory updates, and public claims. That makes it hard to know what is grounded, what is speculative, what is safe to act on, and what should become durable knowledge.

Chaser Agent exists to make that boundary visible. It is a practical harness for learning and building agent systems where source fidelity, uncertainty, human review, evals, and governance come before power.

## The problem: ungoverned agent output

Most agent demos optimize for speed and autonomy. Chaser Agent starts from the opposite direction: before an agent can be useful at scale, it needs a behavior contract, safe input boundaries, clear output types, reviewable artifacts, and tests that prove the contract.

Without those boundaries, a repo can easily confuse smoke tests with product proof, source notes with truth, generated suggestions with memory, or future adapter docs with live authority.

## The solution: a review-first source loop

Chaser Agent V0 takes safe, reviewable source input and produces a deterministic local packet for human review:

```text
safe source input
→ intake metadata
→ source card
→ claims table
→ evidence snippets
→ uncertainty labels
→ contradiction notes
→ action candidates
→ memory candidates
→ human review packet
→ run log
→ no automatic canonical promotion
```

The output is intentionally review-only. It does not call an LLM provider, browse the web, mutate memory, edit ChaseOS canonical docs, or claim production readiness.

## Current status

Current work has completed **Phase 1 — Source Card Harness V0**.

What exists now:

- Layer 0 Behaviour Contract defining the product constitution;
- V0 Definition and Blueprint defining the first useful source-intelligence loop;
- a deterministic local Source Card Harness V0 under `src/chaser_agent/`;
- schema/smoke JSONL datasets under `evals/datasets/golden/`;
- tests that verify the local harness and contract-shaped outputs;
- review-only run artifacts under `logs/runs/<run_id>/` when the harness is executed.

What this means: Chaser Agent can already run a local toy source through the V0 source-card loop and produce structured review artifacts. It is still a bounded harness foundation, not a live autonomous runtime.

## Core capabilities

- **Source cards** — structured summaries of safe source inputs.
- **Claims tables** — source-grounded claims kept separate from model/agent inference.
- **Evidence snippets** — traceable excerpts that support review.
- **Uncertainty labels** — explicit uncertainty, missing context, and contradiction markers.
- **Action candidates** — proposed next actions that require human acceptance.
- **Memory candidates** — possible durable-memory updates that are not promoted automatically.
- **Human review packets** — review-ready bundles for deciding what, if anything, should become action, memory, spec, eval, or canonical truth.
- **Run logs** — local deterministic evidence of what the harness produced.

## Relationship to ChaseOS

Chaser Agent inherits ChaseOS principles but does not replace ChaseOS.

ChaseOS owns:

- canonical truth;
- governance and permission boundaries;
- runtime authority;
- promotion rules;
- operator memory and durable system state.

Chaser Agent owns, inside this repo:

- product implementation experiments;
- source-intelligence harness code;
- eval and dataset scaffolding;
- review artifact schemas;
- learning-oriented docs for AI engineering, evals, retrieval, memory, and runtime governance.

The boundary matters: Chaser Agent may propose; ChaseOS governance decides what becomes durable truth.

## What Chaser Agent is not yet

Chaser Agent is not currently:

- a production autonomous agent;
- a foundation model;
- a live provider/API routing system;
- a Hermes, OpenClaw, Codex, MCP, or browser-control adapter;
- a fine-tuning, PEFT, or LoRA pipeline;
- a private dataset ingestion system;
- a canonical memory owner;
- all 17 architecture layers implemented.

Those lanes remain deferred until the behavior contract, reviewed data, eval evidence, and governance boundaries are strong enough to support them.

## Repo safety rules

- Do not commit `.env`, secrets, credentials, private datasets, cookies, tokens, or raw personal logs.
- Do not mutate ChaseOS canonical docs from this repository.
- Do not activate provider/API/browser/runtime adapters by default.
- Do not auto-promote memory candidates into durable memory or ChaseOS truth.
- Do not claim production readiness or full autonomy.
- Keep generated artifacts review-only unless the operator explicitly approves promotion elsewhere.

## Local verification

From the repo root:

```bash
.venv/bin/python -m scripts.validate_jsonl evals/datasets/golden/*.jsonl
PYTHONPATH=. .venv/bin/python -m pytest -q
```

## Weekly research-upgrade workflow

Chaser Agent now has a ChaseOS-governed weekly research-intake lane for discovering agent-harness, coding-agent, computer-use, memory/context, tool-routing, and eval research that could become future harness RFCs.

Current state is **Phase 1A complete: deterministic dry-run + bounded Hermes cron active**:

```bash
.venv/bin/python scripts/weekly_research_intake_dry_run.py --out logs/runs
```

This validates:

- `research_intake/sources.yaml`
- `research_intake/queries.yaml`
- `research_intake/ranking.yaml`
- `research_intake/cron_proposal.yaml`

The active Hermes cron is script-backed and bounded:

- Name: `Chaser Agent weekly research intake dry-run`
- Schedule: `0 5 * * 1`
- Hermes job id on the local ChaseOS machine: `88bb31188587`
- Wrapper: `/home/chaseos/runtimes/hermes-home/scripts/chaser_agent_weekly_research_intake_dry_run.sh`
- Output: `logs/runs/weekly-research-intake-dry-run-*/manifest.json` and `digest.md`

Control-plane boundary: this cron validates local config and reports a short artifact summary only. It does **not** fetch network sources yet, call model providers, activate credentials, create branches, open PRs, merge code, mutate memory, expand permissions, deploy, or promote ChaseOS canonical truth.

The intended upgrade ladder is:

```text
research sources -> normalized paper cards -> ranked weekly digest -> RFC candidates -> isolated candidate branches -> private eval gates -> human/Gate-approved merge
```

See `docs/07_Research/ChaseOS-Weekly-Research-Upgrade-Setup-Order.md` for the implementation order and approval gates.

Phase 1B has started with bounded arXiv API ingestion:

```bash
PYTHONPATH=. .venv/bin/python -m research_intake.ingest \
  --max-results 25 \
  --query 'cat:cs.AI AND (agent OR harness OR tool use)' \
  --out research_intake/data
```

This writes ignored local artifacts under `research_intake/data/arxiv-ingest-*` and keeps provider/model calls, candidate implementation, PR/merge automation, permission expansion, and canonical promotion disabled.

## Run Source Card Harness V0

```bash
.venv/bin/python -m chaser_agent.cli source-card \
  --input examples/sources/toy_website_design_note.md \
  --out logs/runs
```

The command prints a unique run folder containing:

- `source_card.json`
- `claims_table.json`
- `evidence_snippets.json`
- `uncertainty_labels.json`
- `action_candidates.json`
- `memory_candidates.json`
- `human_review_packet.json`
- `run_log.json`

Outputs are deterministic, local, and review-only.

## Start reading

Read these first:

1. `START_HERE.md`
2. `docs/00_START_HERE.md`
3. `docs/01_Product/Chaser-Agent-Layer-0-Behaviour-Contract.md`
4. `docs/01_Product/Chaser-Agent-V0-Definition.md`
5. `docs/01_Product/Chaser-Agent-V0-Blueprint.md`
6. `docs/03_Summary_Intelligence/Chaser-Agent-V0-Source-Card-Schema.md`
7. `docs/02_Evals/Chaser-Agent-V0-Human-Review-Packet.md`

## Public positioning

The honest public description is:

> Chaser Agent is a local-first, review-first source-intelligence harness for turning safe inputs into evidence-preserving review artifacts under human governance.

Do not describe it as production autonomy, a finished personal AI, a live runtime adapter, a deployed provider stack, or a fine-tuned model.
