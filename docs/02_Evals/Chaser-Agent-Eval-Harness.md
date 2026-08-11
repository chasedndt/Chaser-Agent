# Chaser agent Eval Harness

## Current classification

The existing tests and JSONL files are **smoke/schema checks** unless they explicitly test Layer 0 behavior.

They currently prove useful basics:

- the Python package imports;
- JSONL files parse;
- simple deterministic stubs return expected shapes;
- pytest can run locally.

They do **not** yet prove product-quality Chaser agent behavior.

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

## Layer 0 contract eval targets

Future contract evals should test whether Chaser agent:

- separates source claims from inferences;
- labels uncertainty;
- refuses automatic memory promotion;
- treats actions as review candidates;
- avoids external API/tool use by default;
- preserves evidence snippets;
- records blocked promotion reasons.

## Current next step

Review the six contract seeds with the operator, then expand each family from one wiring case toward at least five reviewed cases. Add regression and metamorphic cases before claiming family coverage. Do not add provider, browser, tool, or runtime authority as part of that work.
