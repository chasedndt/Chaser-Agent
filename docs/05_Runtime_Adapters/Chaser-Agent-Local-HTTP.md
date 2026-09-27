# Chaser Agent local HTTP foundation

Status: implemented and loopback-tested on the `codex/2026-09-27-standalone-http-foundation` worktree, 2026-09-27. The latest security gate refuses the existing E: runtime because its inherited Windows ACL grants broad local access; the service is not currently running from that directory. This is a pre-alpha local review API with an optional offline speech-out endpoint and executor-gated HUD control contract. It is not an autonomous agent, public web service, connected computer-use controller, or two-way voice mode.

## Start it locally

From this worktree, launch without installing into another agent's Python environment:

```powershell
$env:PYTHONPATH = (Join-Path (Get-Location) 'src')
python -m chaser_agent.cli serve --data-dir 'E:\Projects\Chaser Agent\Local Runtime\2026-09-27-http-foundation' --port 8765
```

The process stays in the foreground. Stop it with Ctrl+C. It prints its health URL and the **path** of its generated bearer-token file, never the token value. Use a private data directory outside the source repository. Startup now checks the directory, token, run directory and optional voice directory permissions before binding. On Windows, only the current user, SYSTEM and Administrators may have allow entries; on POSIX, group/other access is refused. It does **not** change permissions automatically. The existing E: runtime fails this check and requires operator-approved ACL repair and token rotation before reuse. The default listener is `127.0.0.1:8765`; an occupied port fails startup instead of silently changing ports. No provider key or ChaseOS process is required.

Before launch, a read-only preflight can inspect the existing runtime path and briefly probe the intended port:

```powershell
$env:PYTHONPATH = (Join-Path (Get-Location) 'src')
python -m chaser_agent.cli doctor --data-dir 'E:\Projects\Chaser Agent\Local Runtime\2026-09-27-http-foundation' --port 8765
```

`doctor --json` gives the same facts for local automation. The actual 2026-09-27 readback found broad ACLs on the runtime directory, control-token file and runs directory; the port was available **at that check**. The command does not create paths, read token contents, change ACLs, rotate a token or start a server. A `preflight_clear` result is not a live startup or port-ownership guarantee. The command exits nonzero for blocked or incomplete checks; an unavailable ACL inspector is reported as unverified rather than treated as private.

For one foreground process that owns both the API and a visible desktop HUD, use `desktop` with the same data directory and port:

```powershell
python -m chaser_agent.cli desktop --data-dir 'E:\Projects\Chaser Agent\Local Runtime\2026-09-27-http-foundation' --port 8765
```

The combined launcher shows the port and an idle, disabled-control HUD even before any computer-use session exists. Closing that window stops only its own HTTP server thread and optional owned local voice worker. It does not start microphone capture, connect an executor, call a model provider or make the current broad-ACL runtime usable. The normal separate `serve` and `hud` commands remain available. `desktop` may also take the same explicit `--voice-library` and `--allowed-origin` options as `serve`.

`desktop --model-dir <pinned-local-STT-directory>` optionally adds a visible push-to-talk panel. Launch it with the optional E: voice virtual environment described in the [voice-input guide](Chaser-Agent-Local-Voice-Input.md). Model loading is asynchronous and never opens the microphone. Only the Talk button opens a bounded take; Cancel or window close discards it. `--voice-library` is separately required before the panel can speak an exact read-only status answer. Neither option activates general agent reasoning or a tool executor.

For an optional offline Pocket Alba speech adapter on this operator's machine, add `--voice-library 'E:\Projects\Chaser Agent\Shared Speech Library'`. Other installations must explicitly provide their own compatible, approved local library; Chaser Agent does not bundle model weights, download a voice, or choose a cloud fallback. The local model prewarms in the background when configured. `/v1/health` reports `voice: configured_local` and `voice_runtime: starting|ready|busy|failed|cold`; only `ready` means the retained model process has loaded. A configured or ready state does **not** mean the take has been listened to or that two-way voice mode exists.

`GET http://127.0.0.1:8765/v1/health` needs no token. All run routes need `Authorization: Bearer <token>`. The first test source must be public/toy, with privacy class `public_toy` or `public`:

```json
{"title":"Toy research note","text":"The operator must review proposed actions before execution.","privacy_class":"public_toy","profile":"general_source_review"}
```

Send that JSON to `POST /v1/source-cards` with `Content-Type: application/json`. The response gives a run ID and `/v1/runs/<id>` URL. `GET /v1/runs/<id>` lists the artifacts and an `integrity_status`; `GET /v1/runs/<id>/artifacts/original_source.md` returns the exact submitted text when integrity passes. The other artifacts are the seven deterministic review JSON files and `run_log.json`. Claims' `source_location` values are line numbers in `original_source.md`; a `high` extraction confidence is **not** a truth or usefulness judgment. This endpoint creates a pending review, not a human score or approved memory.

## Interface and authority contract

