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
| Contract eval | Does output obey Layer 0 behavior? | PARTIAL: deterministic runner + six pending-review seeds. |
| Product-quality eval | Does it help a human operator in realistic work? | Later, human-reviewed. |
| Training eval | Can it guide model training/fine-tuning? | Not active. |

## Why JSONL is not proof by itself

JSONL is a data format. A JSONL row proves only that an example exists and can be parsed. It becomes eval evidence only when the expected behavior, scoring method, failure modes, and review criteria are defined.

The generated test matrix labels each row as an executable contract seed, connected generic smoke seed, connected metadata-eval seed, or generic smoke seed only. Rubric numbers are configured weights, not achieved scores.

## Layer 0 contract eval targets

Current executable contract seeds test whether Chaser Agent:

- separates source claims from inferences;
- labels uncertainty;
- refuses automatic memory promotion;
- treats actions as review candidates;
- avoids external API/tool use by default;
- preserves evidence snippets;
- records negative authority fields. Broader blocked-reason, trust, lifecycle, and adversarial coverage remains future work.

## Current next step

Review the six contract seeds with the operator, then expand each family from one wiring case toward at least five reviewed cases. Add regression and metamorphic cases before claiming family coverage. Do not add provider, browser, tool, or runtime authority as part of that work.
