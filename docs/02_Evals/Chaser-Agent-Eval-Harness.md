# Chaser Agent Eval Harness

## Current classification

The existing tests and JSONL files are **smoke/schema checks** unless they explicitly test Layer 0 behavior.

They currently prove useful basics:

- the Python package imports;
- JSONL files parse;
- simple deterministic stubs return expected shapes;
- pytest can run locally.
- immutable review, memory lifecycle, retrieval, and provenance contracts behave as tested;
- the exact configured rows and assertions can be regenerated into `Chaser-Agent-Current-Test-Matrix.md`.

They do **not** yet prove product-quality Chaser Agent behavior.

## Eval levels

| Level | Meaning | Current status |
|---|---|---|
| Smoke test | Does the command/import/file parse? | Active. |
| Schema check | Does output have required fields? | Active/starter. |
| Contract eval | Does output obey Layer 0 behavior? | Active: deterministic runner + 30 cases / 154 assertions, all pending operator review. |
| Structural workflow eval | Did the agent navigate dependencies, evidence, authority, artifacts, proof and handoff? | Active V1: `workflow_episode.v1` plus deterministic trace scorer; first case pending operator review. |
| Product-quality eval | Does it help a human operator in realistic work? | Operator scoring begins with three representative runs and the first MarginFlip episode. |
| Outcome eval | Did an approved workflow achieve a verified result within risk/cost limits? | Later; no external execution authority in this phase. |
| Training eval | Can it guide model training/fine-tuning? | Not active. |

## Why JSONL is not proof by itself

JSONL is a data format. A JSONL row proves only that an example exists and can be parsed. It becomes eval evidence only when the expected behavior, scoring method, failure modes, and review criteria are defined.

The generated test matrix labels each row as an executable contract seed, executable workflow episode seed, connected generic smoke seed, connected metadata-eval seed, or generic smoke seed only. Rubric numbers are configured weights, not achieved scores.

## Layer 0 contract eval targets

Current executable contract seeds test whether Chaser Agent:

- separates source claims from inferences;
- labels uncertainty;
- refuses automatic memory promotion;
- treats actions as review candidates;
- avoids external API/tool use by default;
- preserves evidence snippets;
- records negative authority fields. Broader blocked-reason, trust, lifecycle, and adversarial coverage remains future work.

## Case-study workflow evals

`docs/02_Evals/Chaser-Agent-Case-Study-Workflow-Eval-System.md` defines the next rung: real operator workflows become source-linked episodes containing goals, context, dependencies, decision owners, capabilities, actions, expected artifacts, proof, forbidden outcomes, recovery cases and handoff requirements.

The first public-safe MarginFlip-derived episode is structurally executable but not golden. Its candidate trace can receive a deterministic structural score while provenance continues to state `pending_operator_review` and `training_eligible: false`.

## Current next step

1. Score the three representative source-review runs.
2. Correct the MarginFlip episode against the real workflow.
3. Convert operator corrections into regression cases.
4. Add metamorphic and adversarial variants before claiming product-quality coverage.
5. Keep provider, browser, tool, runtime authority, and training separately gated.
