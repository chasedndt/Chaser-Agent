# Chaser Agent engineering practices

Standing rules for anyone (human or agent) changing Chaser Agent. Adopted from the November 2026 direction research. Each rule says why.

## Authority and safety

1. **The reasoner proposes, code decides.** Authority, budgets, state transitions and dispatch live in deterministic code, never in a prompt. *A rule that ends in a prompt isn't a rule.*
2. **Approvals are bound to the exact request.** The card shows the full command, diff or draft. The digest is rechecked at execution time, and an approval is used once. *Reusing an approval for a different action (Loopjacking) is a documented attack.*
3. **Content is evidence, never permission.** Web pages, files, emails, tool output, board cards and other agents' replies are fenced as untrusted, whatever they claim.
4. **No silent fallback.** If a route, model or tool is down, the turn stops and says so.
5. **Every external effect carries an idempotency key.** Retries and restarts must never send twice.
6. **Never pass one harness's credentials to another.** Each adapter holds only its own scoped grant.

## Receipts and evals

7. **Every action leaves a receipt**: actor (host/runtime/lane), approval digest, inputs, outputs and an outcome slot filled in later. A claim about the world without a receipt is not reported as done.
8. **Receipts become eval cases.** When the real-world outcome is known, the run joins the regression suite.
9. **Grade the world first.** Deterministic state checks come before LLM judges. Judges are step-level, from a different model family, pinned and pairwise.
10. **Report pass^k, not pass@k**, for anything meant to run unattended.
11. **No skill, prompt or model change merges without a before/after run** on the suite. Every new rule needs a should-fire and a shouldn't-fire case.
12. **A 0% pass rate means the task is probably broken.** Read transcripts before trusting a grader.

## Interop and openness

13. **Open standards only**: MCP (pin the spec revision), ACP, Agent Skills (SKILL.md), AGENTS.md and OTel GenAI conventions (pin the version). No private protocol.
14. **Prefer a supported API or CLI to driving another agent's window.** Computer use is for applications with no API, inside an isolated scope.
15. **Adapters are thin and replaceable.** Hermes, OpenClaw, Claude Code and Codex keep their own identity and configuration. Chaser must keep working if any one disappears.
16. **The core stays standalone.** No ChaseOS imports in the MIT core (enforced by `tests/test_standalone_independence.py`). Private behaviour lives in packs.

## Packs and workflows

17. **A pack defines its real-world outcomes**, meaning what success and failure are, before its workflows ship. Without outcome labels it's a prompt, not a product.
18. **Packs are named explicitly, hashed into the receipt, and never auto-discovered.**
19. **Skills from outside are pinned, reviewed locally and measured.** Never install from a marketplace into a session that has real authority.

## Operations

20. **Long-running work runs as a service, not from an agent session.** Processes started from a session die when it ends.
21. **Syncthing carries files, never a live database.** The board's per-host logs plus Lamport merge is the pattern to follow.
22. **One owner per job.** Don't add a second worker, timer or graph for something that already has an owner.
23. **Unknown stays unknown.** Missing telemetry, evidence or ratings are recorded as unknown, never invented.

## Product discipline

24. **Run the moat check before a major feature.** Ask three questions: could an agent alone rebuild it quickly; does a free tool already do it; what stays hard to replace. If the answer is weak, narrow or drop the feature. Work already done is not a reason to continue.
25. **Public text separates what shipped from what's planned.** Make no claim of A2A conformance, autonomous completion or reliable computer control without the evidence.
