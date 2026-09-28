# 2026-09-27 — opt-in offline voice input

## Repo-truth delta

Before this pass, Chaser Agent's optional local voice worker could only generate speech. No speech-to-text runtime, microphone contract or voice-input CLI existed in this isolated worktree.

## Changes

- Added optional `voice-input` dependencies and an E:-isolated runtime. The explicit setup script anonymously downloads pinned MIT-licensed Systran faster-whisper-tiny.en revision `0d3d19a32d3338f10357c0889762bd8d64bbdeba` outside the repository and records SHA-256 hashes for the four model files.
- Added `voice-mode`: an operator presses Enter before each 0.5–12-second in-memory microphone capture; `q` quits and Ctrl+C discards a take. A 16 kHz PCM test WAV path bypasses the microphone. Local transcription returns an `unverified` draft with `transcript_only_no_dispatch`; it never authorizes tools, computer use or memory.
- Added optional fixed Pocket Alba acknowledgement via the existing authenticated loopback service and Windows in-memory playback. The microphone audio and transcript are not sent to the voice service; the spoken sentence is not a task answer.
- Updated setup, privacy, model-license and as-built documentation. No OpenAI API, provider credential, cloud STT, ChaseOS canonical integration, push or deployment was used.

## Direct verification

- The optional E: virtual environment installed `faster-whisper==1.2.1`, `sounddevice==0.5.6`, and test-only `pytest==9.1.1`. Model files and dependency caches remain under `E:\Projects\Chaser Agent\Local Runtime`.
- Anonymous model metadata reported MIT and pinned SHA `0d3d19a32d3338f10357c0889762bd8d64bbdeba`; the setup receipt records `model.bin` SHA-256 `1a5afae06a4db91c975c9a9d78be5cc110ee4ea022ad57d55492e4550e936b2a`.
- Existing approved public/toy Alba speech sample converted to 16 kHz mono PCM and transcribed offline as: “An agent can look busy and still tell you almost nothing. With Chaser Agent, we're testing something more useful. Can you see what state it's in and what needs your attention?” CLI returned `draft_unverified`, `transcript_only_no_dispatch`, 8.64-second duration and audio SHA-256 `d83681d05ad40818c24a5243682cccfa30e1b67d6d79e0eda927f834755a3778`.
- Default PortAudio input device reported one input channel and accepted 16 kHz mono int16 settings. That check did **not** record live microphone audio.
- An interactive CLI startup with `q` fed to its prompt loaded the local model, exited normally, and reported “microphone inactive”; no recording began.
- `PYTHONPATH=src python -m pytest -q tests/test_local_stt.py tests/test_voice_ack.py tests/test_local_http.py tests/test_local_voice.py` — 39 passed, 1 skipped (optional NumPy absent in core interpreter).
- E: optional runtime: `python -m pytest -q tests/test_local_stt.py tests/test_voice_ack.py` — 7 passed, no skip. The fixed-ack route was exercised with a fake HTTP service; no speaker playback was auditioned.
- Full core suite: 254 passed, 1 skipped, 31 subtests passed, and the same unrelated locked canon-asset manifest failure (README 1491 bytes versus 1489 in manifest). Approved visual files were not altered.

## Remaining unknowns

Live operator microphone capture, actual speaker playback of the fixed acknowledgement, human listening judgement, noisy/accented STT quality, interruption/barge-in, streaming, text-to-response reasoning, conversation memory, safe voice-to-action handoff, local runtime ACL/privacy review, and full agent voice mode remain unverified or unbuilt. The toy WAV result is functional proof only. See the separate [QA record](<E:/Visual QA/Chaser Agent Visual QA/Current Reviews/2026-09-27-offline-voice-input/QA.md>).