| Route | Auth | Effect |
|---|---|---|
| `GET /v1/health` | None | Process/bind status, disconnected HUD state and local voice-runtime readiness |
| `POST /v1/source-cards` | Bearer | Create one append-only-through-this-API deterministic review run from public text; new runs carry a read-time integrity record |
| `GET /v1/runs/<id>` | Bearer | List artifacts for one HTTP run |
| `GET /v1/runs/<id>/artifacts/<listed-name>` | Bearer | Read one retained source or JSON artifact |
| `GET /v1/hud/current` | Bearer | Read HUD state and controls available for an attached executor; inactive by default |
| `POST /v1/hud/controls` | Bearer | Request pause/resume/stop/take-over for the matching attached session; returns pending until a matching executor acknowledgement |
| `POST /v1/voice/replies` | Bearer | Queue one public/toy Pocket Alba take; returns `202` and a status URL |
| `GET /v1/voice/<id>` | Bearer | Inspect queued, generating, cancelling, cancelled, failed, interrupted, or generated state |
| `POST /v1/voice/<id>/cancel` | Bearer | Request cancellation of this exact queued/generating take with body `{}`; returns `202` while stopping, or terminal state |
| `GET /v1/voice/<id>/audio.wav` | Bearer | Read a receipt-verified WAV after generation |

The source-card routes call no model/provider. If enabled, the voice route invokes only the pinned **local** Pocket TTS runtime; it performs no LLM reasoning and is not speech input. No route executes a computer-use tool, dispatches a proposal, writes ChaseOS state, accepts a human verdict, or promotes a memory. `POST /v1/hud/controls` only dispatches to an already attached, separately authorized **in-process** executor. There is no HTTP route to attach an executor, start a session, or inject an event, and the shipped server attaches none; the endpoint returns `409` in normal startup. The [desktop HUD](../01_Product/Chaser-Agent-Computer-Use-HUD.md) still needs real executor integration and acceptance. Existing CLI `review` and local-governance APIs are separate. The service does not infer that `public` is true: the operator must not submit private or third-party material merely by labelling it public.

New HTTP runs include an internal `.integrity.json` with SHA-256 digests for the nine review/source files. Each authenticated run read checks those files; a changed or missing record returns `409 run_integrity_failed` instead of showing the run as verified. Pre-manifest runs remain readable with `integrity_status: unverified_legacy` and `X-Run-Integrity: unverified_legacy`; they are **not** silently promoted to verified. This detects accidental or unsophisticated after-the-fact changes, but does **not** make the filesystem immutable or resist a same-user actor who can rewrite both files and digests. Keep the private-ACL boundary and independent review.

HUD control body: `{"session_id":"<current-session>","command":"pause"}`. The server generates a unique request ID, records pending state, and returns `202`. Only a newer event from that attached executor with the same request ID and expected phase settles it. A disconnect or dispatch exception disables controls and reports uncertain execution; it does not claim the command succeeded. The same in-process executor object may reattach to its uncertain session, but controls remain disabled until it reports a fresh, higher-sequence event; a different object or session cannot take over that unknown state. Old report callbacks are rejected. A terminal session may be replaced by a new authorized attachment. `take_over` means the executor must acknowledge `stopped` before the operator is told control is available. The loopback bearer token is therefore a **control credential** once an executor is attached; it must not be copied into browser pages, logs, or other accounts. No executor is attached by the standard CLI.

Voice POST body: `{"text":"Ready for review.","privacy_class":"public_toy"}` (1–500 characters). Wait for `voice_runtime: ready`, then POST; poll the returned `status_url` until `generated_pending_listening_review` and fetch `audio_url`. A request while prewarming or generating gets `409 voice_busy`. The local worker and its Windows child interpreter are stopped when the server closes. The original script, WAV and generation receipt remain under the explicit data directory; a take is **not** accepted media until a human listens. On this machine, the retained model took minutes to load, while a second warm reply completed end-to-end in 4.52 seconds. This is speech-out infrastructure, not microphone interaction or a completed conversational voice mode.

For a pending take, POST `{}` to its exact `status_url` plus `/cancel` with the same bearer token. A `cancelling` response means a stop was requested, **not** that the child has stopped; poll until `cancelled`. Cancellation writes a marker in that take's folder before attempting to stop only the owned local child process. The marker suppresses audio retrieval even if a late WAV and receipt appear or the service restarts. Already-terminal generated takes remain generated; this route does not delete files or control an unrelated audio player. The HUD's Cancel reply button requests this path through its local client during pending generation. Fake-worker tests cover cancellation and a later warm-worker restart; actual Pocket Alba timing remains unverified while the E: runtime ACL gate blocks launch.

A separate [opt-in offline voice-input CLI](Chaser-Agent-Local-Voice-Input.md) can now transcribe an explicit short microphone take as a draft. Its optional fixed acknowledgement uses this HTTP voice route, but **never sends microphone audio or recognized text to the service**. The HTTP service still does not accept microphone audio, generate context-aware agent answers, or dispatch from voice.

