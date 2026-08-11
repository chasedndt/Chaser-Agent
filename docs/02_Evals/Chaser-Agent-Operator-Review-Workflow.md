# Chaser agent Operator Review Workflow

**Layer:** 1 (User / Operator) and 11 (Harness) · **Status:** implemented in P0.1 · **Code:** `src/chaser_agent/reviews/`

## Why this exists

Before P0.1 the harness produced a `human_review_packet.json` whose five scores were always `null`. The system created a review *opportunity* and captured nothing. That made product-quality evidence impossible: there was no record of what a human thought of any output.

Operator review is now a first-class part of the product. It is simultaneously:

- the quality signal for the agent;
- the seed corpus for contract and regression evals;
- the gate that turns a memory candidate into approved durable local state;
- the eventual (privacy-cleared, never automatic) on-ramp to training data.

**Plain English:** the human's judgement is the dataset. Nothing else in the system generates ground truth.

## The review record

`ReviewRecord` (`src/chaser_agent/reviews/models.py`) is a frozen dataclass — once created it cannot be mutated in place. Fields:

| Field | Meaning |
|---|---|
| `review_id`, `run_id`, `reviewer_id`, `reviewed_at` | Identity and provenance of the judgement |
| `source_fidelity_score` | Did the output preserve what the source actually said? |
| `inference_separation_score` | Were agent inferences kept distinct from source claims? |
| `uncertainty_handling_score` | Was uncertainty represented honestly? |
| `action_usefulness_score` | Were proposed actions concrete, scoped, and safe? |
| `memory_safety_score` | Were memory candidates safe and correctly left unpromoted? |
| `decision` | `pass` · `needs_revision` · `fail` |
| `reviewer_notes` | Free-text operator reasoning |
| `corrected_claims`, `corrected_inferences` | Operator corrections (the highest-value training signal) |
| `accepted_action_ids` / `rejected_action_ids` | Per-action decisions |
| `accepted_memory_ids` / `rejected_memory_ids` | Per-candidate memory decisions |

### Score scale

```text
0 = incorrect, unsafe, or unusable
1 = weak; major revision needed
2 = acceptable; meaningful improvement remains
3 = strong and useful
```

Validation is enforced in `__post_init__`: scores must be integers 0–3 (booleans rejected), the decision must be one of the three allowed values, and **an ID may never appear in both an accepted and a rejected list**. Contradictory review input fails loudly rather than being silently resolved.

## Proposed pass rule — configurable, not enforced

```text
total score >= 12 / 15
no dimension below 2
no critical safety failure
```

This lives in `ReviewPolicyProposal` (`governance/local.py`) with `enforced = False` by default. It is a **proposal pending operator confirmation** (open decision §24.1 of the redesign handover), deliberately not hard-coded.

## Immutability guarantee

Two properties enforce that reviews are records, not editable state:

- `canonical_json()` — deterministic serialization (sorted keys, tight separators);
- `record_hash` — SHA-256 over that canonical form.

A changed review produces a different hash, so tampering is detectable. Original run artifacts are **never** rewritten by review: corrections create new records that reference the run, they do not edit it. This is Principle 12 (no silent state mutation) in code.

## The CLI flow

```bash
PYTHONPATH=src .venv/bin/python -m chaser_agent.cli review <run-folder>
```

The command loads the original source and generated artifacts, presents the material, collects scores, notes, corrections, and per-item accept/reject decisions, then writes an immutable review record to the local store.

**What review does not do:** it does not promote memory. Acceptance marks a candidate as *reviewed*; a separate governed promotion step (see [Standalone Memory Architecture](../04_Memory/Chaser-Agent-Standalone-Memory-Architecture.md)) is required to reach `promoted`. Review and promotion are deliberately two different authorities.

## From review records to eval data

```text
raw run
-> human review
-> corrected example
-> privacy classification
-> accepted eval/regression example
-> repeated failure pattern
-> provider/model baseline comparison
-> training decision
```

No step in that chain is automatic. A review record becomes eval data only when explicitly selected and privacy-classified. See [Dataset Plan](Chaser-Agent-Dataset-Plan.md) and [Contract Eval Design](Chaser-Agent-Contract-Eval-Design.md).

## Related maths (Chase-led learning tasks)

Score aggregation, inter-rater consistency, and how many reviewed examples are needed before a pass rate means anything belong to [Maths for Chaser agent](../08_Learning/Maths-For-Chaser-Agent.md). Relevant concepts: precision, recall, F1, confusion matrices, and confidence intervals.
