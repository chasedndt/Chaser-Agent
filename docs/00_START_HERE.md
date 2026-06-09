
# Docs Start Here

Read Layer 0 first. The docs are ordered to define behavior before architecture, evals, tools, adapters, or training.

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
11. `docs/02_Evals/Chaser-Agent-Eval-Harness.md`
12. `docs/02_Evals/Chaser-Agent-Dataset-Plan.md`
13. `docs/08_Learning/AI-Engineering-Learning-Map.md`
14. `docs/08_Learning/Maths-For-Chaser-Agent.md`
15. `docs/08_Learning/University-Module-Linkage.md`

Current local repo path: `C:\Users\chaseos\Documents\Projects\chaser-agent`.

WSL path: `/mnt/c/Users/chaseos/Documents/Projects/chaser-agent`.

## Source Card Harness V0

Run the deterministic local Phase 1 harness from the repo root:

```bash
.venv/bin/python -m chaser_agent.cli source-card --input examples/sources/toy_website_design_note.md --out logs/runs
```

The command prints the unique run folder under `logs/runs/`. The run folder contains the V0 artifact loop as JSON:

- `source_card.json` — central review artifact with source claims separated from inferences;
- `claims_table.json` — source-claim rows and supporting evidence links;
- `evidence_snippets.json` — copied snippets from the safe local source;
- `uncertainty_labels.json` — missing-context/review/promotion-boundary labels;
- `action_candidates.json` — review-only possible next moves, not executed actions;
- `memory_candidates.json` — candidate-only memory suggestions, not promoted memory;
- `human_review_packet.json` — operator review checklist scaffold;
- `run_log.json` — provenance and boundary record showing no providers/APIs/runtime adapters/MCP/browser/training were used.

Outputs are deterministic, local, review-only, and not LLM-powered. They do not mutate ChaseOS canonical truth and do not claim production readiness.

Eval harness v0.2 is not the immediate next step anymore. The next pass after Source Card Harness V0 should be Source Card Harness Review or Contract Eval Seeds.
