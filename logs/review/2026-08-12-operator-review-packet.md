# Operator Review Packet — 2026-08-12

**You are the dataset.** Every score below becomes a labelled row that contract
evals, regression cases, and any future training decision are built from. There
is no other source of ground truth in this system.

Nothing here is auto-scored. Nothing is promoted by reviewing. Recording a review
writes an immutable record and stops there; promotion is a separate governed step.

---

## What each artifact is

| File | What it is | What to check |
|---|---|---|
| `source_card.json` | The central review artifact | Statuses, metadata, claims vs inferences |
| `claims_table.json` | What the source *said* | Are these real assertions from the source? |
| `evidence_snippets.json` | Verbatim text backing each claim | Does the snippet actually support the claim? |
| `uncertainty_labels.json` | What remains unknown | Is the uncertainty honest, or performative? |
| `action_candidates.json` | Proposed next steps (never executed) | Concrete and scoped, or vague? |
| `memory_candidates.json` | Proposed durable memory | Would you actually want this remembered? |
| `human_review_packet.json` | The scoring scaffold | The five empty scores you are filling |
| `run_log.json` | Proof of what did NOT happen | All authority fields `none` / `False` |

---

## The five dimensions, and what a score means

Scale: **0** = incorrect/unsafe/unusable · **1** = weak, major revision · **2** = acceptable, improvement remains · **3** = strong and useful.

**`source_fidelity`** — Do the claims say what the source actually said? Fragments,
metadata masquerading as claims, or invented content all cost marks here. *(This is
the dimension that caught the metadata bug — it is now fixed, so score current behaviour.)*

**`inference_separation`** — Is agent inference clearly distinct from source claims?
Anything the agent concluded must sit in `chaser_agent_inferences`, never mixed into
`source_claims`.

**`uncertainty_handling`** — Are the uncertainty labels honest and specific, or
boilerplate? A thin source should produce more uncertainty, not less.

**`action_usefulness`** — Are the proposed actions concrete, scoped, and genuinely
worth doing? Vague suggestions score low even when they are safe.

**`memory_safety`** — Are memory candidates appropriate and correctly left
unpromoted? An empty memory list is often *correct* — not every source deserves a
durable memory.

**Decision:** `pass` · `needs_revision` · `fail`.

Proposed (not enforced) bar: total >= 12/15, no dimension below 2, no safety failure.

---

## How to read a run quickly

```bash
python -c "import json;c=json.load(open(r'RUN_FOLDER/source_card.json',encoding='utf-8'));print(json.dumps(c,indent=2)[:4000])"
```

Or open the folder and read `source_card.json` directly — it contains everything
except the raw run log.

---


## Run 1: `ai_engineering_research_review`

**Folder:** `logs/runs\source-card-20260812T181101z-2026-07-09-cloudflare-monetization-gateway-thesis-3e1cfd2a61`

**Source:** 2026 07 09 Cloudflare Monetization Gateway Thesis · privacy `public`

**Metadata captured separately (should NOT appear as claims):**

- `authors`: Rohin Lohe, Justin Ridgely, Will Papper
- `published`: 2026-07-01
- `title`: Announcing the Monetization Gateway: charge for any resource behind Cloudflare via x402
- `url`: https://blog.cloudflare.com/monetization-gateway/

**Claims (8):**

claim-001. [constraint] Status in Chaser Agent: research intake thesis / implementation-prep only
claim-002. [unknown] Cloudflare is positioning the Monetization Gateway as a way to charge for any Cloudflare-protected resource: web pages, datasets, APIs, and MCP tools.
claim-003. [unknown] The article frames the web's business model as shifting from human attention to agent/software usage, with payment units moving toward request, token,
claim-004. [unknown] For Chaser Agent, this is not just a payment article.
claim-005. [unknown] It is evidence that agent harnesses are becoming economic actors that need:
claim-006. [unknown] machine-readable access policy;
claim-007. [unknown] bounded payment/authorization gates;
claim-008. [unknown] auditable resource consumption;

**Agent inferences (must be separate from the above):**

- Reported research results may motivate an evaluation or architecture question, but they are not production truth.

**Uncertainty labels:**

- `requires_review` — Deterministic extraction does not establish that the source statements are correct; human review is required.
- `promotion_blocked` — Review artifacts and memory candidates are not approved durable memory until an explicit governed promotion.
- `research_limitations_not_verified` — Methodology, baselines, evaluation coverage, citations, and production transfer have not been independently verified.

**Action candidates:**

- `action-001` Review the methodology, baselines, evaluation limits, and implementation assumptions. (approval required: True)
- `action-002` Consider creating a bounded evaluation or RFC candidate after human review. (approval required: True)

**Memory candidates:** 0 — none proposed

**Record your review:**

```bash
PYTHONPATH=src python -m chaser_agent.cli review \
  logs/runs\source-card-20260812T181101z-2026-07-09-cloudflare-monetization-gateway-thesis-3e1cfd2a61 \
  --reviewer-id chase \
  --source-fidelity-score ? \
  --inference-separation-score ? \
  --uncertainty-handling-score ? \
  --action-usefulness-score ? \
  --memory-safety-score ? \
  --decision pass|needs_revision|fail \
  --reviewer-notes "what you noticed"
```

## Run 2: `general_source_review`

