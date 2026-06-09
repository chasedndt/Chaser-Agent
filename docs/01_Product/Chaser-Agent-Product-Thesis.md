# Chaser agent Product Thesis

## One-paragraph thesis

Chaser agent is a governed, eval-aware source-intelligence and harness-development product derived from ChaseOS. Its first useful version does not try to become a fully autonomous agent; it defines Layer 0 behavior, then turns safe sources into reviewable artifacts that separate source claims, Chaser agent inferences, uncertainty, actions, and memory candidates while preserving human review and ChaseOS canonical-promotion boundaries.

## What Chaser agent is

- a focused product/runtime implementation repo;
- a source-summary and harness foundation;
- a learning path for AI engineering, maths, CS, evals, and runtime governance;
- a place to develop reviewable artifacts before production claims;
- a future eval and adapter lab after Layer 0 behavior is defined.

## What Chaser agent is not

- not a foundation model;
- not production-ready;
- not a replacement for ChaseOS;
- not a canonical truth engine;
- not a live provider/API/fine-tuning system today;
- not all 17 layers implemented.

## Relationship to ChaseOS

ChaseOS remains the parent operating system/control plane and canonical governance owner. Chaser agent can develop product implementation, harness code, docs, and evals, but canonical promotion remains governed by ChaseOS.

## Why Layer 0 comes first

Layer 0 defines expected behavior before architecture layers or evals. It prevents the repo from mistaking JSONL files, smoke tests, or adapter notes for product capability.

## First wedge

```text
safe source input
→ source card
→ claims
→ uncertainty
→ actions
→ memory candidates
→ human review
→ no automatic canonical promotion
```

## Why evals come after behaviour definition

JSONL and pytest are not product proof by themselves. Product-quality evals must test the behavior defined by Layer 0 and V0.

## Why maths and CS foundations matter

Chaser agent needs practical foundations in the correct order: terminal/shell/Git, Python package structure, filesystems and operating systems, sets/functions/vectors/matrices, probability and conditional probability, embeddings and similarity, prompt engineering, harness engineering, JSONL as a data format, evals conceptually, RAG/retrieval, memory consolidation, MCP/tool-use later, runtime governance, and PEFT/LoRA/fine-tuning only after reviewed data exists. These foundations make harness work explainable instead of magical.

## Why human review matters

Human review protects taste, context, safety, memory promotion, roadmap decisions, and public claims. Chaser agent proposes; the operator decides.

## Why fine-tuning comes later

Fine-tuning should only happen after reviewed datasets, failure evidence, evals, and privacy rules exist. Training too early would amplify undefined behavior.

## Public positioning

Publicly, Chaser agent can be described as a scaffolded, governed, source-intelligence and harness-development repo. It must not claim production autonomy, canonical memory, full runtime integration, or fine-tuned intelligence.

## Current status labels

| Label | Meaning |
|---|---|
| Layer 0 defined | Behavior contract exists. |
| V0 planned | First source-intelligence loop is specified. |
| Smoke/schema | Test proves structure or imports only. |
| Contract eval | Test proves Layer 0 behavior. |
| Product-quality eval | Human/evidence-backed evaluation of useful behavior. |
| Later | Deferred until foundations exist. |
| Not active | Explicitly blocked in current phase. |

## Non-goals

No provider calls, no browser authority, no Hermes/OpenClaw activation, no private dataset ingestion, no automatic memory promotion, no fine-tuning, no broad autonomy, and no ChaseOS canonical mutation in the current phase.
