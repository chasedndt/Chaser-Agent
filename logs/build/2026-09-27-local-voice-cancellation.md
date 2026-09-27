# 2026-09-27 — cancellable local speech take

## Repo-truth delta

The desktop voice panel could cancel a microphone take and suppress playback before it began, but once a Pocket Alba generation job was queued there was no exact-take server cancellation. Closing the HUD could leave the owned warm worker generating. The current E: runtime still fails its broad-ACL startup gate; no live service/audio acceptance was available.

## Changes

- Added bearer-protected `POST /v1/voice/<id>/cancel` with empty JSON body, exact ID validation, existing host/origin and POST-rate boundaries. It reports `cancelling` until the owned job settles. Unknown IDs remain `404`; terminal jobs are not retroactively relabelled.
- Cancellation records `cancelled.json` in the exact take folder before requesting a stop of only the adapter-owned process. The status and audio routes reject a cancelled take even if a late receipt/WAV appears or the adapter restarts. No generated files are deleted.
- The local client asks the service to cancel on operator cancellation, timeout or polling failure after a job was submitted. The HUD offers a separate Cancel reply click and disables Talk while a reply is pending. Already-started blocking Windows playback cannot be interrupted by this slice.
- Added fake-worker tests for active/queued cancellation, durable late-audio suppression, authenticated route, client request, and warm-worker recovery after cancellation. Captured normal, 200%-style and small-screen synthetic button states in the Chaser Agent QA home.

## Verification

- `PYTHONPATH=src python -m pytest -q tests/test_local_voice.py tests/test_local_http.py tests/test_voice_ack.py tests/test_hud.py tests/test_desktop_voice.py` — **72 passed** after final client cleanup. This includes a fake warm-worker cancel/restart and a post-submit polling-failure cancel request.
- Optional E: speech virtual environment, `python -m pytest -q tests/test_local_voice.py tests/test_voice_ack.py tests/test_hud.py tests/test_desktop_voice.py` — **39 passed**.
- [Synthetic HUD cancellation QA](<E:/Visual QA/Chaser Agent Visual QA/Current Reviews/2026-09-27-voice-cancel/QA.md>) — button label, unverified draft, disabled Talk, port and scroll access visually checked; no token/model/audio.
- `PYTHONPATH=src python -m pytest -q` — **308 passed, 1 skipped, 31 subtests passed, 1 failed** in 40.19s. The sole failure is the pre-existing locked canon-core asset-manifest mismatch: approved `brand/chaser-agent/exports/canon-core/v1.0.0-rc.1/README.md` is 1491 bytes; the manifest says 1489. Neither file was edited in this slice.

## Boundaries and remaining work

No operator microphone, actual Pocket Alba stop timing, audible response, model-provider call or computer-use executor was activated. The existing E: runtime remains blocked pending explicit ACL repair and token rotation. Natural barge-in and full request-aware conversation remain future work; this Codex engineering goal stays active.
