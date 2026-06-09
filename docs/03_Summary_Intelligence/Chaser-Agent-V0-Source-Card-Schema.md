
# Chaser agent V0 Source Card Schema

This document defines the concrete V0 source card shape. A source card is a review artifact, not canonical truth.

## Schema

```yaml
source_id: string
source_title: string
source_type: note|document|repo_doc|toy_jsonl|research_register|other_safe_text
source_origin: string
privacy_class: public|scrubbed|internal_safe|toy
trust_state: untrusted|operator_provided|reviewed_source|trusted_reference
source_summary: string
source_claims:
  - claim_id: string
    claim_text: string
    evidence_snippet_id: string
    source_location: string
    claim_type: fact|preference|instruction|constraint|status|unknown
    confidence: high|medium|low|requires_review
chaser_agent_inferences:
  - inference_id: string
    inference_text: string
    based_on_claim_ids: list[string]
    confidence: high|medium|low|requires_review
    uncertainty_label_ids: list[string]
uncertainty_labels:
  - uncertainty_id: string
    label: requires_review|missing_context|ambiguous_source|unsupported_inference|conflicting_source|privacy_risk|promotion_blocked|implementation_unknown
    explanation: string
    related_claim_ids: list[string]
contradiction_notes:
  - contradiction_id: string
    note: string
    related_claim_ids: list[string]
    severity: low|medium|high|requires_review
action_candidates:
  - action_id: string
    action_text: string
    source_claim_ids: list[string]
    rationale: string
    risk_level: low|medium|high|blocked
    requires_approval: boolean
    blocked_reason: string|null
memory_candidates:
  - memory_candidate_id: string
    candidate_text: string
    evidence_snippet_id: string
    scope: user|project|repo|workflow|unknown
    stability: stable|likely_stable|temporary|unknown
    privacy_class: public|scrubbed|internal_safe|toy
    promotion_status: candidate_only|blocked|rejected
    review_required: boolean
    rejection_reason: string|null
review_status: pending|reviewed|needs_revision|rejected
promotion_status: not_promoted|candidate_only|blocked|approved_elsewhere
created_at: ISO-8601 timestamp
run_id: string
```

## Field rules

- `source_claims` must describe what the source says.
- `chaser_agent_inferences` must not be mixed into source claims.
- `uncertainty_labels` must be present whenever source support is incomplete.
- `action_candidates` are review-only and must not be written as commands.
- `memory_candidates` are review-only and must never use `promoted` in V0.
- `promotion_status` must default to `not_promoted` or `candidate_only`.
- `review_status` must default to `pending` until a human reviews it.

## Toy example

```yaml
source_id: toy-website-design-001
source_title: Website redesign operator note
source_type: note
source_origin: operator_provided_toy_example
privacy_class: toy
trust_state: operator_provided
source_summary: >
  The source asks Chaser agent to review a website design without giving generic advice or overdecorating the styling.
source_claims:
  - claim_id: claim-001
    claim_text: The source wants website-design review to avoid generic design advice.
    evidence_snippet_id: evidence-001
    source_location: line 1
    claim_type: constraint
    confidence: high
  - claim_id: claim-002
    claim_text: The source prefers review that checks design intent, hierarchy, contrast, dark mode, subtle emphasis, current web best practices, and user constraints.
    evidence_snippet_id: evidence-002
    source_location: line 2
    claim_type: instruction
    confidence: high
chaser_agent_inferences:
  - inference_id: inference-001
    inference_text: A strong review packet should score whether design recommendations are specific to the source and constraints.
    based_on_claim_ids: [claim-001, claim-002]
    confidence: medium
    uncertainty_label_ids: [uncertainty-001]
uncertainty_labels:
  - uncertainty_id: uncertainty-001
    label: requires_review
    explanation: The source gives review criteria but no actual website screenshot or implementation.
    related_claim_ids: [claim-002]
contradiction_notes: []
action_candidates:
  - action_id: action-001
    action_text: In the next implementation pass, add a toy source-card case for website-design review quality.
    source_claim_ids: [claim-001, claim-002]
    rationale: The source provides a concrete weak-vs-strong distinction useful for review packets.
    risk_level: low
    requires_approval: true
    blocked_reason: null
memory_candidates:
  - memory_candidate_id: memory-001
    candidate_text: Chaser agent website-design review should distinguish generic advice from source-grounded critique of intent, hierarchy, contrast, dark mode, subtle emphasis, current best practices, and user constraints.
    evidence_snippet_id: evidence-002
    scope: workflow
    stability: likely_stable
    privacy_class: toy
    promotion_status: candidate_only
    review_required: true
    rejection_reason: null
review_status: pending
promotion_status: not_promoted
created_at: '2026-06-09T00:00:00Z'
run_id: toy-run-website-design-001
```

## Promotion warning

The toy example is safe, but it is still only a review artifact. It does not create a task, memory, roadmap change, or canonical ChaseOS truth by itself.
