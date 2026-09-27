# 2026-09-27 — HUD owner reconnection

## Repo-truth delta

The HUD bridge previously invalidated a disconnected executor's callback but would reject every later attachment while the old session was nonterminal. A transient in-process transport loss therefore stranded that session with unknown execution status. The shipped desktop still attaches no computer-use executor.

## Changes

- Preserve the disconnected session, sequence and pending-control uncertainty. Only the identical in-process executor object may reattach the identical nonterminal session. An unrelated object or different session cannot claim it.
- Keep controls disabled until that owner reports a fresh higher-sequence event. The old callback remains invalid by generation check. A terminal session can be replaced by a new authorized attachment.
- Add fake-executor tests for rejected foreign reconnection, stale callback, pending-control settlement and terminal replacement.

## Verification

- `PYTHONPATH=src python -m pytest -q tests/test_hud.py tests/test_local_http.py tests/test_local_desktop.py` — **57 passed**.
- `PYTHONPATH=src python -m pytest -q` — **317 passed, 1 skipped, 31 subtests passed, 1 failed** in 41.99s. The single failure is the existing locked canon-core manifest mismatch: approved `brand/chaser-agent/exports/canon-core/v1.0.0-rc.1/README.md` is 1491 bytes, while its manifest says 1489. This slice did not edit either file.
- The prior read-only `doctor` preflight still shows port `127.0.0.1:8765` available at check time but refuses startup for broad ACLs on the E: runtime directory, token file and runs directory. No live service, real executor, microphone or audio test was run in this slice.

## Boundaries and remaining work

Object identity only supports same-process reconnection. It is not proof of process-crash recovery, a persisted execution journal, or an authorized computer-use adapter. A pending control remains unknown until an appropriate fresh event arrives. Live runtime still needs explicit operator authority for private ACL repair and token rotation. The full HTTP/HUD/voice goal stays active.
