# 2026-09-27 — read-only local HTTP security doctor

## Repo-truth delta

The `serve` and `desktop` commands fail closed on broad runtime ACLs, but before this slice there was no dedicated read-only command that showed the operator all current path blockers and the intended port without attempting startup. The existing E: runtime remained blocked and no ACL or token authorization was supplied.

## Changes

- Added `doctor --data-dir <path> [--port 8765] [--json]`. It reports whether the runtime directory, control-token file and runs directory are missing, symlinked, the wrong type, private, broadly accessible or unverified. It briefly probes only `127.0.0.1:<port>` and closes the socket. Human-readable output is default; JSON is optional.
- The command does not create paths, read the bearer-token value, change an ACL/token, start a server or validate the token contents. `preflight_clear` means only that these read-only checks passed at that moment. Blocked/incomplete results exit nonzero.
- Added tests for missing paths, broad ACLs, occupied port, redacted human/JSON output and invalid ports.

## Verification

- `PYTHONPATH=src python -m pytest -q tests/test_local_doctor.py tests/test_local_acl.py tests/test_local_http.py` — **45 passed**.
- After final operator-output wording adjustment, `PYTHONPATH=src python -m pytest -q tests/test_local_doctor.py` — **7 passed**.
- Actual read-only `doctor --data-dir 'E:\Projects\Chaser Agent\Local Runtime\2026-09-27-http-foundation' --port 8765` — **blocked**: runtime directory, control-token file and runs directory each reported `broad ACL blocks startup`; port reported `available at this check`. The command reported no changed files/permissions and no token-value read. This is not a live service test.
- `PYTHONPATH=src python -m pytest -q` — **301 passed, 1 skipped, 31 subtests passed, 1 failed** in 37.01s. The sole failure is the pre-existing locked canon-core asset-manifest mismatch: approved `brand/chaser-agent/exports/canon-core/v1.0.0-rc.1/README.md` is 1491 bytes; the manifest says 1489. Neither file was edited in this slice.

## Boundaries and remaining work

No permission or token repair was attempted. The current runtime still cannot start; explicit operator approval is required for ACL repair and token rotation before live HTTP/HUD/voice verification. Provider choice, first authorized computer-use tool/executor and conversational voice acceptance remain open. The Codex engineering goal remains active.
