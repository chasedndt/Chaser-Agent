# 2026-08-11 — Provider-Neutral Fake Adapter and Inference Boundary

## Trigger

First part of the §26 recommended next pass, approved by Chase after discussing why a fake provider precedes a real one. Scope held to the boundary itself; the AI-engineering research workflow and the first product-quality eval set are deliberately not in this pass.

## Rationale

The risk in adding a model is the plumbing, not the prose: prompt contents, response validation, failure handling, and whether model output can move governance fields. All of it is testable with a scripted fake at zero cost and offline.

The decisive reason is adversarial. Boundary tests need a model that emits forged approvals and injected instructions *reliably, every run*. A real provider is nondeterministic and mostly well-behaved, so such tests would pass by luck. A fake is a controllable adversary, so they pass by design.

## Implemented

New package `src/chaser_agent/providers/` (no SDK, no network, no credential):

- `models.py` — `ProviderRequest` (deterministic id/hash), `ProviderResponse`, `ProviderOutcome` with an all-false `authority` block. `ALLOWED_PURPOSES` deliberately excludes any authority-shaped purpose; `SENDABLE_PRIVACY_CLASSES` limits what may leave the machine.
- `envelope.py` — `build_request()` fails closed on disallowed privacy class or sensitive material; `scan_for_sensitive_material()` covers OpenAI/GitHub/AWS/Slack key shapes, private-key blocks, bearer tokens, credential assignments, and absolute home paths; `describe_envelope()` is the privacy dry run.
- `fake.py` — `FakeProviderAdapter` (scriptable by single reply, sequence, or purpose map; records every request; enforces the pre-send gate) and `ScriptedReply` constructors for ok/timeout/malformed/truncated/refusal/error/hostile. `HOSTILE_PAYLOADS` seeds the adversarial corpus with six named attacks.
- `quarantine.py` — `quarantine_response()` classifies replies as `untrusted_model_output` with zero authority and empties `candidate_text` on any non-ok status; `detect_governance_claims()` flags authority assertions; `apply_model_candidates()` merges usable text into a **separate** `model_inference_candidates` list, deep-copying input and raising `GovernanceDrift` if the governance fingerprint moves.

`ProviderAdapter` protocol added to `core/protocols.py` so the core depends on the interface and receives adapters by injection.

## Tests

`tests/test_fake_provider_adapter.py` — 35 tests. Parametrised across every hostile payload: each is detected, refused authority, and proven unable to change the governance fingerprint, `review_status`, or `promotion_status`. Every non-ok status is proven unusable so a timeout can never read as quiet success.

`tests/test_standalone_independence.py` extended: `chaser_agent.providers` added to the forbidden-import list for core packages, plus a scan proving the provider package imports no SDK, HTTP client, or socket, and a protocol-conformance check.

## Authority boundary

No live provider, no credential, no network call, no provider router, no model-assisted Layer 7 wiring, no training, no ChaseOS canonical mutation, no merge to `main`.

## Verification

```bash
PYTHONPATH=src .venv/bin/python -m pytest -q
```

## Next

Wire a model-assisted path through `general_source_review` using the fake, then build the deterministic-vs-model comparison harness on reviewed AI-engineering examples before any live provider is considered.
