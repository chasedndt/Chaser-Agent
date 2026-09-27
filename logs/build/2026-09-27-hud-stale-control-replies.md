# 2026-09-27 — stale HUD control-reply guard

## Repo-truth delta

The desktop HUD could send a control request for one computer-use session, render a newer executor snapshot or connection-loss state, then let the older HTTP response overwrite its notice with "acknowledged" or "awaiting". That would make the operator see a stale transport claim over fresher execution evidence. The shipped service still has no real executor attached.

## Changes

- Each button request records the currently displayed session and view revision. The HUD shows "Sending control request · waiting for executor evidence" immediately.
- The response clears the local in-flight flag, but changes the notice only if the same session and exact display revision are still visible. Every rendered snapshot and connection-loss event advances the revision.
- A fake-widget test covers different-session and newer-same-session responses, plus a still-current response. No server contract or authority boundary was widened.

## Verification

- `PYTHONPATH=src python -m pytest -q tests/test_hud.py tests/test_local_http.py tests/test_local_desktop.py` — **67 passed**.
- `PYTHONPATH=src python -m pytest -q` — **327 passed, 1 skipped, 31 subtests passed, 1 failed** in 44.59s. The only failure remains the locked canon-core manifest mismatch: approved `brand/chaser-agent/exports/canon-core/v1.0.0-rc.1/README.md` is 1491 bytes, while its manifest says 1489. Neither file was edited.

## Boundaries and remaining work

This is UI ordering proof with fake state, not real computer-use pause/stop/take-over acceptance. No live HTTP service, real executor, voice device, provider, ACL/token change, ChaseOS canonical write, push or deployment occurred. The E: runtime still fails the private-ACL preflight. The full HTTP/HUD/voice goal remains active.