## Local threat model

- **Bind and DNS rebinding:** socket binds only to `127.0.0.1`; every request must use the exact `Host: 127.0.0.1:<bound-port>` and come from loopback. There is no LAN/public bind option.
- **Browser-origin/CSRF boundary:** browser requests with `Origin` are rejected unless same-origin. A future local UI may opt into one explicit `http://127.0.0.1:<port>` origin with `--allowed-origin`; wildcard/reflected origins and non-loopback sites are rejected. An allowed origin still needs the bearer token. Do not expose the token to arbitrary web pages.
- **Auth and data:** a 256-bit random token is created in the data directory, reused across restarts, and never logged by the server. Run reads and creation require it. The service refuses broad OS ACLs before reading the token or writing runs. `0o600` creation flags alone are **not** a Windows ACL guarantee. The previously broad E: runtime should be treated as having a potentially exposed token; the new startup gate does not retroactively protect it. No permission change or rotation is performed without explicit operator approval. This does not defend against malware running as the same user or a compromised allowed-origin app.
- **Local clients:** the normal desktop HUD and optional voice client now apply the same read-only directory/token ACL gate before loading the bearer credential. The HUD caches it for one session and must restart after rotation. A narrow speech status feature may read `/v1/health` and `/v1/hud/current` but never posts a transcribed command to `/v1/hud/controls`.
- **Parsing and resource limits:** JSON only, one `Content-Length`, 256 KiB max body, 100,000-character source max, duplicate JSON keys rejected, 10-second socket timeout, and 20 authenticated POSTs/minute per process. Early-rejected POSTs drain only a declared body up to 8 KiB before closing, so ordinary Windows clients can receive the error without a reset; malformed/large bodies are not unboundedly drained. At most 16 client handler threads are admitted simultaneously; excess connections receive a minimal `503 Service Unavailable` and are closed. The slot is released when a handler exits, including on disconnect/error. This is not a comprehensive DoS control; Python's threaded HTTP server is not suitable for untrusted public traffic.
- **Path/storage:** run IDs and artifact names are allowlisted; traversal and symlink artifact reads are rejected. The original source and generated run files live outside the repo. A run is built in a non-routable `.pending-...` folder and renamed into the visible run path only after the source, JSON artifacts and integrity record are written. New runs are SHA-256-checked on each read; old runs are labelled unverified, not cryptographically sealed. A crash may leave a pending folder for an operator to inspect; there is no automatic destructive cleanup or retention policy yet.
- **Logging/response:** raw request logging is disabled. Responses set `no-store`, `nosniff`, and a deny-by-default CSP. Health reveals only local service state; it does not prove a provider, HUD, voice, or eval quality is ready.
- **Voice jobs:** HTTP callers cannot choose the executable, preset, model, path, or provider. The adapter uses the approved Pocket Alba manifest, retained production cache and pinned local runtime with Hugging Face offline flags. It keeps one model worker, caps startup and per-take waits, requests stop only for its exact owned child on cancellation/shutdown, and requires receipt/hash verification before authenticated audio readback. A per-take cancellation marker suppresses late audio, including after restart. This does not defend against a malicious same-user edit to the operator-selected speech library, and it does not make new speech automatically publishable.
- **HUD controls:** an authenticated HTTP caller cannot create an executor or forge its status events. The in-process attachment is a separate authority gate, and one session is bound at a time. A disconnected transport leaves execution status unknown; only the identical in-process executor can reconnect that nonterminal session, and a fresh event is required before controls return. This is an identity/lifecycle safeguard within one process, not process-crash recovery or proof that the executor stopped. This contract has fake-executor tests, not a real computer-use safety result; future adapters must redact action text before reporting it and enforce their own grants.

The [standard-library HTTP server](https://docs.python.org/3/library/http.server.html) carries its own security caveat and is used here only for a tightly bounded local engineering slice. Before any wider access, review authentication/ACLs, concurrency, protocol handling, request logging, TLS/proxy policy, Windows firewall behavior, data retention, and independent security testing. An HTTP listener is plumbing, not evidence that the agent harness can act safely.

## Next engineering gates

1. Integrate a genuinely authorized computer-use executor with the in-process HUD bridge and test stop/take-over under a bounded real task. Same-process owner reconnection and old-callback rejection now have fake-executor coverage; process-crash recovery, real task races and stop/take-over acceptance remain open.
2. Improve warm speech latency and verify cancellation/playback with the actual Pocket Alba worker and operator listening. Explicit push-to-talk, local STT, consent indicators and output-only chunked HUD playback now exist; the older CLI acknowledgement still uses blocking Windows playback. Device-level stop latency, natural speech barge-in and an explicit conversation contract still need acceptance and separate permissions. This speech-out job API alone is not Jarvis-style voice mode.
3. Keep human product-quality judgments in Agent Review Studio. Once the operator supplies accepted verdicts, encode them as regression cases; do not generate the verdicts in this engineering branch.
