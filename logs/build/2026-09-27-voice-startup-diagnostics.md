# Offline voice startup diagnostics

The preceding real probe measured a 218.875-second reload after cancellation. Added authenticated `GET /v1/voice/runtime` to distinguish current state from bounded startup milestones: worker starting, libraries loaded, model loaded and ready. Values are elapsed seconds from the latest launch, not timestamps, transcripts, paths, credentials or raw worker logs. A fresh launch clears prior milestones; a reused worker retains its original startup measurements. A stopped/failed worker's state must be read alongside its historical milestones.

The opt-in live probe now prints these diagnostics before and after its jobs. This is instrumentation for the next cold-start investigation, **not a latency fix**. No new live voice run, microphone capture, playback or provider call was performed in this slice. The desktop remains stopped from the prior final check.

Tests cover copied/content-free bounded milestone data and authenticated configured/disabled HTTP responses. Exact focused command: `python -m pytest -q tests/test_local_voice.py tests/test_local_http.py` — **50 passed in 28.46s**, completed across the 27/28 September midnight boundary. Full-suite brand-manifest failure remains outside this slice; no full acceptance claim.

Next: measure imports versus weight/preset load using the live probe, then change only the demonstrated bottleneck. Keep hard-stop cancellation until safe worker-thread shutdown and reuse are verified. The general conversation backend decision and human acceptance are still pending.
