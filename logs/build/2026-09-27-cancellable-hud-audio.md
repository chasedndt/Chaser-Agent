# 2026-09-27 — output-only cancellable HUD playback

## Repo-truth delta

The HUD could request cancellation of a queued/generating local Pocket Alba take, but once `winsound.PlaySound` started its blocking in-memory playback, its cancel event could not interrupt audible output. The existing E: service runtime remains ACL-blocked, so real speaker acceptance is not available yet.

## Changes

- Added a separate local audio module. Only HUD replies with a cancel event use `sounddevice.RawOutputStream`; the fixed CLI acknowledgement keeps its previous Windows playback. The optional environment already pins `sounddevice==0.5.6` for offline STT.
- Parse the returned WAV as bounded uncompressed 16-bit PCM or 32-bit IEEE float, one or two channels, 8–48 kHz, at most 60 seconds and 10 MB. The float format matters because the worker writes its generated float array through SciPy. Reject non-finite or out-of-range float samples before opening output. Output-only writes use roughly 50 ms chunks and check the cancel event between writes. Cancellation calls the stream's abort operation to drop pending buffers, then closes it. Missing optional output support and invalid WAVs fail closed without a silent noninterruptible fallback.
- Add fake-device tests for chunk bounds, normal completion, cancellation after a write, no output opening after pre-cancel, unsupported WAV, missing dependency and client cancellation during output.

## Verification

- `PYTHONPATH=src python -m pytest -q tests/test_local_audio.py tests/test_voice_ack.py tests/test_local_voice.py tests/test_hud.py` — **40 passed** after the float32 correction.
- Optional E: speech virtual environment, same four files — **40 passed**.
- Installed `sounddevice` reports version **0.5.6** and exposes `RawOutputStream`. `check_output_settings(samplerate=24000, channels=1, dtype='int16')` and the corresponding `dtype='float32'` query returned successfully on the default output. Neither query played sound or opened the microphone.
- Official API basis: [python-sounddevice raw stream documentation](https://python-sounddevice.readthedocs.io/en/0.5.2/api/raw-streams.html), [stream abort semantics](https://python-sounddevice.readthedocs.io/en/0.5.0/api/streams.html), and [SciPy WAV writer dtype semantics](https://docs.scipy.org/doc/scipy/reference/generated/scipy.io.wavfile.write.html). The installed version and tests, not these documentation pages alone, are the local implementation evidence.
- `PYTHONPATH=src python -m pytest -q` — **315 passed, 1 skipped, 31 subtests passed, 1 failed** in 72.35s. The sole failure is the pre-existing locked canon-core asset-manifest mismatch: approved `brand/chaser-agent/exports/canon-core/v1.0.0-rc.1/README.md` is 1491 bytes; the manifest says 1489. Neither file was edited in this slice.

## Boundaries and remaining work

No audible reply or device-level cancellation latency was measured; PortAudio writes and shutdown can still block beyond one nominal chunk. The current runtime still needs explicit operator-approved ACL repair/token rotation before real HTTP/HUD/voice QA. General request-aware conversation and a real authorized computer-use executor remain absent. The Codex engineering goal stays active.
