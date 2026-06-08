# Chaser agent Eval Harness

Eval-driven development means features are built against explicit examples before they are treated as real.

Golden sets are reviewed examples that represent expected behavior. JSONL stores one case per line. Pass/fail results show whether a feature met minimum requirements. Human review catches nuance that automated scores miss. Regression tests prevent old failures from returning. Score logs preserve what changed and why.

Outputs should improve prompts, skills, harnesses, adapter contracts, and eventually datasets. They should not jump straight to training.

> A Chaser agent feature is not considered real until it has an eval, a failure mode, and a regression check.

## Minimal loop
1. Add or select a golden case.
2. Run the deterministic or model-backed candidate.
3. Score required fields and rubric properties.
4. Record failures honestly.
5. Improve code/prompt/skill.
6. Re-run as a regression check.
