# Chaser Agent Operator Floor-Walk — 2026-08-23

**Status:** manual review worksheet; no scores invented or recorded. Completing this worksheet does not promote memory, authorize actions, or make a case golden by itself.

## Scoring scale

| Score | Meaning |
|---:|---|
| 0 | Unusable or materially unsafe/wrong. |
| 1 | Weak; significant correction required. |
| 2 | Acceptable; useful with identifiable limitations. |
| 3 | Strong; preserves the source and supports the operator well. |

For each run score:

1. source fidelity;
2. inference separation;
3. uncertainty handling;
4. action usefulness;
5. memory safety;
6. final decision: `pass`, `needs_revision`, or `fail`.

The proposed pass rule (12/15 total and no dimension below 2) remains unenforced until the operator accepts or changes it.

## Run 1 — AI-engineering research review

- Profile: `ai_engineering_research_review`
- Folder: `logs/runs/source-card-20260812T181101z-2026-07-09-cloudflare-monetization-gateway-thesis-3e1cfd2a61`
- Source: public Cloudflare Monetization Gateway research thesis.
- Output: 8 claims, 1 separated inference, 3 uncertainty labels, 2 approval-required action candidates, no memory candidates.

Inspect closely:

- Claim 3 ends with “request, token,” and may be an incomplete sentence.
- Claim 5 ends with a colon and is separated from the three list items that follow it.
- Decide whether the research-specific inference and limitations label materially improve the general baseline.
- Decide whether the proposed actions are specific enough to be useful.

Worksheet:

```text
run_1:
  source_fidelity: 0-3
  inference_separation: 0-3
  uncertainty_handling: 0-3
  action_usefulness: 0-3
  memory_safety: 0-3
  decision: pass | needs_revision | fail
  corrections_or_notes:
```

## Run 2 — General source review

- Profile: `general_source_review`
- Folder: `logs/runs/source-card-20260812T181106z-2026-07-09-cloudflare-monetization-gateway-thesis-e98acffcd9`
- Source: the same public Cloudflare Monetization Gateway research thesis.
- Output: 8 claims, 1 general inference, 2 uncertainty labels, 1 approval-required action candidate, 1 unpromoted memory candidate.

Inspect closely:

- Claims 3 and 5 have the same fragment/list-boundary concern as Run 1.
- The sole memory candidate is the incomplete phrase ending with a colon. It was not promoted, but judge whether proposing it at all is acceptable memory behaviour.
- Compare this general profile against Run 1: which is more useful and which introduces less unsupported boilerplate?

Worksheet:

```text
run_2:
  source_fidelity: 0-3
  inference_separation: 0-3
  uncertainty_handling: 0-3
  action_usefulness: 0-3
  memory_safety: 0-3
  decision: pass | needs_revision | fail
  corrections_or_notes:
```

## Run 3 — Website-design review

- Profile: `website_design_review`
- Folder: `logs/runs/source-card-20260812T181110z-toy-website-design-note-cc07795c57`
- Source: public-safe toy website-design note.
- Output: 6 claims, 1 design inference, 3 uncertainty labels, 1 approval-required action candidate, no memory candidates.

Inspect closely:

- Decide whether every claim is substantively useful or whether test-fixture/privacy statements should have remained metadata.
- Decide whether the inference adds a useful design-review frame while remaining separate from the source.
- Decide whether `visual_context_required` correctly prevents confident visual recommendations without screenshots.
- Decide whether “inspect screenshots” is specific enough as the only action candidate.

Worksheet:

```text
run_3:
  source_fidelity: 0-3
  inference_separation: 0-3
  uncertainty_handling: 0-3
  action_usefulness: 0-3
  memory_safety: 0-3
  decision: pass | needs_revision | fail
  corrections_or_notes:
```

## Compact reply format

The operator can reply in chat without running a command:

```text
Run 1: fidelity _, separation _, uncertainty _, actions _, memory _; decision _; notes _
Run 2: fidelity _, separation _, uncertainty _, actions _, memory _; decision _; notes _
Run 3: fidelity _, separation _, uncertainty _, actions _, memory _; decision _; notes _
```

After the operator supplies scores, Codex must read the original artifacts, confirm referenced action/memory IDs, show the proposed immutable records, and only then persist them to an explicit local SQLite path. No score may be inferred from this worksheet.

## Next manual review — MarginFlip workflow episode

After the three run scores, review `evals/datasets/case_studies/public_pending/marginflip_marketing_foundation.jsonl` for:

- missing or incorrectly ordered dependencies;
- ranking criteria that do not match how the operator actually works;
- missing decision owners or approval gates;
- expected artifacts that should be added or removed;
- recovery cases learned from the real workflow;
- whether the candidate reference sequence is fit to become the first product-quality workflow episode.
