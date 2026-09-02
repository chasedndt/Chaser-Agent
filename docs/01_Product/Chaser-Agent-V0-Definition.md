# Chaser Agent V0 and P0.1 Definition

## V0 foundation

V0 is the deterministic local source-to-review loop. It turns a declared safe source into a structured artifact containing source metadata, evidence-linked claims, separate Chaser Agent inference, uncertainty, action candidates, memory candidates, a review scaffold, and a run log.

## P0.1 standalone completion target

P0.1 makes the V0 review opportunity operational without adding providers or tools:

```text
domain-neutral source review
-> explicit workflow profile
-> immutable human review record
-> local governance decision
-> approved durable local memory
-> lexical/tag retrieval
-> provenance-first knowledge map
-> optional inactive ChaseOS handoff
```

## Operator

In standalone mode the human operator is the approval authority. In ChaseOS-integrated mode the human remains the authority through ChaseOS governance. Automation never replaces the approval decision.

## Problem solved

P0.1 prevents goals, source facts, inference, actions, memory, review, and durable state from collapsing into one output. It also prevents the open-source core from requiring ChaseOS while preserving ChaseOS as the strongest optional integrated deployment.

## Minimum P0.1 proof

1. Core modules import and run without ChaseOS installed.
2. The general profile is default and contains no design/media/trading boilerplate.
3. AI-engineering and website profiles remain isolated.
4. Headings are not treated as factual claims.
5. Review scores, decisions, corrections, and accepted/rejected candidate IDs persist immutably.
6. Original run artifacts remain unchanged.
7. Review alone does not promote memory.
8. Local governance enforces valid lifecycle transitions.
9. SQLite memory persists outside the repository and survives restart.
10. Retrieval respects status, scope, privacy, tags, lexical terms, and recency.
11. Knowledge-map provenance traces memory back to source, evidence, run, and review.
12. ChaseOS integration remains optional, inactive, and outside the core dependency graph.
13. Current eval rows and assertions are exported with honest maturity labels.

## Not included

- FastAPI or web UI;
- live providers or local-model inference;
- semantic RAG, embeddings, or vector databases;
- MCP/tool/browser execution;
- autonomous planning/execution;
- public actions, payments, trading, deployment, or credential operations;
- model training, fine-tuning, LoRA, or PEFT;
- automatic skill optimisation;
- ChaseOS Gate consumption or canonical mutation.

## Manual decisions retained

The final review threshold, data-class definitions, first official domain pack, durable-memory public terminology, profile discovery, later provider/RAG/tool/sandbox choices, standalone/ChaseOS sync/conflict policy, export/deletion, and retention remain operator decisions.
