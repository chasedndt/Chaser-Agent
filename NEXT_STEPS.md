# Chaser agent Next Steps

## Approved direction

Chaser agent is standalone-first, local-first, open-source, domain-neutral, and human-governed. ChaseOS is an optional enhancement through adapters rather than a dependency of the core.

## Active P0.1 pass

Build and prove, in order:

1. protocol boundaries for governance, reviews, memory, knowledge, and profiles;
2. domain-neutral deterministic source review;
3. `general_source_review`, `ai_engineering_research_review`, and `website_design_review` profile isolation;
4. immutable human-review persistence;
5. standalone local governance with no external side effects;
6. SQLite memory lifecycle outside the repository;
7. lexical/tag retrieval without embeddings;
8. provenance-first SQLite knowledge map;
9. optional inactive ChaseOS packet adapter;
10. exact current test-matrix export.

## Operator gates

- Review example operator records before accepting promotion semantics.
- Review durable-state terminology and lifecycle policy.
- Keep the proposed 12/15 review threshold configurable and unapproved.
- Do not invent final data-class definitions, profile discovery, sync/conflict, export/deletion, or retention policy.

See `docs/01_Product/Chaser-Agent-P0.1-Open-Decisions.md`.

## Not now

- FastAPI or web UI;
- live providers or local-model inference;
- semantic RAG, embeddings, or vector databases;
- MCP/tool/browser execution;
- autonomous planner/executor loops;
- public posting, payments, trading, deployment, or credentials;
- model training, fine-tuning, LoRA, or PEFT;
- automatic skill optimisation;
- ChaseOS canonical mutation;
- merge to `main`.

## Later bounded pass

After operator review of P0.1, the likely next pass is a provider-neutral fake adapter plus reviewed AI-engineering examples and a first product-quality eval set. Do not start it automatically.
