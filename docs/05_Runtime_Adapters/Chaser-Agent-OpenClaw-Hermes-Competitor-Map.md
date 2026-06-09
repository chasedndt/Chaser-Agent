# Chaser agent OpenClaw / Hermes / Competitor Map

This map turns runtime and competitor lessons into Chaser agent design constraints. It is not adapter activation authority.

## Hermes lessons

Copy:

- persistent skills and scheduled workflows can make agents operationally useful;
- subagents and tool isolation help contain context and execution;
- gateway surfaces need explicit channel/control-plane rules;
- memory/skill mutation must be bounded and auditable.

Avoid:

- broad privilege aggregation;
- silent skill drift;
- assuming a messaging surface is trusted input;
- treating runtime memory as canonical truth.

Required evals before adapter use: provider failure handling, writeback denial, prompt-injection rejection, and audit-log completeness.

## OpenClaw lessons

Copy:

- local runtime integration can be powerful when it has explicit config, gateway, and plugin boundaries;
- runtime repair needs backup-first config edits and verification;
- security findings should be separated from outage repair.

Avoid:

- credential concentration;
- small-model tool/web exposure without limits;
- unpinned plugin supply chain;
- treating Windows/WSL path drift as harmless.

Required evals: forbidden tool tests, credential redaction checks, plugin provenance checks, and channel authority checks.

## OpenAI / Codex lessons

Copy:

- code agents need precise repo scopes, tests, and branch/PR discipline;
- eval harnesses should record pass/fail reasons, not just success text;
- model/tool capability should be measured by tasks.

Avoid:

- letting a coding agent infer repo authority;
- mixing doc/spec passes with broad code rewrites;
- pushing without operator approval.

Required evals: repo-boundary compliance, test-before/after logs, and no-unrequested-code-change checks.

## Local Ollama lessons

Copy:

- local models are useful for privacy and fallback;
- capability tiers must be explicit;
- small models need stricter tool limits.

Avoid:

- assuming local equals safe;
- giving weak models high-authority tools;
- hiding fallback degradation.

Required evals: fallback quality, refusal/uncertainty handling, and tool-denial behavior.

## MCP lessons

Copy:

- separate resources, tools, and prompts;
- validate schemas;
- prefer read-only resources before write tools;
- record least-authority decisions.

Avoid:

- tool overreach;
- schema drift;
- treating MCP availability as permission to act.

Required evals: resource-vs-tool classification, forbidden write denial, schema validation, and malicious-resource prompt injection.

## SkillOpt / trainable skill-file lessons

Copy:

- skills can be treated as evaluated artifacts;
- before/after measurements can improve prompt assets;
- held-out validation matters.

Avoid:

- uncontrolled self-editing;
- optimizing skills against only easy examples;
- bypassing human review.

Required evals: skill regression, held-out examples, rollback verification.

## Runtime safety lessons

- External messages and web content are untrusted.
- Provider/API failures must be visible.
- Audit logs must distinguish read, draft, proposal, and write.
- No adapter becomes real until it passes no-op/mock evals and operator approval.

## Remote GUI / private networking lesson

Remote GUI, Tailscale, localhost bridges, and private gateways are operational surfaces, not automatic authority grants. Chaser agent should document readiness and risk before it interacts with any such surface.

## What Chaser agent should copy

- eval-first behavior;
- explicit authority ceilings;
- run logs;
- skill provenance;
- fallback transparency;
- human review gates.

## What Chaser agent should avoid

- production claims without tests;
- connector activation before safety evals;
- automatic canonical memory;
- hidden credentials;
- broad autonomy from a scaffold repo.
