# Chaser agent Source Summary Spec

## Layer 0 inheritance

Source summary is the first V0 behavior implementation. It must obey `docs/01_Product/Chaser-Agent-Layer-0-Behaviour-Contract.md`.

All outputs are review-only until a human/operator decides otherwise. Memory candidates are review-only. Actions are review-only. Roadmap impact is a suggestion, not an automatic update. Nothing becomes canonical without ChaseOS governance.

## Purpose

Turn safe source input into a structured review artifact that separates source claims, Chaser agent inferences, uncertainty, actions, memory candidates, and non-promotion notes.

## V0 pipeline

```text
safe source input
→ source metadata
→ source card
→ claims table
→ evidence snippets
→ uncertainty labels
→ contradiction scan
→ action candidates
→ memory candidates
→ human review packet
→ run log
```

## Source card fields

- `source_id`
- `source_type`
- `title`
- `privacy_class`
- `source_says`
- `chaser_agent_infers`
- `uncertainties`
- `evidence_snippets`
- `contradictions`
- `action_candidates`
- `memory_candidates`
- `do_not_promote`
- `human_review_required`

## Review-only boundaries

- Action candidates do not automatically become tasks.
- Memory candidates do not automatically become memory.
- Roadmap impacts do not automatically update the roadmap.
- Source summaries do not become public claims.
- Generated text is not canonical truth.

## Failure modes to test later

- unsupported claims;
- missing uncertainty labels;
- auto-promoted memory;
- actions written as commands rather than candidates;
- private data leakage;
- treating a weak source as authoritative;
- confusing Chaser agent notes with ChaseOS governance.
