# Chaser agent Next Steps

> Status: Phase 0C spec-deepening pass on `docs/spec-deepening-pass`. Repo path: `C:\Users\chaseos\Documents\Projects\chaser-agent`.

## Current state

The standalone Chaser agent repo has scaffold docs, expanded core specs, toy JSONL golden datasets, rubrics, starter skills, a minimal importable Python package, and a working local WSL test environment.

ChaseOS remains the parent control plane and canonical governance layer. Chaser agent is the focused product/runtime implementation and eval lab. No ChaseOS canonical files should be changed from this repo without a separate explicit ChaseOS-side approval pass.

## Phase 0C completed/active checklist

- [x] Product thesis expanded into useful framing.
- [x] Roadmap expanded into phased deliverables and done criteria.
- [x] 17-layer architecture rewritten from placeholder text into concrete layer specs.
- [x] Dataset plan expanded with JSONL schema, privacy classes, dataset lifecycle, and future fine-tuning boundary.
- [x] Source-summary spec expanded with pipeline, schemas, examples, failure modes, and eval criteria.
- [x] Memory states expanded with transitions and authority boundaries.
- [x] Runtime competitor map strengthened without granting adapter authority.
- [x] Skill system expanded with lifecycle, quarantine, review, eval, rollback, and supply-chain guardrails.
- [x] Research register clarified as Markdown mirror of the Excel operator register.
- [x] ChaseOS website alignment placeholder created for later manual review.

## Validation baseline

WSL `.venv` was created with uv and dev dependencies installed. Baseline after environment creation:

```text
python -m scripts.validate_jsonl evals/datasets/golden/*.jsonl  # all six files valid, 3 rows each
PYTHONPATH=. .venv/bin/python -m pytest -q                         # 5 passed
```

## Next implementation pass: Eval harness v0.2

After this docs/log pass is reviewed and committed/pushed as appropriate, move to eval harness v0.2.

### Scope

1. Add richer `EvalResult` serialization with pass/fail reasons.
2. Add per-family runner support for:
   - source summary
   - action extraction
   - memory candidate extraction
   - citation grounding
   - website design workflow
   - trading research workflow
3. Write result JSONL under `logs/runs/` with timestamps.
4. Add tests that assert result rows include:
   - `id`
   - `task`
   - `passed`
   - `score`
   - `failure_reasons`
   - `output`
   - `timestamp`
   - `runner_version`
5. Keep all logic deterministic for now. No LLM calls yet.

### Definition of done

- All six golden JSONL files run through the eval runner.
- Each run writes a valid JSONL result file.
- Tests cover the runner, result schema, and failure reasons.
- No private data, secrets, external API calls, or ChaseOS canonical writes occur.

## Still do not do yet

- Do not fine-tune.
- Do not prepare LoRA/PEFT data.
- Do not ingest private user logs.
- Do not add external API/provider calls.
- Do not mutate ChaseOS canonical docs.
- Do not add broad autonomous runtime behavior.
- Do not activate Hermes/OpenClaw adapters.
- Do not start UI/Studio work.

## Artifact policy decision

`Chaser_Agent_Research_Eval_Register.xlsx` should be committed as an operator-facing planning artifact because it contains no detected secrets in the inspected workbook and directly maps research signals to evals, dataset plans, repo boundaries, and human rubrics. `PACK_MANIFEST.json` should also be committed as starter-pack provenance, with the understanding that some listed files were absorbed into current docs rather than preserved at the repo root.
