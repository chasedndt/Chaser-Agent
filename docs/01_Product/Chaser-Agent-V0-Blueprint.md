
# Chaser agent V0 Blueprint

## 1. V0 purpose

Chaser agent V0 is the first implementation-ready loop after the Layer 0 Ground-Up Reset. It turns **safe, reviewable source input** into a structured review artifact that separates:

- what the source says;
- what Chaser agent infers;
- what remains uncertain;
- what actions may follow;
- what memory candidates may be proposed;
- what should not be promoted automatically.

V0 exists to make source intelligence reviewable before deeper evals, provider calls, runtime adapters, tool-use, or training are attempted.

## 2. V0 operator

The V0 operator is the human reviewer/developer directing Chaser agent work. The operator decides whether the artifact is useful, safe, aligned, and worth promoting into any future action, memory, dataset row, roadmap change, spec change, or ChaseOS-governed truth.

V0 never replaces the operator. V0 creates evidence for operator review.

## 3. V0 command/interface target

The implementation target for Phase 1 is a deterministic local command or Python entry point that can run without external providers:

```bash
python -m chaser_agent.cli source-card --input path/to/source.txt --out logs/runs/<run_id>/
```

Minimum acceptable interface shape:

```text
safe source input
→ intake metadata
→ source card JSON/Markdown
→ human review packet
→ run log
```

The exact CLI name may change in Phase 1, but the interface must remain local, deterministic, review-only, and provider-free.

## 4. V0 input contract

Allowed V0 inputs:

- public or scrubbed text;
- operator-provided notes explicitly marked safe for repo-local review;
- toy JSONL rows already committed under `evals/datasets/golden/`;
- repo docs and tests;
- reviewed research-register entries that contain no secrets or raw private data.

Each input must include or derive:

| Field | Meaning |
|---|---|
| `source_id` | Stable local identifier for the input. |
| `source_title` | Human-readable title. |
| `source_type` | `note`, `document`, `repo_doc`, `toy_jsonl`, `research_register`, or `other_safe_text`. |
| `source_origin` | Where the source came from, without leaking secrets. |
| `privacy_class` | `public`, `scrubbed`, `internal_safe`, or `toy`. |
| `operator_intent` | Why the operator asked Chaser agent to review it. |
| `raw_text` | The safe source text. |

Blocked by default:

- secrets, credentials, cookies, tokens, private datasets, raw personal logs, account data, private trading/wallet data;
- live browser content;
- web/API/provider output fetched during the run;
- Hermes/OpenClaw runtime state;
- MCP resources/tools;
- ChaseOS canonical docs as a mutation target.

## 5. V0 output contract

V0 outputs are review artifacts only. The output set should be:

| Artifact | Target |
|---|---|
| Source card | `logs/runs/<run_id>/source_card.json` and/or `.md` |
| Human review packet | `logs/runs/<run_id>/human_review_packet.md` |
| Run log | `logs/runs/<run_id>/run_log.json` or `.md` |
| Optional copied safe source metadata | `logs/runs/<run_id>/source_metadata.json` |

Every output must preserve these boundaries:

- action candidates are not tasks;
- memory candidates are not memory;
- roadmap impact is not a roadmap update;
- source summaries are not public claims;
- generated output is not canonical truth;
- ChaseOS governance owns canonical promotion.

## 6. V0 source-card schema

The source card is the central V0 artifact. It should follow `docs/03_Summary_Intelligence/Chaser-Agent-V0-Source-Card-Schema.md` and include:

```yaml
source_id: string
source_title: string
source_type: string
source_origin: string
privacy_class: public|scrubbed|internal_safe|toy
trust_state: untrusted|operator_provided|reviewed_source|trusted_reference
source_summary: string
source_claims: list[claim]
chaser_agent_inferences: list[inference]
uncertainty_labels: list[uncertainty]
contradiction_notes: list[contradiction]
action_candidates: list[action_candidate]
memory_candidates: list[memory_candidate]
review_status: pending|reviewed|needs_revision|rejected
promotion_status: not_promoted|candidate_only|blocked|approved_elsewhere
created_at: ISO-8601 timestamp
run_id: string
```

