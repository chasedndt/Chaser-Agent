# Chaser Agent Product Thesis

## Thesis

Chaser Agent is an open-source, standalone-first, local-first agent harness that turns goals and sources into evidence-linked work, learns from explicit human review, preserves governance-approved local memory, and curates a user-owned provenance map. It works independently and gains shared governance, orchestration, canonical state, policy, approvals, routing, and cross-project memory when optionally connected to ChaseOS.

## Why it exists

Agent output often collapses source facts, inference, action, memory, and confidence into fluent text. Chaser Agent makes those boundaries inspectable and durable. The product should show what came from the source, what was inferred, what remains uncertain, which memory influenced the result, what the human decided, and how durable state traces back to evidence.

## First product wedge

```text
safe source or bounded goal
-> evidence-linked source review
-> separate inference and uncertainty
-> action and memory candidates
-> immutable human review
-> governance-controlled local durable state
-> provenance-first knowledge map
```

## Standalone and ChaseOS modes

Standalone users own their local database, review records, memory, knowledge map, configuration, and eventual export/removal controls. The human operator is the authority.

ChaseOS integration remains additive through protocols and adapters. It may govern shared state and execution later; the standalone core does not import or imitate the ChaseOS control plane.

## Domain-neutral core

The default core must not contain website, media, trading, or other domain assumptions. Explicit workflow profiles provide specialisation without authority. This allows the same evidence, review, memory, and provenance contracts to support future domains safely.

## Determinism before providers

The transparent deterministic implementation remains the baseline, oracle, and fallback. Model-assisted intelligence may come later behind provider-neutral interfaces, only after data policy and reviewed eval evidence exist.

## Human review and memory

Human review is product behaviour, not an external afterthought. It records corrections and accepted/rejected candidates without mutating the original run. Local memory changes available context; it does not change model weights. Promotion requires governance and preserves provenance.

## Open-source boundary

The MIT core must remain self-hostable, modifiable, redistributable, and independent of proprietary products. Future hosted, enterprise, managed, premium, or ChaseOS-specific layers must remain separable.

## Honest status

- Layer 0: defined and being realigned to deployment-scoped governance.
- Deterministic source-card harness: implemented shape proof.
- Contract eval: partial seed, pending operator review.
- P0.1 standalone review/memory/knowledge architecture: approved on a review branch; implementation requires code/test proof.
- Provider, RAG, tool, browser, autonomous runtime, and training: not active.

## Why fine-tuning remains later

Training must wait for a stable workflow, reviewed corrections, privacy classification, repeated failure evidence, provider/model baselines, held-out tests, and an explicit training decision. Memory and retrieval should not be misrepresented as model training.
