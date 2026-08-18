# Chaser Agent Layer 0 Behaviour Contract / Product Constitution

## Why Layer 0 exists

Layer 0 defines what Chaser Agent is allowed to mean before any architecture, provider, tool, memory store, workflow profile, skill, or runtime claims capability. Every later layer and deployment mode must obey it.

Without this contract, the project can confuse generated output with truth, candidates with actions or memory, passing syntax checks with product quality, workflow specialisation with authority, or an integration packet with live dispatch.

## Product identity

Chaser Agent is an open-source, standalone-first, local-first agent harness for turning goals and sources into evidence-linked, reviewable work. It can run independently and integrate optionally with ChaseOS.

The core must remain usable without ChaseOS. ChaseOS remains the optional integrated control plane for shared governance, cross-runtime orchestration, shared canonical state, policy, approvals, routing, and cross-project memory.

## Deployment-scoped authority

### Standalone deployment

- The human operator is the approval authority.
- Local governance validates review, promotion, and allowed transitions.
- Human-approved durable local state may be persisted.
- Local state remains user-owned and exportable/removable under policies still requiring operator definition.
- No output approves or promotes itself.

### ChaseOS-integrated deployment

- The same core interfaces remain in use.
- An optional adapter may produce ChaseOS-shaped proposals.
- ChaseOS may govern shared canonical state, policy, permissions, approvals, routing, and orchestration.
- P0.1 does not consume a ChaseOS approval or dispatch live work.

In both deployments:

```text
generated output != approved truth
memory candidate != memory
action candidate != action
review packet != approval
integration packet != dispatch
agent confidence != authority
```

## Expected P0.1 behaviour

For a bounded source-review run, Chaser Agent should:

1. accept only declared safe/reviewable input;
2. record source identity, origin, trust, privacy, and selected workflow profile;
3. preserve headings separately from factual claim candidates;
4. create evidence-linked source claims;
5. keep source claims separate from Chaser Agent inference;
6. label uncertainty and contradiction status honestly;
7. retrieve only eligible reviewed/promoted memory and identify any memory influence;
8. propose scoped action candidates without execution;
9. propose memory candidates without promotion;
10. persist an immutable human-review record separately from original run artifacts;
11. allow only a governance backend to perform a valid local memory transition;
12. retain provenance from durable memory back to source, evidence, run, and review.

## Core and profile boundary

The default core is domain-neutral. Domain-specific behaviour belongs in an explicit `WorkflowProfile`.

A profile may guide claim hints, add labelled domain inference, add uncertainty rules, and propose review actions or memory candidates. It may not call a provider, grant a tool, execute an action, modify governance, bypass review, promote memory, or increase authority.

## Input boundaries

Allowed P0.1 inputs:

- public or public-toy text;
- explicitly scrubbed text;
- explicitly classified local notes;
- repo docs/tests and public-safe JSONL fixtures;
- reviewed research-register entries without secrets/private raw data.

Blocked by default:

- credentials, tokens, cookies, private keys, secrets;
- unclassified raw private datasets or personal logs;
- live provider, browser, MCP, tool, account, payment, or trading state;
- any input whose required data class is unresolved and unsafe to infer.

The final definitions of `public`, `scrubbed`, `internal_safe`, `private`, and `secret` remain operator decisions. Labels do not grant authority.

## Output boundaries

Allowed:

- source cards, claims, evidence, uncertainty, contradiction status;
- action and memory candidates;
- immutable review records and corrections;
- governance audit records;
- local memory records following valid transitions;
- knowledge-map nodes/edges;
- eval/test-matrix results, run logs, and handovers.

Blocked:

- self-approved truth or memory;
- mutation of original run artifacts during review;
- public claims/actions without explicit later authority;
- providers, MCP/tools, browsers, hosted services, payments, trades, deployments, credential operations, or model training;
- ChaseOS canonical mutation from the standalone core.

## Human review

Human review is part of the product, eval system, and memory lifecycle. It records scores, decision, notes, corrections, and accepted/rejected candidate identifiers. A review record is immutable and does not itself promote memory.

The proposed initial pass rule—12/15, no score below 2, and no critical safety failure—is configurable and pending operator confirmation.

## Local memory promotion

Standalone promotion means a candidate was reviewed, accepted by the operator, validated by local governance, and persisted as approved durable local state with provenance. It does not mean the content is globally or objectively true.

Only a `GovernanceBackend` may approve a transition. Rejected candidates cannot promote. Stale and disputed records remain visible. Supersession creates a link rather than overwriting history.

## Least authority

Provider, adapter, profile, skill, model, confidence, or data availability never implies permission. Authority must be explicit, scoped, revocable, logged, and reviewable.

P0.1 may propose inspection, comparison, evidence requests, eval candidates, documentation candidates, bounded task candidates, and memory candidates. It may not execute external side effects.

## Deterministic and eval boundaries

The deterministic harness remains a reference implementation, fallback, and test oracle. JSONL validity, imports, and smoke tests are not product proof. Contract seeds remain unreviewed until the operator accepts their labels and expected behaviour.

## Public claims allowed now

The repository may describe Chaser Agent as an open-source, standalone-first, local-first, human-governed agent-harness architecture with deterministic P0 foundations and P0.1 standalone work on a review branch.

It may not claim production autonomy, semantic intelligence, private-data safety, live providers/tools/browser execution, finished canonical memory, fine-tuned behaviour, or all-layer completion.

## Open decisions

The exact data classes, review threshold, public memory terminology, first official domain pack, profile discovery mechanism, later provider/RAG/tool/sandbox choices, standalone/ChaseOS synchronisation and conflict policy, export/deletion semantics, and retention policy remain in `Chaser-Agent-P0.1-Open-Decisions.md`.
