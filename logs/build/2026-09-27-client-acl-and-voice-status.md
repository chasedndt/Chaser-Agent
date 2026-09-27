# 2026-09-27 — local client ACL and read-only voice status

## Repo-truth delta

The loopback server refused broad Windows runtime permissions, but the desktop HUD and fixed-acknowledgement client still read the token file directly. Push-to-talk could transcribe a draft or speak a fixed acknowledgement, not answer even a local status question. The existing E: runtime is broad and remains unsuitable for bearer-token use.

## Changes

- Added one shared read-only token loader that checks both the runtime directory and token ACL before reading. The normal HUD loads it before opening its window and caches it for that session; the voice client checks on each requested take. Neither changes permissions or rotates the token.
- Added `voice-mode --speak-status`: an opt-in, exact-phrase allowlist for read-only questions about local service status and port. It fetches `/v1/health` and authenticated `/v1/hud/current`, validates the local service identity, and forms a short Pocket Alba reply from allowlisted fields. It never includes the raw transcript, action summary, session ID, source content or token in spoken text, and never calls HUD controls. Unknown phrases/commands do nothing, or get only the existing fixed acknowledgement if `--speak-ack` is also selected.
- Corrected the normal HUD example path, expanded the HTTP/voice/HUD guides and the full engineering-goal boundary. No LLM/provider adapter, real executor, command dispatch or live microphone acceptance was introduced.

## Verification

- `PYTHONPATH=src python -m pytest -q tests/test_local_http.py tests/test_local_acl.py tests/test_voice_ack.py tests/test_voice_status.py tests/test_hud.py tests/test_local_stt.py` — **62 passed, 1 skipped**. This covers exact intent matching, rejected command/prompt-injection text, response redaction, read-only HTTP routing, client ACL refusal and CLI status selection.
- E: optional voice venv, `python -m pytest -q tests/test_local_stt.py tests/test_voice_status.py tests/test_voice_ack.py` — **17 passed**.
- Direct normal HUD CLI against the current E: runtime — exit **2** before a window, `Runtime path has broad Windows ACL access; no permissions were changed`.
- Direct speech client against that runtime — `InsecureRuntimePath` before a token read or network request. No audio was generated.
- Pinned offline voice CLI with the existing public/toy Alba WAV and `--speak-status` — exit **0**, same draft transcript and hash `d83681d05ad40818c24a5243682cccfa30e1b67d6d79e0eda927f834755a3778`; the sentence was not an exact status question, so no reply was generated and no local service was contacted.
- Full core suite — **273 passed, 1 skipped, 31 subtests passed, 1 failed** in 97.72s. The sole failure remains the pre-existing locked canon-core manifest mismatch: approved `brand/chaser-agent/exports/canon-core/v1.0.0-rc.1/README.md` is 1491 bytes, manifest says 1489. This slice did not edit either.
- `git diff --check` — no whitespace errors.

## Limits and next gates

The status reply's HTTP and audio path is tested with a fake local service and in-memory WAV playback hook; it was not played live from the current broad-ACL runtime. Operator-approved ACL repair and token rotation are still needed before a safe live run. Real microphone/STT quality, operator listening acceptance, live HUD state with a real authorized executor, interruption, conversation state and a chosen reasoning provider remain unverified or absent. No ChaseOS canonical write, external call, push, merge, deployment or approval-sensitive action occurred.
