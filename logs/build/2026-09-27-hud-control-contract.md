# 2026-09-27 — HUD executor control contract

## Repo-truth delta

Before this pass, the desktop HUD showed synthetic/read-only state and its four buttons were always disabled. The in-memory reducer could model pending commands but no local request path could hand a command to an executor or display its acknowledgement.

## Changes

- Added `HudBridge`: a separately governed in-process executor may attach one session and receive a bound event callback. HTTP callers cannot attach executors, start sessions or inject events. Detach invalidates the callback and marks execution status unknown.
- Added authenticated `POST /v1/hud/controls` using the existing loopback token, exact session ID and an available pause/resume/stop/take-over command. The server generates a request ID. Requests stay pending until a matching, newer executor acknowledgement; a dispatch exception leaves the request pending and disables controls.
- The desktop HUD now enables buttons only when the read model reports a connected executor and sends the request via the local API. The synthetic preview remains disabled. The standard `serve` CLI attaches no executor.
- After a lost HTTP poll or inactive HUD response, the window clears its session identity and disables buttons. The adapter contract requires prompt enqueue, and dispatch is serialized with detach while allowing a same-thread immediate acknowledgement.
- An unauthorized POST now drains only a bounded declared body before sending 401, avoiding an observed intermittent Windows connection abort while preserving the authentication boundary.
- Updated the interface/threat docs, as-built map, README, and docs index. No ChaseOS canonical files or separate HUD worktree changed.

## Verification

- `PYTHONPATH=src python -m pytest -q tests/test_hud.py tests/test_local_http.py` — 37 passed twice after the robustness and immediate-ack follow-ups.
- `PYTHONPATH=src python -m pytest -q` — 248 passed, 31 subtests passed, one pre-existing locked canon asset-manifest failure: `brand/chaser-agent/exports/canon-core/v1.0.0-rc.1/README.md` is 1491 bytes on disk versus 1489 recorded. The approved asset and manifest were not modified.
- Network tests show unauthenticated control returns 401; no executor returns 409; an attached fake executor gets exactly one generated request ID; the HUD phase stays running until the matching acknowledgement changes it to paused; detach returns to disabled controls.
- A real CLI instance bound `127.0.0.1:8765` without voice or executor. `GET /v1/health` returned 200 and port 8765; authenticated `GET /v1/hud/current` returned `inactive`, `controls_enabled: false`; authenticated `POST /v1/hud/controls` returned 409 `hud_control_unavailable`. That task-created server was stopped and port 8765 was confirmed closed.

## Remaining authority gap

The fake executor is test-only. There is no activated browser/desktop/computer-use executor, no real stop/take-over proof, no reconnect recovery proof and no visual acceptance of enabled controls. The bearer token becomes a local control credential if a real executor is later attached, so ACL/security review remains necessary. Voice is still speech-out only. No external provider, model download, canonical mutation, push, deploy, real-world action or human eval judgment occurred.
