# Chaser agent Source Summary Spec

## Purpose

The source-summary system turns a source into a reviewable packet: what the source says, what evidence supports it, what remains uncertain, what conflicts, what action might follow, and what memory candidates may be worth reviewing.

## Input classes

- public article or documentation excerpt;
- uploaded report or PDF extract;
- operator note or research observation;
- code/repo note;
- runtime incident note;
- future website/page capture after manual review.

## Pipeline

```text
source input
→ source metadata
→ source card
→ claims table
→ evidence packet
→ uncertainty labels
→ contradiction scan
→ action candidates
→ memory candidates
→ roadmap impact suggestions
→ eval row/result log
→ human review
```

## Source card schema

A source card should include:

- `source_id`;
- `title`;
- `source_type`;
- `url_or_file`;
- `date_seen`;
- `privacy_class`;
- `summary`;
- `key_claims`;
- `evidence_snippets`;
- `uncertainties`;
- `contradictions`;
- `action_candidates`;
- `memory_candidates`;
- `review_required`.

## Claims table schema

| Field | Meaning |
|---|---|
| `claim_id` | Stable local ID. |
| `claim_text` | The claim in plain language. |
| `evidence_ref` | Snippet, line, URL, or file reference. |
| `confidence` | high / medium / low / unknown. |
| `claim_type` | source fact, inference, recommendation, risk, TODO. |
| `unsupported_reason` | Why evidence is insufficient, if applicable. |

## Evidence packet schema

Evidence packets preserve grounding:

- source reference;
- quoted snippet or line range;
- transformation note explaining how the claim was derived;
- privacy classification;
- reviewer notes.

## Uncertainty labels

Use:

- `source_says`: directly supported by source;
- `inferred`: reasonable inference but not direct quote;
- `operator_context`: depends on operator/project knowledge;
- `needs_source_review`: citation or source quality not verified;
- `conflicting`: conflicts with another source or repo truth;
- `unsafe_to_promote`: should not become memory/action without review.

## Contradiction scan

The contradiction scan asks:

- Does this conflict with existing repo docs?
- Does it conflict with ChaseOS governance boundaries?
- Does it overclaim implementation status?
- Does it imply automatic writeback or authority expansion?
- Does it contradict recent eval/test results?

## Action candidates

Action candidates must be scoped, reviewable, and noncanonical by default. Each action includes owner, target file/module, rationale, risk, and whether approval is required.

## Memory candidates

Memory candidates are suggestions only. They must include evidence, stability estimate, scope, privacy class, and proposed memory state. Chaser agent cannot auto-promote them into ChaseOS canonical memory.

## Roadmap impact suggestions

Roadmap impacts are review-only suggestions such as “convert this research signal to an eval” or “move adapter activation later.” They do not directly edit the roadmap without operator review.

## Example output

```json
{
  "source_id": "RS-001",
  "summary": "The source suggests memory systems need reviewable consolidation rather than silent mutation.",
  "key_claims": [
    {"claim_id": "C1", "claim_text": "Memory consolidation should separate candidate from promoted memory.", "confidence": "high", "claim_type": "recommendation"}
  ],
  "uncertainties": ["Exact implementation should be validated with evals."],
  "action_candidates": ["Add memory-state eval cases."],
  "memory_candidates": ["Chaser agent proposes memory candidates; ChaseOS governance decides promotion."],
  "review_required": true
}
```

## Failure modes

- hallucinated claims;
- missing evidence;
- flattening uncertainty into confidence;
- promoting memory automatically;
- confusing operator preference with verified truth;
- treating research intake as implementation;
- leaking private data into logs or datasets.

## Eval criteria

Score source summaries on:

- evidence preservation;
- unsupported-claim penalty;
- uncertainty quality;
- action usefulness;
- memory-candidate safety;
- brevity and operator usefulness;
- no-auto-promotion behavior.

## Never auto-promote

Never auto-promote canonical memory, ChaseOS docs, roadmap truth, skill edits, provider authority, runtime adapter activation, or public claims.
