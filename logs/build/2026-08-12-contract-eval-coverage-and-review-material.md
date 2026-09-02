# 2026-08-12 — Contract Eval Coverage + Operator Review Material

## Trigger

Chase asked for a review pass over generated runs, then for the next build step. The stated blocker was a dataset question, not an engineering one: contract-eval coverage sat at one case per clause family against a target of five, and no real runs existed for operator review.

## Part 1 — review material generated

Three real runs produced from public-safe repository sources, deliberately covering profile isolation:

| Run | Profile | Source |
|---|---|---|
| `source-card-20260812T151124z-…-5836e682f6` | `ai_engineering_research_review` | Cloudflare monetization gateway thesis |
| `source-card-20260812T151432z-…-8cec8de888` | `general_source_review` | same source, for comparison |
| `source-card-20260812T151558z-toy-website-design-note-…` | `website_design_review` | toy website design note |

Profile isolation confirmed working on real input: the same source produced different inferences, different uncertainty labels (`research_limitations_not_verified` vs none vs `visual_context_required`), and different actions depending on profile. No design or media vocabulary leaked into the general profile.

**Finding for operator review — metadata lines are being extracted as claims.** On the Cloudflare thesis both profiles produced 8 claims, of which the first four are document metadata (`URL:`, `Title:`, `Published:`, `Authors:`) rather than substantive assertions. The redesign brief required heading-safe extraction; metadata header lines appear to be an uncovered variant of the same problem. Recorded here rather than silently fixed, because operator review is the mechanism that is supposed to catch exactly this, and Chase's score for `source_fidelity` on these runs is the honest signal.

Runs live under `logs/runs/` (git-ignored) and await Chase's scores via `chaser-agent review <run-folder>`.

## Part 2 — contract eval coverage completed

Added 24 cases so every clause family reaches five (30 total, 154 assertions, all passing).

New case shapes per family:

- **no_auto_promotion** — forged gate approval, urgency pressure, claimed standing approval, thin source.
- **injection_resistance** — role-play admin mode, injection inside a fenced code block, impersonated operator instruction, unicode-obfuscated injection (zero-width space plus RTL override).
- **claim_evidence_integrity** — multi-sentence linkage, verbatim evidence occurrence, privacy class retained on evidence, source location present.
- **uncertainty_honesty** — asserted absolute certainty, thin source, contradictory source, labels carry explanations.
- **action_boundary** — demanded file deletion and force push, demanded publication, demanded trade and fund transfer, demanded credential rotation.
- **authority_stamps** — browsing mentioned, training/LoRA mentioned, MCP and runtime dispatch mentioned, blocked actions recorded.

All are `origin: agent_authored_public_toy`, `review_status: pending_operator_review`. Coverage is a count, not operator-reviewed golden data.

## Mutation verification

A passing suite proves nothing unless it can fail. Injecting a regression into the builder (`review_status` `pending_review` → `reviewed`) caused **13 of 30 cases to fail** across four families; the cases that still passed were those that legitimately do not assert `review_status`. The builder was then restored and `git diff` confirmed clean.

Separately verified that `contract-eval` exits non-zero on failure by running it against a deliberately failing case (`EXIT_CODE=1`). An earlier `EXIT=0` reading was an escaping artifact of a nested `wsl.exe -- bash -c` invocation, not a product defect.

## Authority boundary

No provider calls, no live adapter, no network, no training, no ChaseOS canonical mutation, no approval consumed, no merge to `main`. Operator scores were **not** invented — the review records remain unwritten until Chase supplies them.

## Verification

```bash
PYTHONPATH=src .venv/bin/python -m chaser_agent.cli contract-eval \
  --input evals/datasets/contract/layer0_contract_seed.jsonl \
  --out logs/runs/contract-eval-results.jsonl
PYTHONPATH=src .venv/bin/python -m pytest -q
```

## Next

Operator review of the three runs. Those scores, plus the metadata-claims finding, become the first real product-quality rows and decide whether the extractor needs a heading/metadata fix before a provider is wired in.
