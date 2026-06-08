# Chaser agent OpenClaw / Hermes Competitor Map

> Purpose: keep runtime and competitor lessons visible to Chaser agent without granting production authority.

## Boundary

This is a reference map for the standalone Chaser agent repo. It does not modify ChaseOS, does not grant adapter authority, and does not authorize high-privilege runtime behavior.

## Runtime comparison

| Runtime / signal | Useful lesson for Chaser agent | Implementable pattern | Required eval | Authority risk |
|---|---|---|---|---|
| Hermes Agent | Persistent skills, scheduling, subagents, gateway surfaces, and fallback behavior. | Skill registry, run logs, bounded adapter notes, scaffolded cron/runtime contracts. | Skill regression eval and runtime safety eval. | Privilege aggregation if memory + tools + messaging are combined without Gate boundaries. |
| OpenClaw | High-privilege runtime posture and Windows-side execution lessons. | Competitor safety checks, approval logging, backup-first config edits. | High-privilege adapter safety mini-eval. | Shell/writeback/credential escalation if treated as default execution. |
| OpenAI provider lane | Strong model/tool-use signal and structured output potential. | Provider adapter with schema-first outputs and no hidden calls. | Source-card eval, citation eval, tool-use eval. | Provider behavior mistaken for governance truth. |
| Local Ollama | Privacy-first backup runtime/provider option. | Local model adapter with capability and latency scores. | Local model quality and regression eval. | Underpowered output overtrusted without eval evidence. |
| MCP ecosystem | Standardized resources/tools/prompts interface. | MCP adapter contracts and tool/resource distinction. | MCP resource-vs-tool eval and prompt-injection eval. | Treating untrusted tool output as instruction. |
| SkillOpt / trainable skills | Skill files can be optimized like behavioral artifacts. | Skill edit candidates with before/after eval deltas. | Skill improvement regression suite. | Uncontrolled self-editing or supply-chain injection. |

## Product implication

Chaser agent should learn from all runtime lanes while staying eval-first: no runtime adapter is considered real until it has a bounded contract, a failure mode, a regression check, and an operator-reviewed authority boundary.
