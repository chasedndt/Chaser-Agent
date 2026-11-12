# Companion shell and architecture release — 27 September 2026

## Repo-truth delta and authority

Operator explicitly approved pushing, deploying and using the existing Cloudflare browser login. Normal Wrangler OAuth connected through that session with account/user read and Pages write scopes. No passwords or token values were placed in source, chat documentation or public artifacts. Earlier missing-CLI-auth notes are historical, not current blockers.

## Published website evidence

- ChaseOS Web main: `1a2d76f`; prior production/source base `fc729a7` verified before deployment. Deployment `e2d83c96.chaseos-web.pages.dev` succeeded. Canonical `/chaser-agent/architecture/index.html` returned 200 with separate same-origin JS and existing CSP; the browser exercised all 18 layer buttons on the canonical domain with no horizontal overflow at the tested desktop viewport.
- ChaseInTech main: `081f81f`; prior production/source base `00c4de1` verified. Deployment `31b0fcb6.chaseintech.pages.dev` succeeded. Canonical `/projects/chaser-agent/` returned 200 and contains the architecture link and port-8765 engineering boundary.
- Both complete production builds passed in the previous slice. No authentication, DNS, billing, database or provider configuration was changed by this documentation release. The website is explanatory; it does not host or start the operator's agent.

## Runtime changes

Added native HUD taskbar minimization, topmost toggle and a `hud --show-idle` client mode. Window minimization cancels queued/active voice work and discards drafts without dispatching executor controls. Stale draft results after minimization are treated as cancelled, allowing Talk to recover. The local API remains private on 127.0.0.1:8765.

Added a sourced research roadmap: ReAct-style observed action loops, Reflexion-style feedback-memory experiments, OSWorld/Windows Agent Arena outcome evaluation, AgentDojo injection tests, and A2A-inspired adapter contracts. Those are selected foundations and planned experiments, not reproduced benchmark results or completed integrations.

## Tests and verification limits

- Focused HUD/desktop/voice tests after window changes: 36 passed in 3.44s; an additional stale-draft regression was then added.
- Final focused rerun including the stale-draft regression: **37 passed in 3.29s**. The persistent local status HUD was launched as task-owned process 11304; its existence is not proof of connected executor or conversation.
- Launcher follow-up: the initial detached process 11304 exited. A foreground diagnostic launch with the dedicated speech environment reached `HUD waiting for a computer-use session`; wrapper PID 29092 and actual HUD PID 33068 were observed. The API health still reported ready/review-only, voice disabled and HUD executor not connected. Do not treat the earlier detached PID as live evidence.
- Engineering source pushed as preview commit `f458040` and [draft PR #1](https://github.com/chasedndt/Chaser-Agent/pull/1). Website release receipts were also pushed to main (`5cf4f24` ChaseOS Web; `46671d9` ChaseInTech). No private eval files or credentials were added.
- Actual native Tk check against the private runtime: minimized=iconic, restored=normal, topmost=0. No microphone or speaker activated during this check.
- Full suite before the additional regression: 329 passed, 1 skipped, 31 subtests passed, 1 failure in 52.36s. Failure is the pre-existing locked brand README manifest mismatch (1491 actual bytes, 1489 manifest); approved asset and manifest left unchanged. Git-normalized bytes and earlier versions also did not match, so this was not blindly rehashed or suppressed.
- Engineering should be pushed as an explicitly labelled preview branch/PR, not declared an all-green release. Human judgments, real executor acceptance, general conversational reasoning and live voice acceptance remain open.

Next safe action: versioned conversation/session contract and one narrow real harness adapter, then bounded computer-use and cancellation acceptance. Keep human quality ratings in the separate review workflow when the integrated interaction is ready.
