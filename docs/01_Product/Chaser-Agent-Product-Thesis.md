# Chaser agent Product Thesis

**Chaser agent is a governed, eval-backed AI runtime and content-intelligence system derived from ChaseOS.**

Chaser agent is not a random chatbot. It is designed around source grounding, evidence packets, evals, human review, memory candidates, and bounded runtime authority.

Chaser agent is not a replacement for ChaseOS. ChaseOS remains the parent control plane, canonical governance owner, approval system, and durable truth layer.

Chaser agent is not a foundation model. It is a product/runtime repository that can route to providers or local models later, after eval evidence exists.

Chaser agent is not a broad autonomous operator yet. This scaffold begins with the first wedge: source summary + eval harness + memory candidates.

## First wedge
1. Normalize safe source input.
2. Build source cards.
3. Extract claims, uncertainty, actions, and memory candidates.
4. Score outputs with JSONL golden evals.
5. Route reviewed improvements to prompts, skills, harness code, or future datasets.
