# ChaserForge StrikeZone Workflow Runtime — Thread Scaffold

Links: [[HERMES]] · [[Hermes-Runtime-Profile]] · [[Agent-Activity-Index]]

Date: 2026-06-16  
Runtime lane: Hermes / Optimus  
Thread label: **ChaserForge StrikeZone Workflow Runtime**

## Purpose

Build the operational runtime around StrikeZone: how workflows, Discord/server channels, approvals, and automation connect so the system runs cleanly.

## Scope

This lane covers:

| Area | Included work |
|---|---|
| Workflow runtime layer | Map stages, packets, run state, validation, receipts, retry/resume, and handoff surfaces. |
| Automation scaffolding | Define allowed automation, blocked automation, launch/completion semantics, and fail-closed validation. |
| Discord/community operational flow | Describe review lanes, public/member lanes, status threads, approval phrases, and receipt expectations. |
| StrikeZone server workflow bridge | Connect evidence capture → review package → approval → mapped delivery. |
| Server/channel authority map | Maintain channel purposes, what can be posted where, and which steps require operator approval. |
| Approval gates | Separate review-only output, public-ready validation, and final public/member delivery authority. |
| Research → content → community handoff | Preserve evidence manifest, draft package, operator brief, Discord post drafts, and post receipts. |

## Explicit Non-Scope

This lane does **not** cover by default:

- Creating new trading strategies.
- Claiming signal performance.
- Posting to community/server channels without explicit approval.
- Monetization, role, billing, customer, subscription, or server-permission changes.
- Live trade execution or exchange/broker/wallet mutation.

## Operating Rules

1. **Review first, publish second.** StrikeZone outputs start in review/status lanes; public/member channel delivery requires explicit approval and validation-green/public-ready artifacts.
2. **Receipts are completion truth.** A workflow is not complete just because a launcher finished, drafts exist, or a review notification was sent. Public delivery completion requires target-channel send receipts with message IDs or equivalent durable proof.
3. **Evidence gates stay fail-closed.** Missing evidence, stale drafts, blocked source classes, or degraded screenshots keep the package review-only unless the operator explicitly approves a degraded output.
4. **Automation has bounded authority.** Automation may collect evidence, generate drafts, validate packages, post review summaries, and prepare approval-ready payloads. It must not bypass approvals or mutate roles/billing/server configuration.
5. **Channel mapping is authoritative when approved.** From StrikeZone ops context, operator shorthand like “post to the server channels” means use the established StrikeZone channel map after confirming the latest package is public-ready.

## Known StrikeZone Channel Map

Stable mapped Discord targets from the current StrikeZone workflow memory/skill state:

| Purpose | Target |
|---|---|
| Review / ops lane | `discord:1508901758955552808` (`#strikezone-ops-review`) |
| Market thesis desk | `discord:1508961074542547104` |
| BTC mapped channel | `discord:1271887026811179051` |
| ETH mapped channel | `discord:1382444686932971572` |
| SOL mapped channel | `discord:1508960599445471262` |
| Weekly recap | `discord:1382443965185527850` |

## Allowed vs Blocked Automation

| Automation type | Status | Notes |
|---|---|---|
| Evidence acquisition | Allowed, bounded | Must preserve artifacts and validation metadata. |
| Draft generation | Allowed | Review-only until gates pass. |
| Review-lane summary | Allowed | Should include run folder, source coverage, blockers, approval commands, and no-trade wording. |
| Public/member channel posting | Approval-gated | Requires explicit operator approval plus public-ready package/receipt capture. |
| Server role/billing/monetization changes | Blocked by default | Requires separate explicit approval and authority mapping. |
| Live trading/execution | Blocked | Not part of StrikeZone workflow runtime. |
| Performance claims | Blocked unless evidence-approved | Must not imply signal profitability or live execution performance. |

## Handoff Shape

Research → Content → Community should preserve these artifacts:

1. `evidence_manifest.json` and source-item files.
2. Validation report / reviewer gate status.
3. Operator brief / long-form market thesis draft.
4. BTC/ETH/SOL Discord drafts.
5. Chart/media attachment paths.
6. Review-lane notification with approval commands.
7. Public delivery receipt after approval, including target IDs and message IDs where available.

## Next Build Targets

- Confirm or refresh the server/channel authority map from live approved StrikeZone docs or operator-provided channel list.
- Create a reusable approval matrix: `review-only`, `public-ready`, `approved-to-post`, `posted-with-receipts`, `held/needs-changes`.
- Define one daily review-thread convention and fallback behavior when Hermes cannot create/rename Discord threads.
- Wire a run-state checklist that separates launcher acknowledgement, validation completion, review notification, approval consumption, and public delivery receipts.

## Graph Links

[[HERMES]] · [[Hermes-Runtime-Profile]] · [[Agent-Activity-Index]]
