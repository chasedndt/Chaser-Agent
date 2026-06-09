
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

The repo exists and tests run, but existing JSONL/tests are smoke/schema checks unless they test Layer 0 behavior. The V0 Blueprint now defines the implementation-ready loop. Eval harness v0.2 is not the immediate next step anymore.

## Next implementation pass

**Phase 1 — Source Card Harness V0**

Implement the first deterministic source-card loop from the V0 Blueprint. Do not start provider/API calls, Hermes/OpenClaw adapters, MCP tooling, browser/computer-use runtime, fine-tuning, or ChaseOS canonical mutation.

## Verification

```bash
.venv/bin/python -m scripts.validate_jsonl evals/datasets/golden/*.jsonl
PYTHONPATH=. .venv/bin/python -m pytest -q
```
