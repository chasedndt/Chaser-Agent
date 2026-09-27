# Approved private runtime activation — 27 September 2026

## Repo-truth delta

The earlier Windows ACL blocker is resolved. The operator explicitly approved Chaser Agent engineering and runtime repair in this task. This does not activate the canonical ChaseOS integration or supply human eval verdicts.

## Changes and live evidence

- Added the explicit, exact-path-scoped `scripts/repair_local_runtime.ps1`. It refuses reparse points, preserves content hashes, removes broad inherited grants, grants only current user/SYSTEM/Administrators, and optionally rotates the control token. Ordinary startup never invokes it.
- Invoked with the approved runtime path, `-RotateToken -Confirm:$false`: **45 existing paths checked; all existing file contents preserved before rotation**. No run, voice take or judgment deleted. The old bearer credential was invalidated; clients must restart. A private ACL/digest receipt is retained inside the runtime, not committed.
- `python -m chaser_agent.cli doctor --data-dir <runtime> --json`: **preflight_clear**, all three checked paths private, port available at check time.
- Started the actual CLI service on **127.0.0.1:8765**. PID observed at verification: **18440**. It is a task-owned process, not a Windows service/startup installation.
- `PYTHONPATH=src python scripts/probe_local_http.py --data-dir <runtime>`: **201 created**, **200 index**, **verified integrity**, exact source roundtrip, **401 missing token**, **403 untrusted origin**, **409 no executor**.
- Created one public/toy pending-review run: `source-card-http-20260927T215003727811Z-17a11c75f4aa`. This is engineering evidence, not an operator quality score.
- `python -m pytest -q tests/test_local_acl.py tests/test_local_http.py tests/test_local_desktop.py`: **49 passed in 21.66s**.

Runtime: `E:\Projects\Chaser Agent\Local Runtime\2026-09-27-http-foundation`. The control credential was never printed or published. ACL metadata backups do not make restoring broad permissions a recommended operation.

## Architecture and website source

- Added [Mermaid map](../../docs/01_Product/Runtime-Architecture.md) and a fully offline [18-layer explorer](../../docs/01_Product/Runtime-Architecture.html), including responsibilities, fundamentals, source references, status and next proof requirements.
- Clarified native HUD vs independent Agent Review Studio vs optional ChaseOS Studio.
- All 18 layer selections and search/empty-state behaviour passed browser DOM checks. Desktop and 390px mobile viewport checks reported no horizontal overflow; light scheme works. Desktop screenshot was inspected inline. Screenshot file saving to the central QA directory was refused by the browser tool's workspace-root restriction; no alternate destination was used to bypass it. This is not a complete assistive-technology audit.
- Isolated ChaseOS Web source: `E:\Projects\ChaseOS Web\2026-09-27-chaser-runtime-map`. Added public architecture explorer with separate JS compatible with existing script CSP, and a product-page engineering status section.
- Isolated ChaseInTech source: `E:\Projects\ChaseInTech\2026-09-27-chaser-runtime-map`. Added current engineering boundary and architecture link. Project publication audit passed: 14 projects, 28 published logs, 2 drafts. JavaScript syntax and all three repo diff whitespace checks passed.
- **NOT PUBLISHED:** Wrangler 4.95.0 could not list deployments because this session lacks configured `CLOUDFLARE_API_TOKEN`. No credential hunting, login, secret change, production deployment or DNS mutation occurred. Site source is prepared, not live. The architecture link must be released on ChaseOS.ai before the ChaseInTech link is published.
- Additional local website checks: ChaseOS Web `tsc -b` passed. ChaseInTech `npm run build` passed all project/media/build/link/search stages (138 HTML pages in the link audit, zero noncanonical internal links). These do not replace publication readback.
- ChaseOS Web full `npm run build` subsequently passed too, including production Clerk configuration/client gates, prerendering, CSP and route bundle budgets. Both website changes are locally build-verified, still unpublished.

## Untouched boundaries / remaining unknowns

Human eval judgments, canonical ChaseOS state, unrelated dirty worktrees, approved brand assets, provider configuration and existing review runs were not altered. No real executor is attached; the service reports `deterministic_review_only`. Voice is disabled in this live API process. Full conversational voice and microphone/speaker acceptance are still open. The previous full-suite brand manifest mismatch is not fixed or hidden by this focused run.

Next safe engineering work: implement a bounded read-only tool and real executor/HUD integration. Website publication needs configured deployment credentials and current-production reconciliation. Broad engineering permission is already granted; it need not be requested again.
