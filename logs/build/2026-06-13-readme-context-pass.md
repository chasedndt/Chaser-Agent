# 2026-06-13 README context pass

## Scope

Updated the public repo `README.md` for Chaser Agent to be more contextful and closer in spirit to the internal ChaseOS README style, while respecting the operator instruction not to put the roadmap in the README.

## Branch / repo

- Repo: `/mnt/c/Users/chaseos/Documents/Projects/chaser-agent`
- Branch started: `main`
- Branch ended: `main`
- Remote: `git@github.com:chasedndt/Chaser-Agent.git`

## Baseline checks

Ran before editing:

```bash
git status --short --branch
git remote -v
git log --oneline -5
.venv/bin/python -m scripts.validate_jsonl evals/datasets/golden/*.jsonl
PYTHONPATH=. .venv/bin/python -m pytest -q
```

Result:

- Golden JSONL validation: passed for 6 files, 3 rows each.
- Pytest: `7 passed`.

## Files modified

- `README.md`
- `logs/build/2026-06-13-readme-context-pass.md`

## README changes

The README now includes:

- contextual tagline and product definition;
- explanation of why Chaser Agent exists;
- the ungoverned-output problem statement;
- the review-first source loop;
- current Source Card Harness V0 status;
- core capabilities;
- ChaseOS relationship and boundary;
- explicit non-goals / not-yet list;
- repo safety rules;
- local verification commands;
- Source Card Harness V0 command and output list;
- start-reading list;
- public positioning copy.

## Explicitly not included

Per operator instruction, the README does **not** include the roadmap. It also does not claim provider/API calls, browser authority, Hermes/OpenClaw adapter activation, fine-tuning, private dataset ingestion, production autonomy, or ChaseOS canonical promotion.

## Stash note

Existing stash left untouched:

```text
stash@{0}: On docs/spec-deepening-pass: pre-layer0-reset-uncommitted-work-2026-06-09
```

## Final validation

Run after editing before commit/push:

```bash
.venv/bin/python -m scripts.validate_jsonl evals/datasets/golden/*.jsonl
PYTHONPATH=. .venv/bin/python -m pytest -q
```

Result:

- Golden JSONL validation: passed for 6 files, 3 rows each.
- Pytest: `7 passed in 10.46s`.
- README roadmap check: no `roadmap` matches in `README.md`.
