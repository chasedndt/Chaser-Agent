# Chaser Agent computer-use HUD — engineering state

Status, 2026-09-27: an **operator-visible synthetic replay** and a read-only local HTTP state surface exist in this isolated worktree. No computer-use executor is connected. The separate `2026-09-09-computer-use-hud` worktree remains untouched; its immutable state and acknowledgement concepts were carried into this engineering checkout so they can share the local service.

## Intended interaction

When a real, authorized computer-use session begins, a compact always-on-top desktop window should appear with the current phase, a concise redacted action, session identity, recent evidence and control status. It should remain visible after stop/failure/completion until dismissed. Hiding the window must never be treated as stopping execution. Pause, resume, stop and take-over must show **pending** until the executor acknowledges the exact request; a click alone is not proof of control.

The window must not cover the active target, capture pointer input outside its controls, or expose credentials in screenshots. Keyboard access, reduced motion, high contrast, display scaling and multiple monitors require real visual acceptance before the HUD is treated as ready for computer use.

## What works now

- `hud.py` keeps ordered, session-scoped immutable display state. Stale/foreign events and post-terminal updates do not rewrite it.
- `hud_controls.py` models pending commands and matching acknowledgements in memory. It dispatches nothing.
- `hud_runtime.py` offers a thread-safe read model. `GET /v1/hud/current` is bearer-protected and says `inactive`, `controls_enabled: false`, and `display_only_no_executor` until a trusted in-process adapter supplies a session. There is **no HTTP route to inject events or send controls**.
- `hud_window.py` is a small always-on-top Windows/Tk desktop shell. Normal mode polls the local read model and stays hidden while inactive. `chaser-agent hud --preview` shows a clearly marked four-state synthetic replay. Its buttons are deliberately disabled; it does not operate a computer.

Start the normal HUD in a separate terminal after starting the local service:

```powershell
$env:PYTHONPATH = (Join-Path (Get-Location) 'src')
python -m chaser_agent.cli hud --data-dir 'E:\Projects\Chaser Agent\Local Runtime\http-foundation' --port 8765
```

For layout inspection only: `python -m chaser_agent.cli hud --preview`. The preview opens without a server and cannot affect the desktop outside its own window.

## Verified and unverified

The reducer, acknowledgement contract, registry and API state are covered by tests. A 200%-scaled Windows synthetic replay was visually inspected in the local [HUD preview QA record](<E:/Visual QA/Chaser Agent Visual QA/Current Reviews/2026-09-27-computer-use-hud-preview/QA.md>); the title and four disabled controls fit after a layout correction. That proves a rendered prototype only, not the real active-session experience. Normal-mode appearance, occlusion avoidance, multi-monitor behavior, assistive technology, live control latency, reconnect recovery and actual computer-use integration remain unverified.

## Next gate

Build an authenticated executor event adapter that binds session ID, ordered sequence, redacted action and verified result evidence. Only then enable control dispatch and acknowledgement in the window. Test stop/take-over during a real bounded task, including disconnect and restart, before saying the HUD works in unison with computer use. Do not promote this visual replay as computer-use completion evidence.
