# 2026-09-27 — explicit Talk-next voice turn

## Repo-truth delta

The HUD previously disabled Talk while a local status reply was pending. An operator had to cancel the reply, wait, then click Talk again. The local reply path now has output-only cancellation, but no real device timing has been accepted and the voice feature still answers only exact read-only status questions.

## Changes

- During a pending reply, the HUD labels the Talk button **Talk next**. An explicit click requests cancellation and queues one next capture; it does not open the microphone while the reply worker is still active.
- The queued capture begins only when the speech worker posts completion. Clear draft revokes the queued capture. The existing DesktopVoiceController still paints its recording indicator before opening the input device.
- Added fake-controller tests proving that Talk next first sets cancellation, does not capture early, captures after completion, and can be revoked. The prior Cancel reply path remains available.

## Verification

- `PYTHONPATH=src python -m pytest -q tests/test_hud.py tests/test_voice_ack.py tests/test_local_audio.py tests/test_local_voice.py tests/test_desktop_voice.py` — **50 passed**.
- The same five files in the optional E: speech virtual environment — **50 passed**.
- `PYTHONPATH=src python -m pytest -q` — **325 passed, 1 skipped, 31 subtests passed, 1 failed** in 46.02s. The only failure remains the locked canon-core manifest mismatch: approved `brand/chaser-agent/exports/canon-core/v1.0.0-rc.1/README.md` is 1491 bytes, while its manifest says 1489. Neither file was edited.
- `git diff --check` — passed; Git emitted only LF-to-CRLF warnings.

## Boundaries and remaining work

No real microphone or speaker opened, and no fresh rendered visual QA was produced for the Talk-next label. Device stop latency, acoustic feedback, responsiveness at minimum HUD width and operator comprehension remain unverified. This does not add wake-word listening, a general reasoning provider, voice-to-tool execution or a real computer-use executor. The E: runtime still needs explicit operator approval for ACL repair and token rotation before live acceptance. The full goal stays active.
