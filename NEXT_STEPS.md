# Chaser agent Next Steps

## Approved direction

Chaser agent is standalone-first, local-first, open-source, domain-neutral, and human-governed. ChaseOS is an optional enhancement through adapters rather than a dependency of the core.

## Active P0.1 acceptance pass

The standalone foundations are implemented and locally verified on the review branch. Before any new authority or model work:

1. inspect a real local review record, reviewed/rejected memory history, and provenance trace;
2. accept or revise the proposed review threshold and durable-state terminology;
3. decide the first official domain pack and profile-discovery direction;
4. add human-reviewed product-quality cases beyond the six contract wiring seeds;
5. decide export/deletion and retention semantics before exposing management commands.

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

After operator acceptance of P0.1, the likely next pass is a provider-neutral fake adapter plus reviewed AI-engineering examples and a first product-quality eval set. Do not start it automatically.
