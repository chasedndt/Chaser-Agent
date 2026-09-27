# 2026-09-27 — HTTP run integrity and early POST replies

## Repo-truth delta

The local API described source-card runs as immutable, but it served retained files without checking for post-creation changes. A full-suite pass also exposed an intermittent Windows client abort when a small POST body remained unread before an early `404` response. The existing E: runtime remains blocked by broad ACLs, so these are isolated loopback tests, not live operator acceptance.

## Changes

- New HTTP runs receive a private `.integrity.json` containing SHA-256 digests for the nine source/review artifacts after all files are written but before the run folder becomes routable. The run log records integrity version 1.
- Every authenticated run read verifies all nine digests. A mismatch, unsafe record or missing record required by a new run returns `409 run_integrity_failed`. Pre-manifest runs remain readable but are explicitly `unverified_legacy` in the index and `X-Run-Integrity` response header. No route mutates or promotes a run.
- Early-rejected POSTs now drain only a declared body up to 8 KiB before closing the connection; malformed or larger bodies are not drained without a bound. This covers route, Host, Origin and rate-limit rejection paths.
- Documentation no longer calls these HTTP files filesystem-immutable. An actor with same-user write access can modify both data and digests; the hash record is drift detection within the existing private-storage premise, not a signature or independent audit log.

## Verification

- `PYTHONPATH=src python -m pytest -q tests/test_local_http.py tests/test_local_desktop.py tests/test_hud.py` — **63 passed**.
- Repeated targeted network cases for early POST rejection, exact voice-cancel path and rate limiting — **5 passed**.
- `python -m compileall -q src/chaser_agent/local_http.py` — passed.
- `PYTHONPATH=src python -m pytest -q` — **323 passed, 1 skipped, 31 subtests passed, 1 failed** in 52.37s. The sole failure is the pre-existing locked canon-core manifest mismatch: approved `brand/chaser-agent/exports/canon-core/v1.0.0-rc.1/README.md` is 1491 bytes; its manifest says 1489. Neither file was edited.

## Boundaries and next action

No live server, provider, real executor, microphone, audio output, ACL/token change, ChaseOS canonical write, push or deployment occurred. Before live HTTP/HUD/voice acceptance, the operator must explicitly approve securing the current E: runtime ACLs and rotating its potentially exposed token. The full goal remains active.
