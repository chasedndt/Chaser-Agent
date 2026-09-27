# Chaser Agent local voice input — opt-in engineering lane

Status, 2026-09-27: an **interactive push-to-talk CLI** and a pinned offline English speech-to-text model work on a public/toy WAV. Live microphone capture is implemented but has **not** been exercised with the operator's microphone or accepted by a human listener. A new opt-in read-only status response is tested with mocked local HTTP, but not live speech playback. This is not a conversational agent: the transcript is an unverified draft, no LLM formulates a general reply, and no tool/computer-use/memory action is dispatched.

## What the command does

`voice-mode` loads a receipt-verified model from an explicit local directory once, then waits for the operator to press Enter before each bounded microphone capture. It prints `MICROPHONE ACTIVE`, records up to 0.5–12 seconds of 16 kHz mono PCM in memory, closes the device, and prints `MICROPHONE OFF` before local transcription. `q` quits. Ctrl+C during capture discards that take. No wake word or background listening exists. Neither raw microphone audio nor its transcript is sent to a cloud API or written to the repository by this command.

Each result says `draft_unverified` (or `no_speech`) and `transcript_only_no_dispatch`. It is **not** a command to the harness. Do not treat model text as operator approval, a safe intent, a correct quote, or evidence of an action being performed.

The draft is printed in the local terminal. Operators should use a private terminal session if their shell, screen recorder or support tooling logs console output; this command does not control those external logs.

Optional `--speak-ack` asks a separately running, voice-enabled `127.0.0.1:8765` service to generate and play one fixed public/toy acknowledgement: “I heard you. The draft transcript is ready for your review.” The transcript is never sent to that service. The acknowledgement is not an answer to the user's request. It uses the existing authenticated Pocket Alba route and Windows in-memory WAV playback; the service must already report `voice_runtime: ready`.

Optional `--speak-status` recognizes only a small allowlist of exact questions, such as “What's your status?”, “Is computer use active?” and “What port are you running on?”. It reads local service health and authenticated HUD state, then speaks a bounded answer that does **not** include source text, HUD action, session ID or the transcript. An unknown phrase or command does nothing; if `--speak-ack` is also present, it gets only the fixed acknowledgement. This is a read-only status feature, not general reasoning or voice-to-action. Both speech options refuse broad runtime/token permissions before reading the credential.

The combined desktop command now has an optional `--model-dir` panel for the same pinned offline model. It loads the model in a background thread while the microphone stays off. The visible Talk button opens one five-second in-memory take; Cancel and window close set a cancellation event and discard partial audio. The indicator is painted before the capture worker may open the device. The displayed transcript is truncated to 150 characters, retained only in process memory as an unverified draft, and cleared by Clear draft or window close. A separate Speak status click is enabled only for an exact allowlisted question and only when `--voice-library` was configured; it never posts the transcript or HUD control command. The panel does not provide free-form conversational replies.

While a local status reply is pending, **Speak status** becomes **Cancel reply**. **Talk** becomes **Talk next**: an explicit click requests the same token-protected stop of the exact speech take, then waits for the output worker's completion event before beginning a new push-to-talk capture. It never opens the microphone merely because speech began; Clear draft revokes a queued Talk next. The server records a cancellation marker so late generated audio stays inaccessible. For the desktop HUD, the optional speech environment plays bounded 16-bit PCM or 32-bit IEEE-float WAV (the latter matches the worker's SciPy write path) through an output-only stream in about 50 ms chunks and aborts pending output buffers on cancellation. This is a tested click-to-interrupt sequence, **not** proven natural barge-in: device writes and shutdown can still add latency, and the operator has not listened to a real take. The CLI's fixed acknowledgement retains blocking Windows in-memory playback. [Synthetic button-state QA](<E:/Visual QA/Chaser Agent Visual QA/Current Reviews/2026-09-27-voice-cancel/QA.md>) predates Talk next and is not a real listening test.

Each desktop take now has an in-process sequence ID. The HUD ignores late draft, cancellation or transcription events from an older take after a newer recording begins; a cancellation arriving before the final result is emitted discards that result. This is UI-state race protection, not proof of real microphone-driver cancellation latency.

At narrow HUD widths, status and draft text wrap to the available canvas width and the four computer-use controls plus three voice controls reflow to two rows. A [synthetic before/after visual audit](<E:/Visual QA/Chaser Agent Visual QA/Current Reviews/2026-09-27-talk-next-hud/QA.md>) caught clipped labels and verified the correction at the tested size. When Talk next has been clicked, the waiting controls say **Talk queued** and **Stopping reply**. These captures used no microphone, speaker, model or live service; they do not prove keyboard or screen-reader usability.

## One-time setup, kept on E:

