# 2026-09-27 — desktop voice take-order protection

## Repo-truth delta

The opt-in desktop push-to-talk panel could begin a second take after the first worker cleared its busy flag but before the first worker's final event reached Tk. A late draft or cancellation from the first take could then replace the visible state of the second active recording. Cancellation during transcription also needed a final check before a result was delivered. No real microphone acceptance has occurred, and the existing E: runtime remains ACL-blocked.

## Changes

- Assign a monotonic in-process ID to each explicit take and tag its recording, transcribing, cancellation and final events. The HUD accepts final events only from its active take; an older queued event cannot enable Speak status or overwrite the active microphone indicator.
- Check the cancellation event while holding the final state lock, immediately before clearing busy and emitting the result. A cancellation that wins that boundary discards the transcript.
- Add deterministic tests for cancellation during transcription, delayed delivery from a previous take, and stale HUD draft/cancellation filtering.

## Verification

- `PYTHONPATH=src python -m pytest -q tests/test_desktop_voice.py tests/test_hud.py` — **23 passed**.
- Optional E: speech virtual environment, same two test files — **23 passed**.
- `PYTHONPATH=src python -m pytest -q` — **294 passed, 1 skipped, 31 subtests passed, 1 failed** in 39.43s. The sole failure is the pre-existing locked canon-core asset-manifest mismatch: approved `brand/chaser-agent/exports/canon-core/v1.0.0-rc.1/README.md` is 1491 bytes; the manifest says 1489. Neither file was edited in this slice.

## Boundaries and remaining work

No user microphone, audible response, reasoning provider or computer-use executor was activated. These tests prove state ordering, not driver-level capture cancellation or complete Jarvis-style conversation. The runtime ACL/token decision and provider/tool decisions remain open. The Codex engineering goal stays active.
