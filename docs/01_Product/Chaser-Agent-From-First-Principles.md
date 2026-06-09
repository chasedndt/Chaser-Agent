# Chaser agent From First Principles

Chaser agent starts with a human and a source. Everything else exists to make the source easier to review without pretending the output is automatically true.

## 1. Human operator

A person decides the goal, reviews outputs, and approves what becomes action or memory.

## 2. Source input

A source is a piece of text, document, repo note, research signal, or operator note. The first question is not “what can the agent do?” but “what does this source actually say?”

## 3. Context

Context is helpful background, but it can be wrong or stale. Chaser agent should separate source facts from context-driven inference.

## 4. Model/provider

A model may help transform text, but in V0 no live provider is required. Model output is an artifact to review, not truth.

## 5. Prompt/skill

A prompt is a task instruction. A skill is a reusable reviewed procedure. Skills must not grant tool or write authority by themselves.

## 6. Harness

A harness runs examples, checks outputs, and records results. Early harness tests are smoke/schema checks until Layer 0 behavior is tested.

## 7. Tool boundary

Tools can read, write, browse, call APIs, or run code. V0 avoids broad tool authority. Later tools must obey least authority and human review.

## 8. Output artifact

The artifact is a source card or review packet. It contains claims, evidence, uncertainty, actions, memory candidates, and review notes.

## 9. Review

Review asks: Is this grounded? Is it useful? Is it safe? Is it aligned with ChaseOS? What should not be promoted?

## 10. Memory candidate

A memory candidate is a suggestion that might become durable later. It is not memory yet.

## 11. Later promotion through ChaseOS

If something should become canonical truth, it routes through ChaseOS governance. Chaser agent does not silently promote it.

See also `docs/08_Learning/Harness-Engineering-Glossary.md` for terms such as source card, eval, JSONL, memory candidate, and writeback.