Use a separate Python virtual environment and dependency cache under an E: runtime directory. This pass locally tested `faster-whisper==1.2.1` and `sounddevice==0.5.6`; they are optional and not imported by the deterministic core. The [faster-whisper implementation](https://github.com/SYSTRAN/faster-whisper) supports local-directory models and CPU int8 inference. The selected [tiny English model](https://huggingface.co/Systran/faster-whisper-tiny.en/tree/0d3d19a32d3338f10357c0889762bd8d64bbdeba) is MIT-licensed. Tiny is a functionality baseline, **not** an accuracy acceptance choice for real agent commands.

```powershell
$env:PIP_CACHE_DIR = 'E:\Projects\Chaser Agent\Local Runtime\pip-cache'
$env:HF_HOME = 'E:\Projects\Chaser Agent\Local Runtime\hf-cache'
python -m venv 'E:\Projects\Chaser Agent\Local Runtime\stt-venv'
& 'E:\Projects\Chaser Agent\Local Runtime\stt-venv\Scripts\python.exe' -m pip install faster-whisper==1.2.1 sounddevice==0.5.6
$env:PYTHONPATH = (Join-Path (Get-Location) 'src')
& 'E:\Projects\Chaser Agent\Local Runtime\stt-venv\Scripts\python.exe' scripts/setup_local_stt.py --output 'E:\Projects\Chaser Agent\Local Runtime\stt-models\faster-whisper-tiny.en-0d3d19a' --accept-download
```

The setup command is the **only** download step. It uses anonymous access, pins revision `0d3d19a32d3338f10357c0889762bd8d64bbdeba`, and creates `stt-model.json` with SHA-256 values for the four required model files. Normal `voice-mode` verifies that receipt and passes a local path with `local_files_only=True`; it cannot silently download another model.

The receipt detects changes **after local setup**. It is not an independent signature or a full upstream supply-chain audit.

From the repo root, a no-microphone proof with a 16 kHz mono 16-bit PCM toy WAV is:

```powershell
$env:PYTHONPATH = (Join-Path (Get-Location) 'src')
& 'E:\Projects\Chaser Agent\Local Runtime\stt-venv\Scripts\python.exe' -m chaser_agent.cli voice-mode --model-dir 'E:\Projects\Chaser Agent\Local Runtime\stt-models\faster-whisper-tiny.en-0d3d19a' --sample-wav 'E:\Projects\Chaser Agent\Local Runtime\stt-test-alba-16k.wav'
```

Omit `--sample-wav` for explicit interactive capture. The command never opens the microphone before the operator presses Enter. Add `--speak-ack` or `--speak-status` with `--data-dir <same-data-dir-as-serve>` only if the local HTTP service was started with `--voice-library` and is ready. The default service port is 8765; use the same `--port` on both commands if changed. The existing E: data directory currently has broad Windows ACLs, so these speech options fail closed until its permissions and token are repaired with operator approval. Plain transcription still works without the service.

For the desktop panel after that approval, use the same E: virtual environment and add `--model-dir <same pinned model path>` to `desktop`; add `--voice-library <approved local Pocket Alba library>` only if speech-out is desired. This is a local setup choice, not approval for background listening. The current broad-ACL runtime still prevents a live desktop launch. A [synthetic voice-panel visual QA record](<E:/Visual QA/Chaser Agent Visual QA/Current Reviews/2026-09-27-desktop-voice-panel/QA.md>) shows the ready and recording-indicator layouts without opening a microphone.

## Evidence and limits

The existing approved Alba toy sample was converted to PCM 16 kHz under the E: local runtime; `voice-mode --sample-wav` transcribed its sentence about Chaser Agent and operator attention correctly on this machine. The sample contained no private operator speech. The local model receipt records the pinned revision and model hashes. Focused tests cover receipt tampering, PCM/WAV limits, explicit microphone opening, no-speech handling, draft-only output, and the fixed-text acknowledgement request. See the [build log](../../logs/build/2026-09-27-offline-voice-input.md).

Still missing: operator microphone acceptance, listening quality, word-error-rate evaluation across accents/noise, device-level interruption/barge-in acceptance, streaming, approved ACL repair/token rotation, per-user voice settings, conversation state, an authorized reasoning/provider adapter, and general response text tied to the request. The HTTP voice jobs retain generated WAVs and receipts in their configured E: data directory; cancelled takes also retain a marker and cannot expose late audio through the API. `voice-mode` and the desktop panel do not retain raw captures. The read-only status reply, server-side cancellation, chunked HUD output and Talk-next sequencing are unit-tested with mocked audio/workers, not human-auditioned on the current runtime. The installed optional `sounddevice` 0.5.6 environment accepted read-only 24 kHz mono/int16 and float32 output-settings checks; no speaker opened in those checks. Device write/abort latency and the legacy CLI's blocking playback need live acceptance testing.
