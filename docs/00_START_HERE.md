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
| Local HTTP engineering slice | `05_Runtime_Adapters/Chaser-Agent-Local-HTTP.md` |
| Opt-in offline voice input | `05_Runtime_Adapters/Chaser-Agent-Local-Voice-Input.md` |
| Computer-use HUD engineering state | `01_Product/Chaser-Agent-Computer-Use-HUD.md` |
| Contract eval design | `02_Evals/Chaser-Agent-Contract-Eval-Design.md` |
| Exact current test values | `02_Evals/Chaser-Agent-Current-Test-Matrix.md` |

The standalone-first dependency rule is enforced by `tests/test_standalone_independence.py`, which parses core-package imports and fails on any ChaseOS, provider, MCP, or browser dependency.

Isolated engineering evidence for the new local service: `../logs/build/2026-09-27-standalone-local-http-foundation.md`, `../logs/build/2026-09-27-hud-and-local-voice-bridge.md`, `../logs/build/2026-09-27-warm-voice-worker.md`, `../logs/build/2026-09-27-hud-control-contract.md`, and `../logs/build/2026-09-27-offline-voice-input.md`. These do not replace the older P0.1 acceptance state.

The isolated-worktree [documentation history](DOCUMENTATION_HISTORY.md), [daily engineering index](../logs/daily/README.md), and [agent activity index](../logs/agent-activity/README.md) track this local pass without changing ChaseOS canonical state.

## Truth boundary

P0.1 may persist human review and governance-approved durable local memory. That state is user-owned and deployment-scoped; it is not automatically shared ChaseOS canonical state or global truth.

Profiles specialise analysis but never grant permission. Original run artifacts remain immutable. Providers, FastAPI, tools, MCP, browsers, embeddings, autonomous execution, and training remain inactive.
