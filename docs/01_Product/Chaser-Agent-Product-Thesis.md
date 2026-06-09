# Chaser agent Product Thesis

## One-paragraph thesis

**Chaser agent** is a governed, eval-first AI product/runtime lab for turning messy sources into reviewable source cards, scoped action candidates, and memory candidates without silently mutating ChaseOS canonical truth. Its first wedge is not broad autonomy or provider orchestration; it is a source-summary and eval harness that proves whether Chaser agent can preserve evidence, label uncertainty, surface useful next actions, and route memory suggestions through human review.

## What Chaser agent is

Chaser agent is:

- a focused product/runtime implementation repo derived from ChaseOS concepts;
- an eval lab for source summaries, action extraction, memory-candidate extraction, citation grounding, workflow judgement, and later tool/MCP behavior;
- a place to develop implementation code, tests, datasets, rubrics, skills, and adapter notes before anything is promoted into ChaseOS canonical governance;
- a human-in-the-loop system where output quality is measured by repeatable evals and operator judgement;
- a staging ground for future fine-tuning candidates only after eval evidence and reviewed datasets exist.

## What Chaser agent is not

Chaser agent is not:

- a replacement for ChaseOS;
- a canonical truth owner;
- a production autonomous runtime today;
- a permission bypass for ChaseOS Gate, AOR, provider authority, browser authority, or protected-file writes;
- a fine-tuning project yet;
- a place to ingest private logs, credentials, or raw personal datasets without explicit privacy handling;
- a general chatbot that can make unsupported claims and call them knowledge.

## Relationship to ChaseOS

ChaseOS remains the parent operating system, governance layer, approval system, and durable truth layer. Chaser agent may reference ChaseOS architecture, runtime boundaries, and public/product framing, but it does not silently update ChaseOS canonical docs. Chaser agent proposes, tests, and records; ChaseOS governance decides canonical promotion.

## First product wedge

The first product wedge is:

```text
input source
→ source card
→ claims
→ evidence snippets
→ uncertainty labels
→ contradiction scan
→ action candidates
→ memory candidates
→ JSONL eval rows
→ human review
→ run log
```

This wedge is small enough to test, useful enough to guide real work, and foundational enough to support later memory, tool, runtime, and skill layers.

## Target users / operators

Initial users are:

- the ChaseOS operator who needs grounded summaries and reviewable decisions;
- agent builders comparing Hermes, OpenClaw, Codex, MCP, Ollama, and skill systems;
- reviewers who need clear evidence packets before accepting memory, actions, roadmap changes, or dataset rows;
- future contributors who need enough specification depth to build safely without relying on chat context.

## Core value proposition

Chaser agent helps the operator convert raw research, project notes, product observations, and runtime lessons into structured artifacts that can be evaluated and reviewed. Its value is not “more text”; it is provenance, uncertainty, scoreable behavior, and controlled promotion paths.

## Why eval-first matters

Eval-first development prevents vague “agent quality” claims. Every feature should have:

- an input shape;
- expected output properties;
- failure modes;
- a rubric or deterministic check;
- a regression case;
- human review criteria when judgement is needed.

A feature is not real until it has an eval, a known failure mode, and a regression check.

## Why human review matters

Human review prevents automatic promotion from becoming hidden authority. Chaser agent can propose memory, actions, skill edits, roadmap impacts, or research signals, but an operator must decide whether they are correct, useful, safe, and aligned with ChaseOS.

## Why fine-tuning comes later

Fine-tuning, LoRA, PEFT, and model editing require high-quality training examples, stable evals, privacy discipline, and known failure patterns. Chaser agent must first build golden datasets, result logs, and human-reviewed examples. Training before eval evidence would amplify unknown errors.

## Public positioning

Publicly, Chaser agent should be described as a governed AI-agent evaluation and source-intelligence project. It should not be marketed as production autonomy, self-modifying intelligence, or a canonical memory brain until those capabilities exist and have been reviewed.

## Implementation status labels

Use these labels consistently:

| Label | Meaning |
|---|---|
| Scaffolded | File/module exists but behavior is starter-level. |
| Planned | Spec exists; implementation not started. |
| Active V0 | Small implementation exists and is covered by tests. |
| Human-reviewed | Output requires operator judgement before promotion. |
| Later | Intentionally deferred. |
| Not active | Explicitly blocked for the current phase. |

## Current phase non-goals

Phase 0C does not:

- activate provider calls;
- implement Hermes/OpenClaw runtime adapters;
- add browser/computer-use authority;
- create private datasets;
- fine-tune or prepare LoRA data;
- mutate ChaseOS canonical docs;
- claim all 17 layers are implemented.
