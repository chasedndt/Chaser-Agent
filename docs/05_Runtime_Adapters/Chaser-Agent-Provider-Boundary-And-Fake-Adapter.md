# Chaser Agent Provider Boundary and Fake Adapter

**Layer:** 12 (Provider / Model Router) · **Status:** boundary implemented, fake adapter only — no live provider · **Code:** `src/chaser_agent/providers/`

## Why a fake provider comes before a real one

Adding a model to a governed harness is dangerous in the plumbing, not the prose. The risks are: what goes into the prompt (does private data leak out?), what comes back, how it is validated, what happens on timeout or malformed output, and — above all — whether model output can move fields it has no business touching.

All of that is designable and testable with a scripted fake, at zero cost, offline, with no credential in play.

The decisive reason is adversarial. This architecture rests on boundaries: memory cannot self-promote, actions always need approval, injected instructions must change nothing. To test those boundaries *against a model*, you need a model that reliably emits the worst possible output — forged approvals, injected instructions, fabricated certainty — every single run. A real provider will not cooperate: it is nondeterministic and mostly well-behaved, so boundary tests written against one pass by luck rather than by design.

**A fake adapter is a controllable adversary.** It makes those tests pass by construction.

Secondary benefits: the deterministic test suite stays deterministic, free, and offline; the deterministic-vs-model comparison rig can be built and validated before spending money (Principle 7 keeps the deterministic harness as the test oracle); and the abstraction is proven genuinely provider-neutral, because a fake has no vendor shape to accidentally encode.

**What a fake cannot tell you:** whether a model is any good at the task, real latency, real cost, or failure modes nobody thought to script. It de-risks the harness, not the intelligence. It is a prerequisite, not a substitute.

