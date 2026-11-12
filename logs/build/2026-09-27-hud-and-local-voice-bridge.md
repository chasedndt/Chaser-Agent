# 2026-09-27 — HUD read model and offline speech-out bridge

## Repo-truth delta

The earlier local HTTP slice served deterministic pending reviews only. The separate `2026-09-09-computer-use-hud` worktree has uncommitted HUD state/control research and was inspected but not changed. The operator-approved Pocket Alba library existed locally but was not connected to this Chaser Agent service.

## Implemented in this isolated E: worktree

- Optional `--voice-library` startup setting; the HTTP caller cannot select a model, executable, preset or path. The adapter validates the approved Pocket Alba manifest, pinned offline runtime and local preset.
- `POST /v1/voice/replies` queues one bounded public/toy speech-out job and returns `202` immediately. Authenticated status and WAV routes verify the retained receipt and SHA-256. One active job, no online fallback, and explicit server-close process termination are intended boundaries.
- The first synchronous attempt was **not accepted**: a 150-second client timed out while a cold Pocket Alba take took 174 seconds, leaving a WAV later. The route was replaced with an asynchronous job and direct pinned Python process control; the second real take returned `queued` in 0.49 seconds, then produced a 1.28-second WAV in 93.16 seconds. Its receipt hash matched the WAV and the authenticated audio route returned HTTP 200. This proves offline speech-out, not conversational latency or listening acceptance.
- Ported the immutable HUD reducer/control-acknowledgement concepts into this checkout, added a thread-safe read registry, bearer-protected `GET /v1/hud/current`, and a Tk desktop shell. The normal shell hides while inactive. Synthetic preview shows running, awaiting approval, paused and stopped. Four controls remain disabled because no executor is connected.
- Corrected the preview's four-button clipping at 200% Windows scaling. The inspected final render is `E:\Visual QA\Chaser Agent Visual QA\Current Reviews\2026-09-27-computer-use-hud-preview\hud-synthetic-terminal-v2.png`. An earlier DPI-incorrect crop remains in the review folder as a rejected capture, not acceptance evidence.

## Tests and runtime evidence

- `PYTHONPATH=<worktree>/src python -m pytest tests/test_hud.py tests/test_local_http.py tests/test_local_voice.py -q` — 37 passed after the disconnect display-state test.
- `PYTHONPATH=<worktree>/src python -m pytest -q` — 238 passed, 31 subtests passed, one pre-existing locked canon asset-manifest mismatch (`1491` bytes on disk versus `1489` in its manifest). No asset rewrite was made.
- Live loopback voice job `voice-20260927T131132292827Z-bbcdecf6dffe`: queued, generated pending listening review, authenticated WAV readback 200, receipt and status SHA-256 matched. No actual playback/listening verdict was recorded. The task-created server and preview process were stopped; only test artifacts under E: remain.

## Untouched boundaries and next safe work

No ChaseOS canonical state, original C: checkout, separate HUD worktree, eval verdict, provider key, cloud account, public deployment, or computer-use executor was changed. The goal remains active: the HUD needs a real authorized executor event/control transport and visual QA on live bounded tasks; voice needs a warm local runtime, microphone/STT and interruption semantics before it resembles a Jarvis-style mode. Keep human eval labeling in the original Codex branch task.
