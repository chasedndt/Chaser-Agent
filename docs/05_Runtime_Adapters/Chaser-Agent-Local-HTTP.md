# Chaser Agent local HTTP foundation

Status: implemented and loopback-tested on the `codex/2026-09-27-standalone-http-foundation` worktree, 2026-09-27. This is a pre-alpha local review API with an optional offline speech-out endpoint and display-only HUD state. It is not an autonomous agent, public web service, connected computer-use controller, or two-way voice mode.

## Start it locally

From this worktree, launch without installing into another agent's Python environment:

```powershell
$env:PYTHONPATH = (Join-Path (Get-Location) 'src')
python -m chaser_agent.cli serve --data-dir 'E:\Projects\Chaser Agent\Local Runtime\http-foundation' --port 8765
```

The process stays in the foreground. Stop it with Ctrl+C. It prints its health URL and the **path** of its generated bearer-token file, never the token value. Use a private data directory outside the source repository. The default listener is `127.0.0.1:8765`; an occupied port fails startup instead of silently changing ports. No provider key or ChaseOS process is required.

For an optional offline Pocket Alba speech adapter on this operator's machine, add `--voice-library 'E:\Projects\Chaser Agent\Shared Speech Library'`. Other installations must explicitly provide their own compatible, approved local library; Chaser Agent does not bundle model weights, download a voice, or choose a cloud fallback. The local model prewarms in the background when configured. `/v1/health` reports `voice: configured_local` and `voice_runtime: starting|ready|busy|failed|cold`; only `ready` means the retained model process has loaded. A configured or ready state does **not** mean the take has been listened to or that two-way voice mode exists.

`GET http://127.0.0.1:8765/v1/health` needs no token. All run routes need `Authorization: Bearer <token>`. The first test source must be public/toy, with privacy class `public_toy` or `public`:

```json
{"title":"Toy research note","text":"The operator must review proposed actions before execution.","privacy_class":"public_toy","profile":"general_source_review"}
```

Send that JSON to `POST /v1/source-cards` with `Content-Type: application/json`. The response gives a run ID and `/v1/runs/<id>` URL. `GET /v1/runs/<id>` lists the artifacts; `GET /v1/runs/<id>/artifacts/original_source.md` returns the exact submitted text. The other artifacts are the seven deterministic review JSON files and `run_log.json`. Claims' `source_location` values are line numbers in `original_source.md`; a `high` extraction confidence is **not** a truth or usefulness judgment. This endpoint creates a pending review, not a human score or approved memory.

## Interface and authority contract

| Route | Auth | Effect |
|---|---|---|
| `GET /v1/health` | None | Process/bind status, disconnected HUD state and local voice-runtime readiness |
| `POST /v1/source-cards` | Bearer | Create one immutable deterministic review run from public text |
| `GET /v1/runs/<id>` | Bearer | List artifacts for one HTTP run |
| `GET /v1/runs/<id>/artifacts/<listed-name>` | Bearer | Read one retained source or JSON artifact |
| `GET /v1/hud/current` | Bearer | Read display-only computer-use state; currently inactive without an executor |
| `POST /v1/voice/replies` | Bearer | Queue one public/toy Pocket Alba take; returns `202` and a status URL |
| `GET /v1/voice/<id>` | Bearer | Inspect queued, generating, failed, interrupted, or generated state |
| `GET /v1/voice/<id>/audio.wav` | Bearer | Read a receipt-verified WAV after generation |

The source-card routes call no model/provider. If enabled, the voice route invokes only the pinned **local** Pocket TTS runtime; it performs no LLM reasoning and is not speech input. No route executes a computer-use tool, dispatches a proposal, writes ChaseOS state, accepts a human verdict, or promotes a memory. The HUD has no HTTP event-injection or control route; its [desktop preview and remaining gates](../01_Product/Chaser-Agent-Computer-Use-HUD.md) are separate from executor activation. Existing CLI `review` and local-governance APIs are separate. The service does not infer that `public` is true: the operator must not submit private or third-party material merely by labelling it public.

