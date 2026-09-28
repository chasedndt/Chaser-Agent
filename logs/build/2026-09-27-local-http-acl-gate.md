# 2026-09-27 — local HTTP ACL gate

## Repo-truth delta

The isolated local API already bound to `127.0.0.1:8765` and required a bearer token. Its documentation warned that POSIX `0o600` creation flags did not guarantee private Windows ACLs. Read-only inspection of the existing `E:\Projects\Chaser Agent\Local Runtime\2026-09-27-http-foundation` showed inherited `AU` (Authenticated Users) and `BU` (Built-in Users) allow entries on the runtime directory. The token and generated artifacts must therefore be considered potentially exposed to other local accounts. This is local engineering state, not a live ChaseOS agent profile or merged release.

## Changes

- Added a read-only Windows SDDL/POSIX mode privacy check. HTTP startup refuses broad ACLs on the data directory, token file, run directory and optional voice directory before binding. It never repairs permissions silently.
- Kept the token check before reading token contents. Added regression tests for private and broad SDDL, malformed DACLs, token-creation refusal and server-start refusal.
- Drained small rejected non-JSON request bodies to avoid an intermittent Windows connection abort before the `415` response.
- Corrected the documented local runtime path and recorded the fail-closed state in the README and HTTP guide.

## Verification

- `PYTHONPATH=src python -m pytest -q tests/test_local_acl.py tests/test_local_http.py tests/test_local_voice.py` — **39 passed**.
- Direct `python -m chaser_agent.cli serve --data-dir 'E:\Projects\Chaser Agent\Local Runtime\2026-09-27-http-foundation' --port 8765` — exit **2**, `Runtime path has broad Windows ACL access; no permissions were changed`. No listener was opened by this attempt; no token was printed.
- `PYTHONPATH=src python -m pytest -q` — **260 passed, 1 skipped, 31 subtests passed, 1 failed** in 102.47s. The sole failure is the pre-existing locked canon-core asset-manifest mismatch: `brand/chaser-agent/exports/canon-core/v1.0.0-rc.1/README.md` is 1491 bytes, manifest says 1489. This pass did not edit that asset or manifest.

## Boundary and next gate

No ACL, token, canonical ChaseOS file, provider, model-selection decision, tool authority, merge, push or deployment was changed. The existing runtime will remain unavailable under the new gate until the operator explicitly authorizes a narrowly scoped ACL repair and token rotation. After that, rerun the real loopback smoke test and verify the listener, token handling and optional voice data. This gate does not protect against same-user malware or retroactively make a previously exposed token safe.
