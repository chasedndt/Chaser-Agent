# Docs Start Here — Chaser Agent

## Product order

1. `01_Product/Chaser-Agent-Product-Narrative-and-Utility.md`
2. `01_Product/Chaser-Agent-Layer-0-Behaviour-Contract.md`
3. `01_Product/Chaser-Agent-Standalone-vs-ChaseOS-Architecture.md`
4. `01_Product/Chaser-Agent-P0.1-Open-Decisions.md`
5. `01_Product/Chaser-Agent-V0-Definition.md`
6. `01_Product/Chaser-Agent-V0-Blueprint.md`
7. `01_Product/Chaser-Agent-Roadmap.md`
8. `01_Product/Chaser-Agent-17-Layer-Architecture.md`
9. `02_Evals/Chaser-Agent-Case-Study-Workflow-Eval-System.md`

## First operator exercise

To start producing human product-quality labels now, open the [operator floor-walk](../logs/review/2026-08-23-operator-floor-walk.md). It gives the exact file order, five 0–3 ratings per run, three-run starter workload, decision rule, rating cadence and connection to the automated workflow evaluator. No download or paid service is required.

## Implemented P0.1 review order

1. domain-neutral source review and profiles;
2. immutable operator review;
3. local governance;
4. standalone memory lifecycle;
5. knowledge-map provenance;
6. exact test-matrix visibility;
7. optional inactive ChaseOS integration.

All seven surfaces are implemented on `codex/standalone-first-memory-realignment` and covered by the current test suite. They remain pre-alpha review-branch work pending operator acceptance and merge.

### Subsystem architecture documents

| Surface | Document |
|---|---|
| Profiles and domain-neutral review | `03_Summary_Intelligence/Chaser-Agent-Workflow-Profile-Architecture.md` |
| Operator review and score capture | `02_Evals/Chaser-Agent-Operator-Review-Workflow.md` |
| Standalone memory lifecycle | `04_Memory/Chaser-Agent-Standalone-Memory-Architecture.md` |
| Knowledge-map provenance | `04_Memory/Chaser-Agent-Knowledge-Map-Architecture.md` |
| Optional ChaseOS integration | `05_Runtime_Adapters/Chaser-Agent-ChaseOS-Optional-Integration.md` |
| Contract eval design | `02_Evals/Chaser-Agent-Contract-Eval-Design.md` |
| Case-study workflow evals | `02_Evals/Chaser-Agent-Case-Study-Workflow-Eval-System.md` |
| Exact current test values | `02_Evals/Chaser-Agent-Current-Test-Matrix.md` |

The standalone-first dependency rule is enforced by `tests/test_standalone_independence.py`, which parses core-package imports and fails on any ChaseOS, provider, MCP, or browser dependency.

## Truth boundary

P0.1 may persist human review and governance-approved durable local memory. That state is user-owned and deployment-scoped; it is not automatically shared ChaseOS canonical state or global truth.

Profiles specialise analysis but never grant permission. Original run artifacts remain immutable. Providers, FastAPI, tools, MCP, browsers, embeddings, autonomous execution, and training remain inactive.
