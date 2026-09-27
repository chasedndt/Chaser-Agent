# 2026-09-27 — Warm offline Pocket Alba worker

## Repo-truth delta

The prior optional voice route launched the approved Pocket Alba model once per take. A real 1.28-second WAV took 93.16 seconds to generate, so it was not a usable responsive voice path. The HTTP route itself already queued jobs asynchronously and retained hash-verified receipts.

## Changes

- Added `pocket_worker.py`, a private stdin/stdout JSON-line process with no socket. It loads the pinned local model and Alba preset once, reads only allowlisted job IDs and scripts under the selected local runtime folder, and retains compatible WAV/receipt artifacts.
- Added `WarmPocketAlbaVoice` and made the configured HTTP service prewarm it in the background. Health now reports `voice_runtime: starting|ready|busy|failed|cold`; POST stays bounded and receives `409` while the runtime is starting or occupied.
- Restored the exact production cache roots from the approved speech-library manifest. A first exploratory worker run with a new empty cache timed out and produced no WAV; this was not accepted as success.
- Added exact owned-process-tree shutdown on Windows because this Python venv launcher spawns a child interpreter. No broad process kill is used.

## Direct local verification

- `PYTHONPATH=<worktree>/src python -m pytest tests/test_pocket_worker.py tests/test_local_voice.py tests/test_local_http.py tests/test_hud.py -q` — 43 passed. `PYTHONPATH=<worktree>/src python -m pytest -q` — 244 passed, 31 subtests passed, one unchanged locked canon asset-manifest size mismatch (1491 bytes on disk versus 1489 recorded). No approved visual asset was rewritten.
- A warm-process first take generated 1.68 seconds of audio in 4.02 seconds **after** model startup; its WAV hash matched the receipt.
- A second take in that same worker returned a generated state in 4.52 seconds end-to-end; the receipt recorded 3.45 seconds for 1.84 seconds of audio. Authenticated WAV GET returned 200 and matched the receipt hash.
- A fresh service prewarmed in the background: health moved from `starting` to `ready`. The first request after ready completed in 10.76 seconds; receipt generation was 8.33 seconds for 1.52 seconds of audio, with a matching hash.
- Stopping the task-created server left zero matching worker processes and zero port-8765 listeners.
- The local [voice QA record](<E:/Visual QA/Chaser Agent Visual QA/Current Reviews/2026-09-27-warm-voice/QA.md>) lists the retained takes and missing human listening gate.

## Authority and remaining work

No provider API, model download, microphone capture, computer use, ChaseOS mutation, human eval verdict, publication, or push occurred. This is an offline speech-out worker, not a full voice assistant. Microphone/STT consent, interruption, warm-load telemetry, latency distribution, audio playback UX and human listening acceptance remain open.
