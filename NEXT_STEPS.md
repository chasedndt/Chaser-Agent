
# Chaser Agent Next Steps

## Current state

Chaser agent is reset to the correct thinking order: Layer 0 first, V0 Definition second, V0 Blueprint third, 17 layers as a subordinate map, learning foundations before deeper evals, and implementation only after behavior is defined.

## Completed foundation

- Layer 0 Behaviour Contract created.
- V0 Definition created.
- V0 Blueprint created.
- First-Principles model created.
- Product Thesis rewritten from Layer 0.
- Roadmap restarted from fundamentals.
- 17-layer architecture depends on Layer 0.
- AI engineering learning ladder expanded.
- Maths foundation handout expanded.
- University module linkage expanded.
- Existing tests/JSONL classified as smoke/schema unless they test Layer 0 behavior.
- Source Summary Spec marked as first V0 behavior implementation and review-only.

## Current next implementation pass

**Phase 1 — Source Card Harness V0 is implemented.**

Run it from the repo root:

```bash
.venv/bin/python -m chaser_agent.cli source-card --input examples/sources/toy_website_design_note.md --out logs/runs
```

It writes a unique `logs/runs/source-card-.../` folder containing source-card, claims-table, evidence-snippet, uncertainty-label, action-candidate, memory-candidate, human-review-packet, and run-log JSON artifacts.

The artifacts prove the local V0 shape only. They are deterministic and not LLM-powered. They remain review-only and do not promote memory, execute actions, call providers/APIs, activate runtime adapters/MCP/browser/computer-use, fine-tune models, mutate ChaseOS canonical truth, or claim production readiness.

## Long-range Chaser Agent multi-domain harness direction

The orchestration/harness product is **Chaser Agent**—not “Chase Agent.” Chaser Agent is not primarily a trading agent. It is the governed, computer-local, multi-domain harness for reusable skills, workflows, datasets, evals, tools, and approval boundaries.

Trading/StrikeZone is one methodology pack alongside source intelligence, social-media growth/control, web and UI design, coding, business operations, and future personal workflows. Each domain must keep separate authority, evidence, evaluation, review, and rollback contracts.

The overall progression is bounded source/review foundations → evaluated domain skills → governed workflow execution → separately approved higher-authority capabilities. Within the trading pack only, execution progression remains observation-only → structured candidates → paper/digital twin → shadow live → human-approved orders → bounded autonomy.

See [`docs/plans/2026-07-11-multi-domain-agent-harness-direction.md`](docs/plans/2026-07-11-multi-domain-agent-harness-direction.md). The immediate V0 pass remains Source Card Harness Review or Contract Eval Seeds.

## Not next anymore

Eval harness v0.2 is not the immediate next step. The next pass after Source Card Harness V0 should be **Source Card Harness Review** or **Contract Eval Seeds**, using the generated artifacts as the first shape proof.

## Not now

- no provider/API calls;
- no Hermes/OpenClaw adapter activation;
- no MCP tools/resources;
- no browser/computer-use runtime;
- no fine-tuning, LoRA, PEFT, or model training;
- no private dataset ingestion;
- no ChaseOS canonical mutation;
- no production-readiness claims.
