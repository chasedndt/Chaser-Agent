# Real offline startup measurement — 28 September 2026

## Result

Ran the existing `WarmPocketAlbaVoice` against the approved speech library and private runtime, without launching HTTP or the HUD. Preflight checked the private token boundary without printing its value. No utterance, microphone capture, playback, provider call or model download was requested. The task waited on the same live worker until terminal readiness, then closed its exact owned process through `adapter.close()` in `finally`.

| Milestone | Seconds since launch | Approximate interval |
|---|---:|---:|
| Worker started | 0.922 | 0.922 |
| Libraries loaded | 36.625 | 35.703 |
| Model loaded | 57.516 | 20.891 |
| Voice preset ready | 57.594 | 0.078 |

Final state was `ready`, followed by `closed`; command exited 0. No new audio artifacts were produced. This verifies the newly added diagnostics against a real worker, not only mocked events.

## Interpretation

The earlier complete cancellation/recovery took 218.875 seconds, including output generation; the subsequent warm response took 8.469 seconds. This fresh startup took 57.594 seconds. These measurements have different scopes and machine/cache conditions, and are too few for percentiles or a causal performance claim. No loading code was optimized between them. It would be incorrect to advertise a speedup or blame the entire earlier delay on weight loading.

Imports dominate this particular startup; preset loading does not. Library/filesystem cache effects, resource contention and model initialization remain possible explanations, not verified causes. HUD/HTTP were absent from this measurement. Before changing worker reuse or model loading, collect matched phase measurements and preserve safe cancellation. The general conversational provider choice and operator microphone/listening acceptance remain outstanding; the engineering goal is not complete.
