
# Start Here — Chaser agent

Start with Layer 0. Do not start with eval implementation.

Read in this order:

1. `docs/01_Product/Chaser-Agent-Layer-0-Behaviour-Contract.md`
2. `docs/01_Product/Chaser-Agent-V0-Definition.md`
3. `docs/01_Product/Chaser-Agent-V0-Blueprint.md`
4. `docs/01_Product/Chaser-Agent-From-First-Principles.md`
5. `docs/01_Product/Chaser-Agent-Product-Thesis.md`
6. `docs/01_Product/Chaser-Agent-Roadmap.md`
7. `docs/01_Product/Chaser-Agent-17-Layer-Architecture.md`
8. `docs/03_Summary_Intelligence/Chaser-Agent-V0-Source-Card-Schema.md`
9. `docs/02_Evals/Chaser-Agent-V0-Human-Review-Packet.md`
10. `docs/03_Summary_Intelligence/Chaser-Agent-Source-Summary-Spec.md`
11. `docs/08_Learning/AI-Engineering-Learning-Map.md`
12. `docs/08_Learning/Maths-For-Chaser-Agent.md`
13. `docs/08_Learning/University-Module-Linkage.md`

## Current truth

The repo exists and tests run, but existing JSONL/tests are smoke/schema checks unless they test Layer 0 behavior. The V0 Blueprint defines the implementation-ready loop, and Phase 1 now provides the first deterministic local Source Card Harness V0. Eval harness v0.2 is not the immediate next step.

## Source Card Harness V0

Run the deterministic local harness from the repo root:

```bash
.venv/bin/python -m chaser_agent.cli source-card --input examples/sources/toy_website_design_note.md --out logs/runs
```

The command prints the unique run folder under `logs/runs/`. That folder contains:

- `source_card.json`
- `claims_table.json`
- `evidence_snippets.json`
- `uncertainty_labels.json`
- `action_candidates.json`
- `memory_candidates.json`
- `human_review_packet.json`
- `run_log.json`

These outputs are deterministic, local, review-only artifacts. They are not LLM/provider output, not memory, not actions, not ChaseOS canonical truth, and not production-readiness proof.

## Next implementation pass

After Phase 1, the next pass should be **Source Card Harness Review**, **Contract Eval Seeds**, or the new **ChaseOS-native review packet V0** when the work needs ChaseOS control-plane handoff shape. Do not jump to provider/API calls, Hermes/OpenClaw adapters, MCP tooling, browser/computer-use runtime, fine-tuning, or ChaseOS canonical mutation.

## ChaseOS-native review packet V0

Run the bounded ChaseOS-native wrapper from the repo root:

```bash
PYTHONPATH=. .venv/bin/python -m chaser_agent.cli chaseos-native-source-card \
  --input examples/sources/toy_website_design_note.md \
  --out logs/runs \
  --workflow hermes_review_execute \
  --runtime-lane chaser-agent
```

This creates the normal Source Card Harness V0 artifacts plus `chaseos_native_packet.json` and `operator_handoff.md`. The packet adds ChaseOS-native routing/review fields while preserving review-only authority boundaries.

## Verification

```bash
.venv/bin/python -m scripts.validate_jsonl evals/datasets/golden/*.jsonl
PYTHONPATH=. .venv/bin/python -m pytest -q
```
