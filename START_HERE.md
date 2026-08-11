# Start Here — Chaser agent

Chaser agent is standalone-first and ChaseOS-enhanced. Read the product definition and authority boundary before implementation details.

## Reading order

1. `docs/01_Product/Chaser-Agent-Product-Narrative-and-Utility.md`
2. `docs/01_Product/Chaser-Agent-Layer-0-Behaviour-Contract.md`
3. `docs/01_Product/Chaser-Agent-Standalone-vs-ChaseOS-Architecture.md`
4. `docs/01_Product/Chaser-Agent-P0.1-Open-Decisions.md`
5. `docs/01_Product/Chaser-Agent-V0-Definition.md`
6. `docs/01_Product/Chaser-Agent-V0-Blueprint.md`
7. `docs/01_Product/Chaser-Agent-From-First-Principles.md`
8. `docs/01_Product/Chaser-Agent-Product-Thesis.md`
9. `docs/01_Product/Chaser-Agent-Roadmap.md`
10. `docs/01_Product/Chaser-Agent-17-Layer-Architecture.md`
11. `docs/03_Summary_Intelligence/Chaser-Agent-V0-Source-Card-Schema.md`
12. `docs/02_Evals/Chaser-Agent-V0-Human-Review-Packet.md`
13. `docs/08_Learning/AI-Engineering-Learning-Map.md`

## Current truth

- The deterministic Source Card Harness exists.
- The six-family Layer 0 contract seed exists locally and remains pending operator review.
- The current default builder is not yet domain-neutral until the P0.1 profile migration is verified.
- Standalone review persistence, governed local memory, and a provenance map are approved P0.1 work, not capabilities to infer without code/tests.
- ChaseOS integration is optional and inactive by default.
- Providers, tools, MCP, browsers, FastAPI, embeddings, autonomous loops, and training remain outside P0.1.

## Baseline verification

```bash
.venv/bin/python -m pytest -q
.venv/bin/python -m scripts.validate_jsonl evals/datasets/golden/*.jsonl evals/datasets/contract/*.jsonl
```

## Current implementation branch

P0.1 redesign work is reviewed on:

```text
codex/standalone-first-memory-realignment
```

Do not infer that review-branch work is merged or released.
