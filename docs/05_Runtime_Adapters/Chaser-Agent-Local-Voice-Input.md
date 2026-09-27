# Chaser Agent local voice input — opt-in engineering lane

Status, 2026-09-27: an **interactive push-to-talk CLI** and a pinned offline English speech-to-text model work on a public/toy WAV. Live microphone capture is implemented but has **not** been exercised with the operator's microphone or accepted by a human listener. This is not a conversational agent: the transcript is an unverified draft, no LLM formulates a reply, and no tool/computer-use/memory action is dispatched.

## What the command does

`voice-mode` loads a receipt-verified model from an explicit local directory once, then waits for the operator to press Enter before each bounded microphone capture. It prints `MICROPHONE ACTIVE`, records up to 0.5–12 seconds of 16 kHz mono PCM in memory, closes the device, and prints `MICROPHONE OFF` before local transcription. `q` quits. Ctrl+C during capture discards that take. No wake word or background listening exists. Neither raw microphone audio nor its transcript is sent to a cloud API or written to the repository by this command.

Each result says `draft_unverified` (or `no_speech`) and `transcript_only_no_dispatch`. It is **not** a command to the harness. Do not treat model text as operator approval, a safe intent, a correct quote, or evidence of an action being performed.

The draft is printed in the local terminal. Operators should use a private terminal session if their shell, screen recorder or support tooling logs console output; this command does not control those external logs.

Optional `--speak-ack` asks a separately running, voice-enabled `127.0.0.1:8765` service to generate and play one fixed public/toy acknowledgement: “I heard you. The draft transcript is ready for your review.” The transcript is never sent to that service. The acknowledgement is not an answer to the user's request. It uses the existing authenticated Pocket Alba route and Windows in-memory WAV playback; the service must already report `voice_runtime: ready`.

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

Omit `--sample-wav` for explicit interactive capture. The command never opens the microphone before the operator presses Enter. Add `--speak-ack --data-dir <same-data-dir-as-serve>` only if the local HTTP service was started with `--voice-library` and is ready. The default service port is 8765; use the same `--port` on both commands if changed.

## Evidence and limits

The existing approved Alba toy sample was converted to PCM 16 kHz under the E: local runtime; `voice-mode --sample-wav` transcribed its sentence about Chaser Agent and operator attention correctly on this machine. The sample contained no private operator speech. The local model receipt records the pinned revision and model hashes. Focused tests cover receipt tampering, PCM/WAV limits, explicit microphone opening, no-speech handling, draft-only output, and the fixed-text acknowledgement request. See the [build log](../../logs/build/2026-09-27-offline-voice-input.md).

Still missing: operator microphone acceptance, listening quality, word-error-rate evaluation across accents/noise, interruption/barge-in, streaming, privacy review of the runtime directory/Windows ACLs, per-user voice settings, conversation state, an authorized reasoning/provider adapter, and response text tied to the actual request. The HTTP voice jobs retain generated WAVs and receipts in their configured E: data directory; `voice-mode` itself does not retain the raw capture.
