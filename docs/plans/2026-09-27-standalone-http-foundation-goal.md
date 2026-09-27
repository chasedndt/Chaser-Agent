# Engineering goal handoff — standalone local HTTP foundation

Status: operator-requested engineering branch, prepared 2026-09-27. This file is a handoff for a separate Codex branch task. It is **not** an approved public release, a live server, a permission grant, or a substitute for operator eval labels.

Engineering update, 2026-09-27: this Codex branch task is active. Its isolated E: Git worktree now contains a tested local-only HTTP source-review slice; see [runtime contract](../05_Runtime_Adapters/Chaser-Agent-Local-HTTP.md) and [build evidence](../../logs/build/2026-09-27-standalone-local-http-foundation.md). The broader goal also includes HUD and voice, which remain disconnected and are not complete. The Git worktree branch is an implementation isolation detail, **not** the Codex conversation branch requested by the operator.

## Goal to create in the engineering task

Build and verify Chaser Agent's standalone, local-only HTTP foundation so the deterministic harness can be invoked through a bounded loopback service without ChaseOS. Start with a read-only/review-only source-card path and explicit health/status; then add only the review and run retrieval operations whose authority boundaries can be tested. Keep the service secure by default, documented, and independently runnable. Do not generate human product-quality labels or treat pending eval fixtures as golden answers.

## Current baseline

- The source-card, review, local governance, memory, knowledge and contract-eval Python surfaces exist; current as-built truth is in docs/01_Product/Chaser-Agent-As-Built-Map.md.
- No public FastAPI/web server is part of the verified P0.1 core. Runtime adapters are bounded/inactive; the HUD is a separate foundation, not computer-use authority.
- The operator is reviewing run-4 versus preserved run-1 in Agent Review Studio in the original task. Those judgments belong there, not in this branch.

## First implementation slice

1. Reconcile current repo truth, worktree status, tests and dependency policy before selecting an HTTP framework. Use an E: worktree and preserve all unrelated changes.
2. Write a local threat model and interface contract: bind only to 127.0.0.1 by default; define allowed origins/CSRF or equivalent local-client protection, request-size and path boundaries, rate limits, error shapes, logging redaction, and startup/shutdown lifecycle. Explain which controls are implemented versus deferred.
3. Implement the smallest usable loopback service around existing deterministic logic. Prefer stable request/response schemas and no provider, browser, MCP, tool execution, ChaseOS mutation or automatic memory promotion.
4. Add unit, integration and abuse tests for safe inputs, malformed inputs, oversized bodies, unauthorized origins, path traversal, duplicate requests, and negative-authority behavior. Verify a real local port round trip.
5. Document a one-command local launch and exact evidence. Do not claim production security, LAN/public reachability, or computer use from a loopback test.

## Ownership split

Engineering task may choose algorithms, data structures, framework, schemas, threat controls and tests. It may not decide whether a claim is useful, whether an action is good business judgment, or whether run-4 passes product quality. The operator makes those eval decisions in the original task. Engineering may encode an operator-approved verdict into a regression only after that verdict is supplied.

## Explicit boundaries

No push, merge, deployment, domain/DNS change, model training, credential extraction, real-world action, provider activation, durable memory promotion, or public claim without separate authority. If a framework or dependency choice materially changes risk or operating requirements, explain the tradeoff before adopting it. Preserve the canonical ChaseOS vault and the dirty original checkout.

## Completion evidence

Report source commit/worktree, changed interfaces, threat model, exact commands/results, live loopback request/response, security failures tested, untouched boundaries, and remaining unknowns. Keep behavior/docs/build log/history aligned. This goal remains active until the first local service is demonstrably usable and its security boundaries are tested; do not mark it complete for a design document alone.
