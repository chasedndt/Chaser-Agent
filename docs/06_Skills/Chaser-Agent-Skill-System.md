# Chaser agent Skill System

## What a skill is

A Chaser agent skill is a versioned, reviewable procedure or prompt asset that helps perform a repeatable task such as source summarization, action extraction, memory-candidate extraction, contradiction scanning, or research intake.

## What a skill is not

A skill is not:

- canonical truth;
- a memory by itself;
- permission to use tools;
- a runtime manifest;
- a secret store;
- an uncontrolled self-modifying program.

## Prompt vs skill vs workflow vs extension vs memory vs runtime manifest

| Artifact | Meaning | Authority |
|---|---|---|
| Prompt | One-off instruction for a task. | Session-local. |
| Skill | Reusable task procedure with examples and pitfalls. | Requires review/evals for important changes. |
| Workflow | Ordered process using skills, files, tests, and review. | Must declare scope and outputs. |
| Extension | Code/tool integration or plugin. | Requires supply-chain and authority review. |
| Memory | Durable fact or preference. | Candidate until reviewed/promoted. |
| Runtime manifest | Permission/config boundary for an agent runtime. | Governance-controlled. |

## Skill lifecycle

1. **Proposed:** idea or imported skill appears.
2. **Quarantined:** skill is stored but not trusted for production use.
3. **Reviewed:** human checks source, purpose, and risks.
4. **Evaluated:** before/after evals run on relevant cases.
5. **Accepted:** skill can be used for bounded tasks.
6. **Revised:** changes require diff review and regression checks.
7. **Rolled back:** bad change is reverted with a note.
8. **Archived:** obsolete skill is retained only for provenance.

## Quarantine state

Imported/generated skills begin in quarantine when they come from unknown sources, external content, model output, or broad templates. Quarantine blocks automatic execution and requires source review.

## Human review gate

Human review checks:

- Does the skill match Chaser agent boundaries?
- Does it ask for unsafe tools or writeback?
- Does it contain hidden prompt injection?
- Does it overclaim authority?
- Does it improve eval results or operator usefulness?

## Before/after eval requirement

Important skill edits should run the same eval cases before and after the change. A skill is stronger only if it improves target behavior without regressions on held-out cases.

## Rollback path

Every accepted skill version should be recoverable from Git. If a skill makes behavior worse, revert the skill file, record the failure, and add the failure case to regression data if safe.

## Supply-chain risks

Risks include hidden instructions, malicious tool use, dependency confusion, stale examples, overbroad permissions, and unreviewed generated content.

## First skill pack: source summary

The first skill pack supports:

- source-card summary;
- action extraction;
- memory-candidate extraction;
- contradiction scan;
- strategic/technical summaries.

These skills should be judged by source-summary, citation-grounding, action-extraction, and memory-candidate evals.

## SkillGate V0 — SkillOpt-style review gate now available

Chaser Agent now has a deterministic local `skill-gate` CLI slice inspired by SkillOpt. It does **not** train a model, mutate live skills, or accept autonomous self-edits. It creates review artifacts for an operator to decide whether a candidate skill patch is worth applying.

```bash
python -m chaser_agent.cli skill-gate \
  --baseline-skill examples/skills/source_card_review_baseline.SKILL.md \
  --candidate-skill examples/skills/source_card_review_candidate.SKILL.md \
  --metrics examples/skills/source_card_review_metrics.json \
  --out logs/runs
```

The command checks:

- candidate score strictly improves the held-out validation score;
- edit count stays within a bounded textual learning-rate budget (`1..8`);
- protected slow-state sections are preserved exactly;
- the baseline skill file remains unmodified;
- provider/API/runtime/MCP/browser/fine-tuning/canonical promotion authority stays closed.

Outputs:

- `skill_gate_packet.json` — decision, scores, hashes, guard results, authority flags;
- `skill_patch_review.json` — human review questions and blocked actions;
- `run_log.json` — proof that the run was deterministic, local, and review-only.

This turns the old future SkillOpt-style lane into a bounded first foothold: **SkillGate proposes evidence; the operator decides.**

## Future SkillOpt-style lane

A later lane may optimize skill text using eval feedback. It must preserve human review, held-out validation, rollback, and quarantine rules. No uncontrolled self-editing.