## 7. V0 claims-table schema

A claims table separates source claims from inference. Each row should include:

| Field | Required | Meaning |
|---|---:|---|
| `claim_id` | yes | Stable local row id. |
| `claim_text` | yes | What the source says, not what Chaser agent concludes. |
| `evidence_snippet_id` | yes | Link to supporting source snippet. |
| `source_location` | recommended | Line, paragraph, section, or approximate location. |
| `claim_type` | yes | `fact`, `preference`, `instruction`, `constraint`, `status`, `unknown`. |
| `confidence` | yes | `high`, `medium`, `low`, or `requires_review`. |
| `review_note` | recommended | Operator-facing note. |

## 8. V0 evidence-snippet schema

Evidence snippets preserve grounding.

| Field | Required | Meaning |
|---|---:|---|
| `snippet_id` | yes | Stable local snippet id. |
| `text` | yes | Exact quoted or minimally normalized source text. |
| `source_location` | recommended | Line, paragraph, heading, or offset. |
| `supports_claim_ids` | yes | Claim ids supported by the snippet. |
| `privacy_class` | yes | Privacy label inherited from source. |
| `redaction_note` | optional | Note if text was scrubbed before review. |

## 9. V0 uncertainty labels

Allowed labels:

| Label | Meaning |
|---|---|
| `requires_review` | Human review needed before action or promotion. |
| `missing_context` | Source does not provide enough context. |
| `ambiguous_source` | Source can be read more than one way. |
| `unsupported_inference` | Chaser agent inference is not directly proven by the source. |
| `conflicting_source` | Source conflicts with another known source or itself. |
| `privacy_risk` | Output could expose private/sensitive information. |
| `promotion_blocked` | Output must not become canonical without governance. |
| `implementation_unknown` | Blueprint/spec exists but code proof does not yet exist. |

## 10. V0 action-candidate schema

Action candidates are possible next moves, not commands.

| Field | Required | Meaning |
|---|---:|---|
| `action_id` | yes | Stable local id. |
| `action_text` | yes | Proposed human-reviewable next action. |
| `source_claim_ids` | yes | Claims that motivated it. |
| `rationale` | yes | Why the action may follow. |
| `risk_level` | yes | `low`, `medium`, `high`, or `blocked`. |
| `requires_approval` | yes | Boolean; true for anything beyond review-only output. |
| `blocked_reason` | optional | Required when risk is `blocked`. |
| `suggested_owner` | optional | Human/operator or future lane, not auto-assignment. |

## 11. V0 memory-candidate schema

Memory candidates are suggestions only. They are never memory in V0.

| Field | Required | Meaning |
|---|---:|---|
| `memory_candidate_id` | yes | Stable local id. |
| `candidate_text` | yes | Proposed durable fact/preference/convention. |
| `evidence_snippet_id` | yes | Exact evidence. |
| `scope` | yes | `user`, `project`, `repo`, `workflow`, or `unknown`. |
| `stability` | yes | `stable`, `likely_stable`, `temporary`, or `unknown`. |
| `privacy_class` | yes | Inherited/derived privacy. |
| `promotion_status` | yes | Always `candidate_only` in V0. |
| `review_required` | yes | Always true in V0. |
| `rejection_reason` | optional | If unsafe, stale, unsupported, or too temporary. |

## 12. V0 human-review packet schema

The review packet points the operator at the decision. It should follow `docs/02_Evals/Chaser-Agent-V0-Human-Review-Packet.md` and include:

```yaml
run_id: string
source_id: string
operator_review_status: pending|pass|fail|needs_revision
scores:
  source_fidelity: 0|1|2|3
  inference_separation: 0|1|2|3
  uncertainty_handling: 0|1|2|3
  action_usefulness: 0|1|2|3
  memory_safety: 0|1|2|3
checklists:
  source_fidelity: list[item]
  inference_separation: list[item]
  uncertainty: list[item]
  action_usefulness: list[item]
  memory_safety: list[item]
canonical_promotion_warning: string
pass_fail_decision: pass|fail|needs_revision
reviewer_notes: string
```

