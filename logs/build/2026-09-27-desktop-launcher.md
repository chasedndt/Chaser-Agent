# 2026-09-27 — one-process local desktop launcher

## Repo-truth delta

The local API and HUD previously required separate foreground commands. The normal HUD intentionally stayed hidden without a computer-use session, so it did not provide a visible indication that a combined local app was running. The existing E: runtime remained blocked by broad Windows ACLs.

## Changes

- Added `python -m chaser_agent.cli desktop --data-dir <private-E-path> --port 8765`, with the same explicit loopback bind, bearer token, origin, voice-library and ACL boundaries as `serve`.
- The launcher owns one HTTP server thread and one Tk HUD. It verifies its own health response before entering the HUD loop, prints the known port and token **path** (never the token), and shuts down its own service/voice worker when its window closes or Ctrl+C is received. It does not attach an executor or microphone.
- In combined mode, the HUD shows a visible idle state with `127.0.0.1:<port>`, no computer-use session and disabled controls. Separate `hud` mode remains hidden while inactive. Added an idempotent HUD close method and lifecycle/idle-state tests.
- Updated README, as-built map, runtime/HUD guides and goal handoff. No provider choice, tool activation, evaluation label, ChaseOS canonical mutation, ACL repair or token rotation occurred.

## Verification

- `PYTHONPATH=src python -m pytest -q tests/test_local_desktop.py tests/test_hud.py tests/test_local_http.py tests/test_local_acl.py` — **50 passed**. The launcher test binds a real ephemeral loopback port under an injected private-storage premise, observes `/v1/health` and the unauthenticated HUD denial, closes the fake window, and verifies that the owned listener stops. This does not prove the current broad-ACL E: runtime is ready.
- `PYTHONPATH=src python -m chaser_agent.cli desktop --help` — shows required data directory, fixed default port 8765, optional exact origin and explicit local voice library.
- Direct `desktop --data-dir 'E:\Projects\Chaser Agent\Local Runtime\2026-09-27-http-foundation' --port 8765` — exit **2** before GUI/listener because `Runtime path has broad Windows ACL access; no permissions were changed`. No listener on 8765 was observed after the attempt.
- [Synthetic idle HUD visual QA](<E:/Visual QA/Chaser Agent Visual QA/Current Reviews/2026-09-27-desktop-launcher/QA.md>) — 410 × 284 px window-handle capture shows legible port, no-session text and four disabled controls. No real token, API, executor or desktop action was used for the screenshot.
- Full core suite — **277 passed, 1 skipped, 31 subtests passed, 1 failed** in 26.76s. The sole failure is the pre-existing locked canon-core asset-manifest byte mismatch: approved `brand/chaser-agent/exports/canon-core/v1.0.0-rc.1/README.md` is 1491 bytes, manifest says 1489. Neither file was edited here.

## Remaining gates

Live startup and visual acceptance from this operator's E: runtime still require explicit approval to repair the exact ACL and rotate the potentially exposed token. Real authorized computer-use executor events, stop/take-over acceptance, high-DPI/multi-monitor HUD QA, operator microphone acceptance and conversational voice remain open. The active Codex engineering goal is not complete.
