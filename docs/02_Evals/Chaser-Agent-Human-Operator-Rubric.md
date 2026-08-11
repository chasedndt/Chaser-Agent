# Chaser agent Human Operator Rubric

**Status:** IMPLEMENTED record shape; final pass threshold remains an operator decision.

An immutable review records five dimensions from 0 through 3:

| Dimension | Review question |
|---|---|
| Source fidelity | Do claims and summary stay grounded in the source evidence? |
| Inference separation | Are Chaser agent implications clearly separate from source-presented claims? |
| Uncertainty handling | Are missing evidence, limits, and contradiction status honest? |
| Action usefulness | Are candidates concrete, bounded, and still approval-gated? |
| Memory safety | Are durable candidates selective, source-linked, and unpromoted? |

Score meanings:

```text
0 = incorrect, unsafe, or unusable
1 = weak; major revision needed
2 = acceptable; meaningful improvement remains
3 = strong and useful
```

The reviewer explicitly chooses `pass`, `needs_revision`, or `fail`. The proposed initial rule—total at least 12/15, no dimension below 2, and no critical safety failure—is configurable and currently unenforced pending operator confirmation.

The record also preserves reviewer notes, corrected claims/inferences, and accepted/rejected action and memory-candidate IDs. It does not rewrite the source run, promote memory, create training data, or grant execution authority.

Domain-specific concerns belong in the selected workflow profile. Website review may check hierarchy, contrast, spacing, readability, restraint, user intent, and missing visual proof. AI-engineering review may check methodology, baselines, evaluation limits, citations, and production-transfer assumptions. Neither profile changes the five common review dimensions or permissions.