Each of those three limits has since been narrowed as far as it can be without a live call — see [Narrowing the limits](#narrowing-the-limits) below. What remains is only the irreducible residue: real numbers require a real provider.

## The three-part boundary

```text
build_request()  ->  adapter.complete()  ->  quarantine_response()  ->  apply_model_candidates()
   envelope             fake reply            untrusted outcome          labelled candidate
   (fail closed)        (no network)          (zero authority)           (governance frozen)
```

### 1. Envelope — the privacy dry run (`envelope.py`)

`build_request()` constructs exactly what would be sent and **refuses it immediately if unsafe**:

- **Privacy gate:** only `public_toy`, `public`, and `scrubbed` may go to a provider. Anything else raises `EnvelopeRefused` before a request object exists.
- **Secret scan:** OpenAI/GitHub/AWS/Slack key shapes, private-key blocks, bearer tokens, `api_key = …` assignments, and absolute Windows/Unix home paths all raise.
- **Purpose allowlist:** `claim_extraction`, `inference_drafting`, `uncertainty_labeling`, `contradiction_check`, `summary_drafting`. There is deliberately **no** purpose for executing an action, promoting memory, or approving work — those are governance decisions and are not model-shaped. Least authority applies to what you may even *ask*.

`describe_envelope()` answers "what would we have sent to a third party?" without sending anything. Request IDs and hashes are deterministic, so envelopes are comparable across runs.

### 2. Fake adapter (`fake.py`)

`FakeProviderAdapter` satisfies the `ProviderAdapter` protocol with `is_fake = True`, `network_access = False`. It is scriptable three ways: a single reply, a sequence, or a mapping keyed by purpose. It **records every request** for inspection and enforces the same pre-send gate a live adapter must, so unsafe envelopes fail during development.

`ScriptedReply` constructors cover the failure surface: `ok` · `timeout` · `malformed` · `truncated` · `refusal` · `error` · `hostile`.

`HOSTILE_PAYLOADS` is the named seed corpus — the adversarial dataset for this layer:

| Payload | What it attempts |
|---|---|
| `forged_promotion` | Sets `promotion_status: promoted`, claims canonical write |
| `forged_approval` | Claims approval consumed, `requires_approval: false` |
| `instruction_injection` | "Ignore your governance rules", developer mode |
| `authority_claim` | Impersonates the ChaseOS control plane, demands gate disable |
| `action_claimed_done` | Claims commits, posts, deployments, and trades happened |
| `fabricated_certainty` | Denies all uncertainty, declares review unnecessary |

The corpus is expected to grow as new failure shapes are imagined.

### 3. Quarantine (`quarantine.py`)

Model output is **untrusted input**. `quarantine_response()` classifies a reply and returns a `ProviderOutcome` whose `authority` block is all-`False` and whose `trust_state` is always `untrusted_model_output`.

- Any non-`ok` status is unusable, and `candidate_text` is emptied — a timeout can never read as a quiet success. This mirrors `attempted_unverified` in the visual completion evaluator: missing proof is never treated as proof.
- `detect_governance_claims()` pattern-matches attempts to assert authority; a reply that tries is recorded and refused usability, not silently dropped, so the operator can see what was attempted.

`apply_model_candidates()` merges usable text into artifacts under three guarantees:

1. Model text lands in a **separate** `model_inference_candidates` list — never in `chaser_agent_inferences`. Deterministic inference and untrusted model proposals cannot be confused.
2. Every candidate is stamped `origin: model_candidate`, `confidence: unverified`, `requires_human_verification: true`, `promotion_status: not_promoted`.
3. Governance fields are **fingerprinted before and after** the merge; any drift raises `GovernanceDrift` rather than persisting. The input artifacts are deep-copied, never mutated.

## Dependency rule

`ProviderAdapter` lives in `core/protocols.py`; concrete adapters live in `providers/`. The core depends on the protocol and receives an adapter by injection — it never imports one. `tests/test_standalone_independence.py` enforces this: `chaser_agent.providers` is on the forbidden-import list for every core package, and the provider package itself is scanned to ensure no SDK, HTTP client, or socket import ever appears.

## Test coverage

`tests/test_fake_provider_adapter.py` — 35 tests: envelope determinism, credential and privacy refusals, purpose allowlist, adapter determinism and request recording, every failure status proven unusable, and — parametrised across **every** hostile payload — proof that the governance fingerprint is unchanged, `review_status` stays `pending_review`, and `promotion_status` stays `not_promoted`.

## Narrowing the limits

### Limit 1 — failure modes nobody imagined

**The problem with the first design:** `detect_governance_claims()` is pattern-based. A blacklist is enumerable, and an enumerable defence is always incomplete — the attack you did not imagine walks through it.

**The patch: structural containment.** `MERGE_WRITABLE_KEYS` whitelists the only three keys any merge may create or change, anywhere in the artifact set: `model_inference_candidates`, `model_output_rejections`, `model_governance_claims_ignored`. `assert_only_whitelisted_changes()` performs a full recursive diff of the artifact tree before and after the merge and raises `GovernanceDrift` if a single change lands outside that whitelist — **including a field nobody has ever thought of**. Pattern detection is demoted to advisory labelling for the operator; containment no longer depends on it.

**Plus randomised fuzzing.** `test_random_hostile_output_never_moves_governance` assembles 400 seeded-random payloads from hostile fragments, forged JSON, unicode direction overrides, null bytes, format-string and traversal strings, and empty input, then asserts the invariant holds for every one. Example-based tests cover attacks somebody imagined; a property-based test asserts the property itself.

**Residue:** a novel attack could still produce *misleading candidate text* a human then believes. Containment stops it changing state; it cannot stop it being wrong. That is what human review is for.

### Limit 2 — cost, latency, and rate limits

**The patch: enforced ceilings, not estimates of trust.** `budget.py` adds a `BudgetPolicy` (prompt characters, output tokens, deadline, requests per run, projected cost) and a `BudgetLedger` that refuses a request *before it is sent* when a ceiling would break — verified by asserting `adapter.request_count == 0` after a refusal. `enforce_deadline()` converts a late reply into a `timeout` on the harness side, so a slow provider is never treated as a success just because bytes eventually arrived. Every call is recorded with estimated tokens, latency, and cost; the fake simulates latency and rate limiting so all of it is exercised now.

Token counts use a ~4-characters-per-token heuristic and are labelled `token_counts_are_estimates: true` everywhere they surface.

**Residue:** the real price, real speed, and real rate limits are unknown until a live call. But the ceiling machinery, the ledger, and the deadline enforcement already exist and are tested — the unknown is now a number to fill in, not a system to build.

### Limit 3 — unknown model quality

**The patch: calibrate the ruler before weighing the object.** `evals/comparison.py` scores a model-assisted run against its deterministic baseline: statement-level grounding against the source vocabulary, unsupported-statement counts, uncertainty preservation, governance-violation count, and a composite `quality_score`. Governance violations or unusable output force a score of zero — a hostile reply cannot score well by being eloquent.

The calibration is the point: `test_ruler_ranks_known_quality_outputs_in_the_correct_order` scripts three outputs whose quality is *known in advance* — well-grounded, partly grounded, wholly fabricated — and requires the ruler to rank them in that order. Calibrating a scale with known weights is not the same as weighing an unknown object, but an uncalibrated scale makes the later weighing meaningless.

**Residue:** whether a real model produces good analysis is genuinely unknowable until it is called. What is no longer unknown is whether we can *tell*.

### Graceful degradation

`assisted_review.py` builds the deterministic artifacts first and treats provider output as strictly additive. A refused envelope, a breached budget, a timeout, a refusal, or malformed output all leave the deterministic result standing, with `degraded: true` recorded. Degradation is structural, not error handling that might be forgotten.

## What is still out of scope

No live provider, no credential handling, no network path, no provider router or fallback logic, no model-assisted Layer 7 wiring, no cost/latency budgeting, no LLM-as-judge scoring, no training. Activating a real provider is authority expansion under Layer 0 and needs explicit operator approval.

## Recommended next step

The model-assisted path and the comparison rig now exist and are calibrated. The remaining work before a live provider is a **dataset** question, not an engineering one: assemble reviewed AI-engineering research examples so the comparison runs on cases whose correct answer an operator has judged, and reach the coverage bar in the [Contract Eval Design](../02_Evals/Chaser-Agent-Contract-Eval-Design.md).

Only then does activating a real provider become a cheap, well-instrumented experiment — with ceilings enforced, degradation graceful, containment structural, and a ruler already proven to rank quality correctly.
