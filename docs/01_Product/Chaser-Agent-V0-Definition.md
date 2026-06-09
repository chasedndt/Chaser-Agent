# Chaser agent V0 Definition

## What is the first useful version?

The first useful version of Chaser agent is a source-intelligence loop that turns a safe source into a structured review artifact and records enough evidence for an operator to decide what, if anything, should become an action, memory candidate, spec update, or eval case.

## Who is the operator?

The operator is the human reviewer/developer directing Chaser agent work. The operator decides whether outputs are useful, safe, aligned, and worth promoting. In this repo, the operator is not replaced by automation.

## What problem does V0 solve?

V0 solves the “messy source to reviewable artifact” problem. It prevents the agent from mixing source facts, inferences, actions, and memory suggestions into one ungrounded blob.

## One source-summary loop

```text
safe source input
→ intake metadata
→ source card
→ claims table
→ evidence snippets
→ uncertainty labels
→ contradiction notes
→ action candidates
→ memory candidates
→ human review packet
→ run log
```

## Files/folders part of V0

- `docs/01_Product/Chaser-Agent-Layer-0-Behaviour-Contract.md`
- `docs/01_Product/Chaser-Agent-V0-Definition.md`
- `docs/03_Summary_Intelligence/Chaser-Agent-Source-Summary-Spec.md`
- `docs/02_Evals/Chaser-Agent-Eval-Harness.md`
- `docs/02_Evals/Chaser-Agent-Dataset-Plan.md`
- `evals/datasets/golden/`
- `evals/rubrics/`
- `src/chaser_agent/summary/`
- `src/chaser_agent/evals/`
- `tests/`
- `logs/runs/`

## Not included in V0

- full 17-layer implementation;
- live external provider calls;
- Hermes/OpenClaw adapter activation;
- browser/computer-use authority;
- private dataset ingestion;
- automatic memory promotion;
- fine-tuning, PEFT, or LoRA;
- ChaseOS canonical doc mutation.

## Minimum proof that V0 exists

V0 exists when:

1. Layer 0 and V0 docs define expected behavior;
2. a source-card loop can run deterministically on safe inputs;
3. outputs separate source claims, inferences, uncertainty, actions, and memory candidates;
4. tests cover the contract shape;
5. JSONL/result logs record cases;
6. human review remains required for promotion.

## Manual human judgement required

Humans must judge:

- whether a source is trustworthy;
- whether the summary preserved evidence;
- whether inferred actions are useful;
- whether memory candidates are stable and safe;
- whether a failure should become a regression case;
- whether any output should affect ChaseOS truth, roadmap, skills, or public wording.