Voice POST body: `{"text":"Ready for review.","privacy_class":"public_toy"}` (1–500 characters). Wait for `voice_runtime: ready`, then POST; poll the returned `status_url` until `generated_pending_listening_review` and fetch `audio_url`. A request while prewarming or generating gets `409 voice_busy`. The local worker and its Windows child interpreter are stopped when the server closes. The original script, WAV and generation receipt remain under the explicit data directory; a take is **not** accepted media until a human listens. On this machine, the retained model took minutes to load, while a second warm reply completed end-to-end in 4.52 seconds. This is speech-out infrastructure, not microphone interaction or a completed conversational voice mode.

## Local threat model

- **Bind and DNS rebinding:** socket binds only to `127.0.0.1`; every request must use the exact `Host: 127.0.0.1:<bound-port>` and come from loopback. There is no LAN/public bind option.
- **Browser-origin/CSRF boundary:** browser requests with `Origin` are rejected unless same-origin. A future local UI may opt into one explicit `http://127.0.0.1:<port>` origin with `--allowed-origin`; wildcard/reflected origins and non-loopback sites are rejected. An allowed origin still needs the bearer token. Do not expose the token to arbitrary web pages.
- **Auth and data:** a 256-bit random token is created in the data directory, reused across restarts, and never logged by the server. Run reads and creation require it. Token-file secrecy depends on the OS ACL of the chosen E: directory; `0o600` creation flags alone are **not** a Windows ACL guarantee. This is not hardened against another local account with read access to that directory, malware running as the same user, or a compromised allowed-origin app.
- **Parsing and resource limits:** JSON only, one `Content-Length`, 256 KiB max body, 100,000-character source max, duplicate JSON keys rejected, 10-second socket timeout, and 20 authenticated POSTs/minute per process. This is not a comprehensive DoS control; Python's threaded HTTP server is not suitable for untrusted public traffic.
- **Path/storage:** run IDs and artifact names are allowlisted; traversal and symlink artifact reads are rejected. The original source and generated run files live outside the repo. A run is built in a non-routable `.pending-...` folder and renamed into the visible run path only after the source and JSON artifacts are written. A crash may leave a pending folder for an operator to inspect; there is no automatic destructive cleanup or retention policy yet.
- **Logging/response:** raw request logging is disabled. Responses set `no-store`, `nosniff`, and a deny-by-default CSP. Health reveals only local service state; it does not prove a provider, HUD, voice, or eval quality is ready.
- **Voice jobs:** HTTP callers cannot choose the executable, preset, model, path, or provider. The adapter uses the approved Pocket Alba manifest, retained production cache and pinned local runtime with Hugging Face offline flags. It keeps one model worker, caps startup and per-take waits, terminates the exact owned Windows process tree on shutdown, and requires receipt/hash verification before authenticated audio readback. This does not defend against a malicious same-user edit to the operator-selected speech library, and it does not make new speech automatically publishable.

The [standard-library HTTP server](https://docs.python.org/3/library/http.server.html) carries its own security caveat and is used here only for a tightly bounded local engineering slice. Before any wider access, review authentication/ACLs, concurrency, protocol handling, request logging, TLS/proxy policy, Windows firewall behavior, data retention, and independent security testing. An HTTP listener is plumbing, not evidence that the agent harness can act safely.

## Next engineering gates

1. Connect a **read-only** live run/event stream to the existing HUD state model, retaining an explicit stop/approval boundary. Do not infer computer-use authority from visual controls.
2. Improve warm speech latency and add cancellation. Then add microphone capture, offline speech-to-text, consent indicators, interruption/barge-in and an explicit conversation contract behind separate permissions. This speech-out job API alone is not Jarvis-style voice mode.
3. Keep human product-quality judgments in Agent Review Studio. Once the operator supplies accepted verdicts, encode them as regression cases; do not generate the verdicts in this engineering branch.