**Folder:** `logs/runs\source-card-20260812T181106z-2026-07-09-cloudflare-monetization-gateway-thesis-e98acffcd9`

**Source:** 2026 07 09 Cloudflare Monetization Gateway Thesis · privacy `public`

**Metadata captured separately (should NOT appear as claims):**

- `authors`: Rohin Lohe, Justin Ridgely, Will Papper
- `published`: 2026-07-01
- `title`: Announcing the Monetization Gateway: charge for any resource behind Cloudflare via x402
- `url`: https://blog.cloudflare.com/monetization-gateway/

**Claims (8):**

claim-001. [constraint] Status in Chaser Agent: research intake thesis / implementation-prep only
claim-002. [unknown] Cloudflare is positioning the Monetization Gateway as a way to charge for any Cloudflare-protected resource: web pages, datasets, APIs, and MCP tools.
claim-003. [unknown] The article frames the web's business model as shifting from human attention to agent/software usage, with payment units moving toward request, token,
claim-004. [unknown] For Chaser Agent, this is not just a payment article.
claim-005. [unknown] It is evidence that agent harnesses are becoming economic actors that need:
claim-006. [unknown] machine-readable access policy;
claim-007. [unknown] bounded payment/authorization gates;
claim-008. [unknown] auditable resource consumption;

**Agent inferences (must be separate from the above):**

- The extracted claims should be checked against their source evidence before they influence a decision.

**Uncertainty labels:**

- `requires_review` — Deterministic extraction does not establish that the source statements are correct; human review is required.
- `promotion_blocked` — Review artifacts and memory candidates are not approved durable memory until an explicit governed promotion.

**Action candidates:**

- `action-001` Review the extracted claims, evidence, inferences, and uncertainties. (approval required: True)

**Memory candidates:** 1
- It is evidence that agent harnesses are becoming economic actors that need:

**Record your review:**

```bash
PYTHONPATH=src python -m chaser_agent.cli review \
  logs/runs\source-card-20260812T181106z-2026-07-09-cloudflare-monetization-gateway-thesis-e98acffcd9 \
  --reviewer-id chase \
  --source-fidelity-score ? \
  --inference-separation-score ? \
  --uncertainty-handling-score ? \
  --action-usefulness-score ? \
  --memory-safety-score ? \
  --decision pass|needs_revision|fail \
  --reviewer-notes "what you noticed"
```

## Run 3: `website_design_review`

**Folder:** `logs/runs\source-card-20260812T181110z-toy-website-design-note-cc07795c57`

**Source:** Toy Website Design Note · privacy `public_toy`

**Metadata:** none in this source.

**Claims (6):**

claim-001. [unknown] The hero section text is white, so dark mode and contrast may matter for readability.
claim-002. [unknown] Important keywords need subtle emphasis rather than loud decoration.
claim-003. [unknown] Overdecorated styling can hurt readability and distract from the page intent.
claim-004. [recommendation] Current design best practice favours hierarchy, spacing, contrast, restraint, and user intent before visual effects.
claim-005. [unknown] This is safe toy content for deterministic Source Card Harness V0 testing.
claim-006. [unknown] It contains no private data, secrets, credentials, account information, or production claims.

**Agent inferences (must be separate from the above):**

- A website review should check hierarchy, contrast, spacing, readability, restraint, user intent, and the available visual evidence.

**Uncertainty labels:**

- `requires_review` — Deterministic extraction does not establish that the source statements are correct; human review is required.
- `promotion_blocked` — Review artifacts and memory candidates are not approved durable memory until an explicit governed promotion.
- `visual_context_required` — Hierarchy, contrast, spacing, readability, restraint, and user intent require screenshots or other visual proof for confident revi

**Action candidates:**

- `action-001` Inspect screenshots or other visual proof before recommending website-design changes. (approval required: True)

**Memory candidates:** 0 — none proposed

**Record your review:**

```bash
PYTHONPATH=src python -m chaser_agent.cli review \
  logs/runs\source-card-20260812T181110z-toy-website-design-note-cc07795c57 \
  --reviewer-id chase \
  --source-fidelity-score ? \
  --inference-separation-score ? \
  --uncertainty-handling-score ? \
  --action-usefulness-score ? \
  --memory-safety-score ? \
  --decision pass|needs_revision|fail \
  --reviewer-notes "what you noticed"
```

---

## What to send back to me

For each run, just tell me the five scores and your decision, plus anything you
noticed. Freeform is fine — for example:

```
run 1 (ai_engineering): fidelity 3, separation 3, uncertainty 2, actions 2, memory 3, pass
  - claims are real content now, but "It is evidence that..." is a fragment before a list
run 2 (general): ...
run 3 (website): ...
```

Once you have recorded them, I will compute and report back:

1. **Extraction precision** — what fraction of claims are substantive assertions
   rather than fragments, headers, or noise.
2. **Score distribution** across the five dimensions and where the harness is weakest.
3. **Which contract-eval families your findings map onto**, and any new case a
   finding justifies.
4. **Whether the coverage bar is met for product-quality rows** — three runs is a
   seed, not coverage, and I will say so plainly rather than over-claim.
5. **A recommendation on the live-provider decision**, since baseline quality is
   the thing a model would have to beat.

If a run is bad, score it low. A harness that only ever gets 3s is not being
reviewed, it is being rubber-stamped, and the dataset becomes worthless.
