# Engineering goal handoff — standalone local HTTP foundation

Status: operator-requested engineering branch, prepared 2026-09-27. This file is a handoff for a separate Codex branch task. It is **not** an approved public release, a live server, a permission grant, or a substitute for operator eval labels.

Engineering update, 2026-09-27: this Codex branch task is active. Its isolated E: Git worktree now contains a tested local-only HTTP source-review slice; see [runtime contract](../05_Runtime_Adapters/Chaser-Agent-Local-HTTP.md) and [build evidence](../../logs/build/2026-09-27-standalone-local-http-foundation.md). The broader goal also includes HUD and voice, which remain disconnected and are not complete. The Git worktree branch is an implementation isolation detail, **not** the Codex conversation branch requested by the operator.

Earlier follow-on engineering status: local Pocket Alba speech-out was implemented, and a fake-executor-tested HUD control bridge could carry requests and acknowledgements. At that stage, the normal CLI had no computer-use executor, microphone input, speech-to-text or full conversational voice. This remained an active goal, not a completed handoff.

Voice-input follow-on, 2026-09-27: an optional pinned offline STT model and explicit push-to-talk CLI now exist; the public/toy WAV round trip succeeded. The CLI can request a fixed Pocket Alba acknowledgement, but no task-aware reply, live operator microphone acceptance, interruption, or voice-to-action handoff exists. The full objective remains active.

Client-security/status follow-on, 2026-09-27: server, HUD and speech clients now refuse broad token-storage ACLs. The current runtime is still not usable until operator-approved ACL repair and token rotation. Optional voice status answers a few exact read-only questions from health/HUD state; it is not general reasoning, human-auditioned voice or computer-use control. This Codex goal remains active for the full HTTP/HUD/voice outcome, not merely the first service slice.

Desktop-lifecycle follow-on, 2026-09-27: a single `desktop` command now owns the local API and a visible idle HUD on the fixed loopback port; closing the HUD shuts down that owned service. A toy loopback test and synthetic window capture verify wiring/layout only. The real E: runtime remains ACL-blocked, and the complete goal still requires live secure service, authorized computer-use integration and operator-accepted voice.

Desktop-voice follow-on, 2026-09-27: optional explicit push-to-talk was added inside the visible HUD. A cancellable bounded take produces only an unverified draft; read-only status speech requires another click. The installed E: STT model loaded without recording, and synthetic ready/recording UI captures passed review. The current runtime remains ACL-blocked and no live operator microphone, audible answer, reasoning provider or executor is accepted. The full Codex goal remains active.

Voice-state follow-on, 2026-09-27: per-take IDs now prevent an old queued draft or cancel event from appearing over a newer active recording, and cancellation before final emission discards the draft. Deterministic race tests passed; live microphone and operator voice acceptance remain open. The full goal remains active.

HTTP-security follow-on, 2026-09-27: a read-only `doctor` command now reports ACL and port preflight without reading token contents or changing state. It confirmed three broad-ACL blockers in the actual E: runtime and a momentarily available `127.0.0.1:8765`. No service startup occurred; the full goal remains active.

Speech-interruption follow-on, 2026-09-27: an exact authenticated voice-cancel route, persistent cancelled marker and HUD Cancel reply control now exist. Fake warm-worker tests prove a later take can recover, and synthetic layouts show the control at normal/high scale. Actual Pocket Alba stop latency and already-started playback interruption remain unverified on a real device; no general conversational provider or computer-use executor is attached. The full goal remains active.

HUD-playback follow-on, 2026-09-27: the desktop's cancel-event path now uses output-only PCM16 or IEEE-float32 chunks and aborts pending buffers; the fixed CLI acknowledgement keeps legacy blocking playback. The installed optional audio environment accepted 24 kHz mono/int16 and float32 settings without opening a speaker. Actual audible quality, device stop latency, provider-backed conversation and real executor/HUD integration remain unverified; the full goal stays active.

HUD-reconnect follow-on, 2026-09-27: after a nonterminal disconnect, only the same in-process executor may reattach the same session. Its old callback stays invalid, pending controls remain uncertain, and a fresh higher-sequence event is required to re-enable controls. Fake-executor tests cover this same-process path, not process-crash recovery or real computer use. The full goal stays active.

HTTP-integrity follow-on, 2026-09-27: new source-card runs carry read-time SHA-256 records; changed or missing new-run records fail with `409`, while older runs are labelled unverified. This corrects an overstrong "immutable" API claim: no filesystem seal or same-user adversary resistance exists. Live service, computer-use executor and conversational voice remain open; the full goal stays active.

HTTP-rejection follow-on, 2026-09-27: early rejected POSTs now drain only small declared bodies before closing, avoiding an observed Windows connection abort on a 404 path. Focused network tests cover invalid route, Host, Origin and rate-limit replies. Larger or malformed bodies still close without unbounded reads.

Voice-turn follow-on, 2026-09-27: during a pending spoken reply the HUD now offers Talk next. That explicit click requests cancellation, waits for the reply worker to complete, then starts a new bounded push-to-talk take; Clear draft revokes the queued capture. Mocked UI-state tests prove ordering and no early microphone opening, but no real microphone/speaker latency or general conversation is verified. The full goal stays active.

HUD-visual follow-on, 2026-09-27: actual Tk screenshots with fake/no-device state exposed clipping at a narrow width. The HUD now wraps status text to the canvas and reflows controls into two rows; a second capture verifies readable labels at that tested size. Talk-next waiting copy now distinguishes queued capture from reply stopping. See the [QA record](<E:/Visual QA/Chaser Agent Visual QA/Current Reviews/2026-09-27-talk-next-hud/QA.md>). Keyboard, screen-reader and real-device behavior remain unverified.

HUD-control-race follow-on, 2026-09-27: outbound button requests carry the displayed session and view revision. A delayed HTTP response cannot overwrite a newer executor snapshot, connection-loss warning or another session's notice. Mocked UI tests cover the stale-response case; a real authorized computer-use executor is still absent.

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

Report source commit/worktree, changed interfaces, threat model, exact commands/results, live loopback request/response, security failures tested, untouched boundaries, and remaining unknowns. Keep behavior/docs/build log/history aligned. This goal remains active until a secure local service is demonstrably usable, the HUD works with a real authorized computer-use executor, and voice can accept and answer real operator speech safely. Do not mark it complete for a protocol test, synthetic HUD replay, toy WAV, or design document alone.
## Latest operator approval and evidence — 27 September 2026

The operator has explicitly pre-approved Chaser Agent layer engineering, runtime ACL/token maintenance and architecture/product-page updates. The old ACL approval blocker no longer applies. Repair and token rotation are complete and the live local API passed its probe; see [evidence](../../logs/build/2026-09-27-runtime-activation.md). Deployment credentials are not configured in this session, so website changes remain prepared source. Human eval judgments and canonical ChaseOS activation remain separate. Real executor/HUD and conversational voice completion gates are still open. The app Goal record still reports blocked; work resumed under the user's instruction without claiming completion or creating a duplicate Goal.
