# Chaser Agent computer-use HUD — engineering state

Status, 2026-09-27: an **operator-visible synthetic replay** and a tested executor-gated HTTP control path exist in this isolated worktree. No real computer-use executor is connected. The separate `2026-09-09-computer-use-hud` worktree remains untouched; its immutable state and acknowledgement concepts were carried into this engineering checkout so they can share the local service.

## Intended interaction

When a real, authorized computer-use session begins, a compact always-on-top desktop window should appear with the current phase, a concise redacted action, session identity, recent evidence and control status. It should remain visible after stop/failure/completion until dismissed. Hiding the window must never be treated as stopping execution. Pause, resume, stop and take-over must show **pending** until the executor acknowledges the exact request; a click alone is not proof of control.

The window must not cover the active target, capture pointer input outside its controls, or expose credentials in screenshots. Keyboard access, reduced motion, high contrast, display scaling and multiple monitors require real visual acceptance before the HUD is treated as ready for computer use.

## What works now

- `hud.py` keeps ordered, session-scoped immutable display state. Stale/foreign events and post-terminal updates do not rewrite it.
- `hud_controls.py` models pending commands and matching acknowledgements in memory. It dispatches nothing.
- `hud_runtime.py` offers a thread-safe read model plus `HudBridge`. A separately governed in-process executor can attach one session and obtain a bound event callback. Stale callbacks are invalidated on detach. `GET /v1/hud/current` is bearer-protected and says `inactive`, `controls_enabled: false`, and `display_only_no_executor` by default. `POST /v1/hud/controls` accepts a matching session and an available command only if an executor is attached; otherwise it returns `409`. There is **no HTTP route to attach an executor or inject events**.
- `hud_window.py` is a small always-on-top Windows/Tk desktop shell. Normal mode polls the local read model and stays hidden while inactive. It enables available buttons only for an attached executor, sends authenticated requests, and waits for the matching event before showing the new phase. `chaser-agent hud --preview` shows a clearly marked four-state synthetic replay with all controls disabled. The shipped CLI attaches no executor, so its normal buttons remain disabled.

Start the normal HUD in a separate terminal after starting the local service:

```powershell
$env:PYTHONPATH = (Join-Path (Get-Location) 'src')
python -m chaser_agent.cli hud --data-dir 'E:\Projects\Chaser Agent\Local Runtime\2026-09-27-http-foundation' --port 8765
```

The normal HUD checks the runtime and token-file ACL before reading its credential or opening a window, then holds that token in memory; restart it after an approved token rotation. The existing E: runtime currently fails this check. For layout inspection only: `python -m chaser_agent.cli hud --preview`. The preview opens without a server and cannot affect the desktop outside its own window.

## Verified and unverified

The reducer, acknowledgement contract, registry, executor-gated HTTP control path and negative-authority checks are covered by tests with a fake executor. A 200%-scaled Windows synthetic replay was visually inspected in the local [HUD preview QA record](<E:/Visual QA/Chaser Agent Visual QA/Current Reviews/2026-09-27-computer-use-hud-preview/QA.md>); the title and four disabled controls fit after a layout correction. That proves a rendered prototype only, not the real active-session experience. Enabled-button visual QA, normal-mode appearance, occlusion avoidance, multi-monitor behavior, assistive technology, live control latency, reconnect recovery and actual computer-use integration remain unverified.

## Next gate

Connect an authorized executor event adapter that binds session ID, ordered sequence, redacted action and verified result evidence. The current in-process bridge and HTTP control route are not such an executor. Test stop/take-over during a real bounded task, including disconnect and restart, before saying the HUD works in unison with computer use. Do not promote the fake-executor contract or visual replay as computer-use completion evidence.
