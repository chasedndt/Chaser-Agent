# 2026-09-27 — optional desktop push-to-talk panel

## Repo-truth delta

The one-process `desktop` launcher previously showed local HTTP/HUD state but had no microphone control. A separate CLI could transcribe an explicit take, and exact read-only status speech existed, but neither was operable from the desktop window. The current E: service runtime remains blocked by broad Windows ACLs.

## Changes

- Added optional `desktop --model-dir <pinned-local-STT-directory>`. It loads the already-installed offline model asynchronously without opening a microphone; Talk starts one five-second take only after the active indicator is painted. Cancel and window close set a cancellation event and discard partial audio. Short 0.1-second reads check cancellation around each read; device-driver latency remains unverified.
- The HUD displays an unverified, in-memory draft with no action authority. A separate Speak status button is enabled only for an exact allowlisted read-only question and only when an approved local Pocket Alba library was explicitly configured. It does not send transcript text to the HTTP service or HUD controls. Window close suppresses late UI callbacks and cancels speech before new playback, although already-blocking playback cannot be interrupted here.
- The first simulated 200%-style Tk scaling revealed serious clipping in the fixed HUD geometry. The window now scales with text, caps to available screen bounds and offers a scrollbar when its content exceeds the screen. Pending Tk timers are cancelled on close. This is a synthetic layout correction, not real-device accessibility acceptance.
- Model errors leave the microphone inactive. Failure to paint the microphone indicator prevents the capture worker from starting. Background model/speech events are queued for the Tk UI thread, so a fast model cannot lose its ready event before the main loop starts. The service/HUD still launch without `--model-dir` and still attach no computer-use executor or reasoning provider.
- Updated product/runtime guides and synthetic visual QA. No new model download, provider credential, canonical ChaseOS mutation, token/ACL repair, push or deployment occurred.

## Verification

- `PYTHONPATH=src python -m pytest -q tests/test_desktop_voice.py tests/test_local_stt.py tests/test_local_desktop.py tests/test_hud.py tests/test_voice_ack.py tests/test_voice_status.py tests/test_local_http.py tests/test_local_acl.py tests/test_local_voice.py` — **83 passed, 1 skipped**. Coverage includes explicit-only capture, cancellation, device closure, failed-indicator refusal, draft-only behavior, exact status-speech gating, queued background UI updates, scale-aware dimensions, local HTTP and HUD contracts.
- Optional E: voice virtual environment: `python -m pytest -q tests/test_desktop_voice.py tests/test_local_stt.py tests/test_voice_ack.py tests/test_voice_status.py tests/test_hud.py` — **39 passed**.
- The installed pinned E: STT model loaded through `DesktopVoiceController`: `model_state=ready`, `capture_started=False`. No microphone was opened by that check.
- `python -m chaser_agent.cli desktop --help` shows optional `--model-dir` and fixed default port 8765.
- Direct `desktop` launch against the existing broad-ACL E: runtime with `--model-dir` — exit **2** before GUI/model/microphone startup; no permissions changed.
- [Synthetic desktop voice-panel QA](<E:/Visual QA/Chaser Agent Visual QA/Current Reviews/2026-09-27-desktop-voice-panel/QA.md>) — 410 × 452 px ready/recording layouts, a corrected 820 × 904 px 200%-style layout, and a 760 × 520 px simulated small-screen scrolled view. A contradictory draft line and high-scale clipping were corrected before final capture. These images use no real microphone or service.
- Full core suite — **288 passed, 1 skipped, 31 subtests passed, 1 failed** in 73.26s. The sole failure remains the pre-existing locked canon-core asset-manifest mismatch: approved `brand/chaser-agent/exports/canon-core/v1.0.0-rc.1/README.md` is 1491 bytes, manifest says 1489. Neither was edited.

## Remaining gates

Operator-approved ACL repair and token rotation are required before real desktop startup. Then verify live device open/cancel latency, actual spoken reply/listening quality, STT accuracy in noise/accents, accessibility and high-DPI visual behavior. A chosen/authorized reasoning provider and real computer-use executor are still absent; this is not full Jarvis-style conversation or HUD-in-unison-with-computer-use acceptance. The Codex engineering goal remains active.
