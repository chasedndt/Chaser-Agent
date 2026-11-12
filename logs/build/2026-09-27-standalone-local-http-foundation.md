# 2026-09-27 — Standalone local HTTP foundation

## Repo-truth delta

Before this task, the deterministic Chaser Agent CLI and review artifacts existed, but no Chaser Agent HTTP listener was implemented. The separate `2026-09-09-computer-use-hud` worktree contains an unmerged in-memory HUD state/control prototype; the shared speech library contains operator-approved Pocket Alba production voice assets but no live Chaser Agent voice adapter. Neither is connected by this change.

## Changes in this isolated E: worktree

- Added `src/chaser_agent/local_http.py` and `chaser-agent serve`: fixed loopback bind, default port 8765, bearer token stored outside repo, exact Host/Origin checks, public/toy JSON input, request and rate bounds, read-only retrieval of immutable review artifacts and exact `original_source.md`.
- A source-card POST creates only pending-review artifacts. It does not call a provider, execute tools, control a browser, promote memory, mutate ChaseOS, or produce a human verdict.
- Added socket-level tests for successful round trip, source bytes, auth, origin, malformed/duplicate JSON, privacy class, traversal, size and rate bounds. Added the interface/threat-model document and current-status pointers in README and docs index.
- The original C: checkout, canonical vault, HUD worktree, shared speech library, eval judgments, and public deployments were untouched.

## Verification

- `PYTHONPATH=<worktree>/src python -m pytest tests/test_local_http.py -q` — 23 passed after the final Unicode/CRLF source-retention test strengthening.
- `PYTHONPATH=<worktree>/src python -m pytest -q` — 224 passed, 31 subtests passed, 1 unrelated failure: `test_manifest_assets_exist_and_match_hashes`, because `brand/chaser-agent/exports/canon-core/v1.0.0-rc.1/README.md` is 1491 bytes while its locked manifest says 1489. This mismatch preceded the HTTP edit; do not rewrite the canon source set in this task.
- Live foreground service at `127.0.0.1:8765`: health reported `deterministic_review_only`, `hud=not_connected`, `voice=not_connected`; authenticated public-toy POST created a pending run; authenticated retrieval returned the exact Unicode/CRLF source. The task-created listener was stopped; the port was no longer listening.

## Security status and remaining unknowns

The implemented controls and non-goals are in `docs/05_Runtime_Adapters/Chaser-Agent-Local-HTTP.md`. This is pre-alpha local-only plumbing, not production-hardening proof. Windows ACL secrecy, local same-user compromise, public/LAN serving, DoS resistance, retention/deletion and independent security review remain open.

Next: rerun the final targeted tests, then connect the existing HUD reducer only through a separately verified authenticated status/event transport. Do not expose control buttons as live authority until an executor acknowledgement path and stop semantics are tested. Pocket Alba voice requires a separate local adapter and listening QA; no microphone, provider or model download has been activated.
