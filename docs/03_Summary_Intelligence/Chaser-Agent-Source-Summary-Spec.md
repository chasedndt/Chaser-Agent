
# Chaser agent Source Summary Spec

## Required upstream docs

Source summary is the first V0 behaviour implementation. Read these docs before changing source-summary behavior:

1. `docs/01_Product/Chaser-Agent-Layer-0-Behaviour-Contract.md`
2. `docs/01_Product/Chaser-Agent-V0-Definition.md`
3. `docs/01_Product/Chaser-Agent-V0-Blueprint.md`
4. `docs/03_Summary_Intelligence/Chaser-Agent-V0-Source-Card-Schema.md`
5. `docs/02_Evals/Chaser-Agent-V0-Human-Review-Packet.md`

## Layer 0 inheritance

Source summary must obey Layer 0. It turns safe source input into a structured review artifact that separates source claims, Chaser agent inferences, uncertainty, actions, memory candidates, and non-promotion notes.

Nothing in the source-summary loop is approved durable state without an explicit governance decision. Standalone governance can approve local durable state; ChaseOS governance controls shared canonical state in an integrated deployment.

## V0 behaviour implementation

The first V0 behavior implementation is available through the deterministic local Source Card Harness V0:

```bash
.venv/bin/python -m chaser_agent.cli source-card --input examples/sources/toy_website_design_note.md --out logs/runs --profile website_design_review
```

The command writes a unique run folder under `logs/runs/` and produces:

```text
safe source input
→ intake metadata
→ source_card.json
→ claims_table.json
→ evidence_snippets.json
→ uncertainty_labels.json
→ contradiction notes inside source_card.json
→ action_candidates.json
→ memory_candidates.json
→ human_review_packet.json
→ run_log.json
```

The implementation is local, deterministic, review-only, and provider-free. It skips Markdown headings as claims, preserves source order, classifies how a source presents a statement rather than calling it a fact, links copied evidence snippets, and delegates domain-specific inference, uncertainty, actions, and memory proposals to an explicit workflow profile. The general profile is the default; AI-engineering and website-design profiles are opt-in.

## Output status

All outputs are review-only:

- source summaries are review-only;
- roadmap impact is review-only;
- memory candidates are review-only;
- action candidates are review-only;
- contradiction notes are review-only;
- human review packets are review aids, not automatic approvals;
- run logs are provenance records, not production-readiness proof.

## Source card fields

Use `docs/03_Summary_Intelligence/Chaser-Agent-V0-Source-Card-Schema.md` as the concrete schema source. Minimum fields:

- `source_id`
- `source_title`
- `source_type`
- `source_origin`
- `privacy_class`
- `workflow_profile`
- `workflow_profile_version`
- `trust_state`
- `source_summary`
- `source_claims`
- `chaser_agent_inferences`
- `uncertainty_labels`
- `contradiction_notes`
- `action_candidates`
- `memory_candidates`
- `review_status`
- `promotion_status`
- `created_at`
- `run_id`

## Review-only boundaries

- Action candidates do not automatically become tasks.
- Memory candidates do not automatically become memory.
- Roadmap impacts do not automatically update the roadmap.
- Source summaries do not become public claims.
- Generated text is not canonical truth.
- Chaser agent does not mutate ChaseOS canonical docs.
- Standalone local governance owns approved durable local promotion; ChaseOS governance owns shared canonical promotion.

## Forbidden in this V0 source-summary path

- provider/API calls by default;
- web browsing by default;
- Hermes/OpenClaw adapter activation;
- MCP tool/resource activation;
- fine-tuning, LoRA, PEFT, or training;
- secrets/private dataset ingestion;
- writes outside declared output/log folders;
- production-readiness claims.

## Failure modes to test later

- unsupported claims;
- missing uncertainty labels;
- auto-promoted memory;
- actions written as commands rather than candidates;
- private data leakage;
- treating a weak source as authoritative;
- confusing Chaser agent notes with ChaseOS governance;
- using generated output as canonical truth;
- failing to record blocked promotion/tool/provider behavior.
