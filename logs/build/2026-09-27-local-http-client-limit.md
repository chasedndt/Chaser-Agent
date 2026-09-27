# 2026-09-27 — bounded local HTTP client handlers

## Repo-truth delta

The loopback service already had exact host/origin checks, bearer authentication, request-size and authenticated POST-rate limits, but inherited Python's unbounded thread-per-accepted-connection behavior. A local client could exhaust handler threads even without a valid bearer token. The existing E: runtime still fails its broad-ACL startup gate.

## Changes

- Cap concurrent HTTP client handlers at 16 using a server-owned bounded semaphore. A full listener sends a minimal no-store `503 Service Unavailable` and closes the new connection without parsing it or spawning a handler thread.
- Release the slot after normal completion, disconnect or handler error; guard against a thread-start failure. Production callers cannot increase the cap above 16.
- Add a network-level overflow/recovery test and invalid-limit tests. Document the remaining local-only DoS limits.

## Verification

- `PYTHONPATH=src python -m pytest -q tests/test_local_http.py` — **32 passed**. The overflow test holds one handler, sees a raw `503` on the next socket, then confirms `/v1/health` returns `200` after release.
- `PYTHONPATH=src python -m pytest -q` — **291 passed, 1 skipped, 31 subtests passed, 1 failed** in 63.47s. The sole failure is the pre-existing locked canon-core asset-manifest mismatch: approved `brand/chaser-agent/exports/canon-core/v1.0.0-rc.1/README.md` is 1491 bytes, while the manifest says 1489. Neither file was edited in this slice.

## Boundaries and remaining work

No operator eval data or judgments changed. No real runtime permissions or bearer token changed, so the existing E: data directory remains unusable until explicit operator approval for ACL repair and rotation. The server is not suitable for untrusted public or LAN traffic. Real executor/HUD behavior and operator-accepted conversational voice remain open; the Codex engineering goal stays active.
