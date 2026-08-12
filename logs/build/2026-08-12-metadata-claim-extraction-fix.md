# 2026-08-12 — Metadata Claim Extraction Fix

## Trigger

Operator decision. The 2026-08-12 review-material pass surfaced that on a real research source, four of eight extracted claims were the document's own metadata header (`URL:`, `Title:`, `Published:`, `Authors:`) rather than anything the source asserted. The finding was left deliberately unfixed and unscored so the operator could judge it. Chase ruled: fix it.

## RED

New `tests/test_source_metadata_extraction.py` failed on import (`extract_source_metadata` did not exist), then on behaviour once stubbed.

## Two defects, not one

### 1. Metadata lines extracted as claims

`sentence_chunks()` already skipped Markdown headings, but a metadata line such as `- URL: https://…` survived list-prefix stripping and became a claim.

**Fix:** `extract_source_metadata()` plus an explicit `METADATA_LABELS` whitelist. Metadata is now *preserved* on the source card in a new `source_metadata` field rather than discarded, so provenance survives without masquerading as a claim.

The whitelist is deliberate. A general `Label: value` rule would also swallow `Decision: we will use the deterministic baseline` or `Risk: …` — exactly the statements a reviewer needs. Over-filtering loses source truth *silently*; under-filtering produces a visible, mildly noisy claim. The asymmetry favours a conservative list. `test_labelled_statements_that_are_real_claims_are_not_filtered` guards this directly.

Applying that principle to evidence found during verification: `status`, `type`, `category`, and `categories` were removed from the whitelist after a real run captured `Status: implemented, tests green, not committed` as metadata. In this repository's documents those labels carry substantive content.

### 2. Hard-wrapped sentences split into fragments (found by the new tests)

`sentence_chunks()` split line-by-line, so a wrapped paragraph produced mid-sentence claims. The source sentence "Operators must review pricing before enabling it." became two claims: `"Operators must review"` and `"pricing before enabling it."`

This is arguably the worse defect — a fragment claim no longer says what the source said, which is a direct source-fidelity failure — and it was invisible until the metadata tests exercised a realistically wrapped document.

**Fix:** lines are joined into paragraphs before sentence splitting. Blank lines, headings, metadata lines, and bare URLs flush the paragraph buffer; list items remain separate units because each bullet is its own statement.

## Verified against the source that exposed it

On `docs/research/2026-07-09-cloudflare-monetization-gateway-thesis.md`:

- before: 8 claims, 4 of them metadata;
- after: `source_metadata` = `{url, title, published, authors}`; all 8 claims are substantive content.

## Authority boundary

No provider calls, no adapters, no network, no training, no ChaseOS canonical mutation, no approval consumed, no merge to `main`.

## Verification

```bash
PYTHONPATH=src python -m pytest tests/test_source_metadata_extraction.py -q
PYTHONPATH=src .venv/bin/python -m pytest -q
```

## Note for review

The three runs generated on 2026-08-12 were produced by the *old* extractor. They should be regenerated before scoring, or scored with the knowledge that the metadata defect they exhibit is now fixed.
