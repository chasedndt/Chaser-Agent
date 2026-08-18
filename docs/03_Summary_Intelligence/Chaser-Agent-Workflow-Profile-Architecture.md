# Chaser Agent Workflow Profile Architecture

**Layer:** 7 (Summary Intelligence) and 17 (Extension / Skill) · **Status:** implemented in P0.1 · **Code:** `src/chaser_agent/workflows/`

## The defect this fixes

The pre-P0.1 builder accepted arbitrary text but contained hard-coded website-design behaviour: design keywords, design-specific uncertainty text, design-specific inferences, actions, and memory candidates. A generic-looking interface therefore behaved like a website-design reviewer no matter what you fed it. Feeding it a research paper produced design language.

Workflow profiles separate **domain-specific behaviour** from the **domain-neutral core** (Principle 4).

## The split

```text
core builder              profile
-----------               -------
normalise text            claim hints
split sentences           uncertainty rules
preserve headings         domain inference
create evidence           domain actions
attach source locations   memory policy
neutral claim candidates  review dimensions
```

The core performs generic deterministic extraction, then calls the selected profile. The core contains no domain vocabulary.

## Profile contract

Defined as a `Protocol` in `core/protocols.py` (`WorkflowProfile`), with safe defaults in `workflows/base.py` (`SafeReviewProfile`). Every profile declares:

```text
profile_id · display_name · version · purpose
allowed_input_types · claim_hints · uncertainty_rules
action_policy · memory_policy · forbidden_actions
required_review_dimensions · tags
```

and implements four builders: `build_uncertainties`, `build_inferences`, `build_actions`, `build_memories`.

### What a profile may do

Guide deterministic claim selection · add labelled domain inference · add domain-specific uncertainty checks · propose domain review actions · propose memory candidates.

### What a profile may never do

Execute an action · promote memory · call a provider · grant tool permission · modify governance · bypass review · increase runtime authority.

**Principle 11: profiles do not grant permissions.** A profile shapes analysis; it cannot expand authority. `SafeReviewProfile` hard-codes `FORBIDDEN_EXTERNAL_ACTIONS` (public posts, messages, payments, trades, deployments, account changes, credential operations, destructive file changes, external tool calls) and every generated action carries `requires_approval: True` with `suggested_owner: human_operator`.

## Built-in profiles

### `general_source_review` — the default

Source-neutral and conservative. No website, media, or trading language unless that language is present in the source itself. Generic uncertainty labels. Safe review actions. **Memory defaults to empty**: `SafeReviewProfile.build_memories` returns `[]`, encoding the rule that not every source deserves a memory candidate. Durability must be evident, not assumed.

### `ai_engineering_research_review`

For technical and research sources. Distinguishes *reported results* from *Chaser Agent implications*; surfaces methodology limitations, eval limitations, and missing baselines; proposes architecture questions, eval candidates, and RFC candidates; preserves citation provenance. Core rule: a paper claim is never production truth.

### `website_design_review` — optional and explicit

Preserves the genuinely useful design-review concerns that were wrongly living in the core: hierarchy, contrast, spacing, readability, restraint, user intent, and requests for visual proof when needed. Now it only activates when explicitly selected.

## Default uncertainty labels

Every profile inherits two safe defaults:

- `requires_review` — deterministic extraction does not establish that source statements are correct;
- `promotion_blocked` — review artifacts and memory candidates are not approved durable memory until an explicit governed promotion.

## Memory candidate shape

`memory_from_claim()` produces candidates that are always `promotion_status: candidate_only`, `review_required: True`, carrying `evidence_snippet_id` for provenance and an explicit `privacy_class`.

## Profile isolation is tested

`tests/test_workflow_profiles.py` asserts the general profile is the default, that it emits no design or media boilerplate, that the website profile's design language appears *only* when selected, and that profiles cannot grant permission or auto-promote memory. Profile leakage is a test failure, not a style question.

## Future profiles — not in P0.1

`trading_research_review` · `business_research_review` · `university_learning_review` · `media_creation_review` · `cybersecurity_research_review` · `software_repository_review`

Media creation must never become the default profile or define core behaviour.
