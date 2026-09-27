# Live desktop and offline voice probe — 27 September 2026

## Repo-truth delta

The combined desktop service was launched with the existing approved Pocket Alba library and pinned offline STT model on the private runtime. The task-owned API-only process 18440 was revalidated by command line and replaced by the combined desktop: wrapper 29052, actual process 15764, exec session 50804. The native window reported `Chaser Agent HUD`, responding true. Microphone access still requires Talk; no capture or playback occurred in this verification.

At the 23:56 BST recheck, HTTP refused connection, the exact desktop and worker processes were absent, and the exec session no longer existed. There were zero port-8765 listeners. The reason for exit is unknown; do not infer a crash or operator close. The completed probes below remain historical evidence, not a claim of a currently running service. No automatic restart was performed.

Added `scripts/probe_local_voice.py`: explicit `--confirm-toy-jobs`, fixed public/toy text, authenticated loopback only, no proxy, no cloud model, no microphone, no speaker. Default mode requests cancellation immediately after queueing, verifies cancelled audio is inaccessible, then checks a recovery take. `--mode warm-only` measures a subsequent take without cancelling. This does not prove cancellation at every model phase or audible interruption.

## Actual measurements

| Check | Result |
|---|---|
| Cancel requested after queueing | Terminal cancelled after 4.625 seconds |
| Cancelled audio GET | 404 |
| Recovery including cold reload | 218.875 seconds |
| Subsequent warm reply | 8.469 seconds |
| Generated audio | 3.52 seconds, 337978 bytes |
| Authenticated audio | 200, SHA-256 matches receipt |
| Unauthenticated audio | 401 |
| Human listening / microphone acceptance | Not performed |

Both completed takes used the same fixed text and seed, returning SHA-256 `19fd58c303d0bf5910563eaa32a8c6bf7fd43ec4272a39bc55f8285788505fad`. Their matching hashes are expected for this deterministic smoke, not a speech-quality evaluation. The cancelled take and two generated takes remain in the private runtime. No private recordings were created or published.

Actual local IDs: cancelled `voice-20260927T224142974988Z-b5522ad6a7c4`; recovery `voice-20260927T224147978968Z-6f3a4f58c9e7`; warm `voice-20260927T224654756333Z-6d64a9bfb81d`.

## Reproduce

With the existing voice-enabled service idle, from the repository root:

```powershell
$env:PYTHONPATH = (Join-Path (Get-Location) 'src')
python scripts/probe_local_voice.py --data-dir '<private runtime>' --confirm-toy-jobs
python scripts/probe_local_voice.py --data-dir '<private runtime>' --confirm-toy-jobs --mode warm-only
python -m pytest -q tests/test_local_voice.py tests/test_local_http.py tests/test_hud.py tests/test_local_desktop.py tests/test_desktop_voice.py
```

Both live probe modes exited 0. Focused tests: **85 passed in 41.09s**. This is not a new full-suite result; the prior locked brand manifest mismatch remains unresolved.

## Implications and next action

Cancellation currently stops the owned model process. Recovery therefore incurs a cold model reload; 219 seconds is not acceptable conversational latency. The installed Pocket implementation's streaming generator also owns decoder/generation threads, so simply abandoning its generator would not prove safe cancellation or safe model reuse. A future cooperative protocol must acknowledge all worker threads stopped before reuse, or retain hard-stop fallback. Keep measurements separate from promises.

General conversation still needs the operator's pending provider/backend selection and data policy. No credential was created, copied or printed; no reasoning provider or real executor was attached. Human evaluation remains separate. The full goal is active and incomplete. Website publication was completed in the preceding [release](2026-09-27-companion-release.md); no additional website change was necessary for this private runtime probe.