## 13. V0 run-log schema

The run log records reproducibility and boundaries.

| Field | Required | Meaning |
|---|---:|---|
| `run_id` | yes | Unique run id. |
| `created_at` | yes | ISO-8601 timestamp. |
| `command` | yes | Local command or function used. |
| `repo_commit` | recommended | Git commit if available. |
| `input_source_id` | yes | Source id. |
| `outputs` | yes | Paths to generated artifacts. |
| `provider_calls` | yes | Must be `none` in V0. |
| `external_api_calls` | yes | Must be `none` in V0. |
| `runtime_adapters` | yes | Must be `none` in this pass. |
| `blocked_actions` | yes | Any denied action/promotion/tool request. |
| `review_required` | yes | Must be true. |
| `notes` | optional | Implementation notes. |

## 14. V0 folder/file targets

Implementation targets for the next pass:

```text
docs/01_Product/Chaser-Agent-V0-Blueprint.md
docs/03_Summary_Intelligence/Chaser-Agent-V0-Source-Card-Schema.md
docs/02_Evals/Chaser-Agent-V0-Human-Review-Packet.md
docs/03_Summary_Intelligence/Chaser-Agent-Source-Summary-Spec.md
src/chaser_agent/summary/
src/chaser_agent/harness/
tests/
evals/datasets/golden/
logs/runs/<run_id>/
logs/build/
```

Phase 1 may add code under `src/chaser_agent/summary/` and tests under `tests/`, but this blueprint pass does not deepen eval code.

## 15. V0 non-goals

V0 does not:

- auto-promote memory;
- mutate ChaseOS canonical truth;
- call external APIs by default;
- browse the web by default;
- activate Hermes/OpenClaw adapters by default;
- activate provider/model router calls by default;
- activate MCP tools or resources;
- fine-tune models;
- run LoRA/PEFT/model-training;
- read secrets;
- write outside declared outputs/logs;
- treat generated output as canonical truth;
- claim production readiness;
- claim all 17 layers are implemented.

## 16. V0 pass/fail definition

A V0 source-card run passes only if:

1. input is safe/reviewable and privacy-classed;
2. source claims are separated from Chaser agent inferences;
3. evidence snippets support source claims;
4. uncertainty is labeled;
5. action candidates are framed as review-only;
6. memory candidates are framed as review-only;
7. the review packet contains checklist scores and pass/fail decision fields;
8. the run log records that provider/API/runtime adapter calls were not used;
9. outputs land only in declared run-log/output folders;
10. no canonical promotion is claimed.

A run fails if it invents unsupported source facts, hides uncertainty, promotes memory, issues actions as commands, writes outside declared targets, leaks private data, calls tools/providers without approval, or implies production readiness.

## 17. V0 relationship to Layer 0

Layer 0 is the product constitution. V0 is the first practical behavior shape that must obey it. If V0 output conflicts with Layer 0, Layer 0 wins.

## 18. V0 relationship to the 17-layer architecture

The 17-layer architecture remains a map, not an implementation claim. V0 touches only the minimum layers needed for a review-first source-card loop: source intake, summary intelligence, memory candidate state, harness/run logging, and human review. Provider, MCP, browser, runtime adapter, and training layers remain inactive.

## 19. V0 relationship to future evals

This blueprint defines the expected artifact shape that later contract evals can test. Existing JSONL/tests remain smoke/schema checks unless they directly test Layer 0 behavior. Product-quality evals come after Source Card Harness V0 exists.

## 20. V0 relationship to future fine-tuning

Fine-tuning, LoRA, and PEFT are deferred. V0 may eventually produce reviewed examples, but no V0 output is training data until it passes privacy review, human review, dataset policy, and explicit operator/governance approval.
