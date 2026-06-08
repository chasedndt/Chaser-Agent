# Chaser agent Next Steps

> Status: post-scaffold, post-reference-doc pass. Repo path: `C:\Users\chaseos\Documents\Projects\chaser-agent`.

## Current state

The standalone Chaser agent repo now has the scaffold, eval foundation, ChaseOS-aligned reference docs, JSONL golden toy datasets, rubrics, starter skills, and a minimal importable Python package.

ChaseOS remains the parent control plane and canonical governance layer. Chaser agent is the focused product/runtime implementation and eval lab. No ChaseOS canonical files should be changed from this repo without a separate explicit ChaseOS-side approval pass.

## Completed checklist

- [x] Repo exists at the real Windows project path.
- [x] Git remote is configured for `git@github.com:chasedndt/Chaser-Agent.git`.
- [x] Scaffold docs, package, datasets, rubrics, skills, tests, and build log exist.
- [x] Missing Chaser agent reference docs from the starter-pack plan exist inside this repo.
- [x] JSONL validator passes across all golden datasets.
- [x] Import and deterministic eval-runner smoke pass.
- [x] Repo has been pushed to GitHub.

## Immediate next step: make the test environment real

Before building new features, create a local venv and run the full test suite with pytest. The current system Python does not have `pytest`, so use an isolated environment:

```bash
cd /mnt/c/Users/chaseos/Documents/Projects/chaser-agent
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -e .[dev]
python -m scripts.validate_jsonl evals/datasets/golden/*.jsonl
python -m pytest -q
```

Definition of done:

- `pytest` runs without missing-package errors.
- All scaffold tests pass, or failures are documented honestly.
- `HANDOVER.md` and the build log are updated with real pytest results.

## Next build pass: eval harness v0.2

After pytest is real, the next implementation pass should upgrade the eval harness from scaffold smoke tests to useful product instrumentation.

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
5. Keep all logic deterministic for now. No LLM calls yet.

Definition of done:

- All six golden JSONL files can be run through the eval runner.
- Each run writes a valid JSONL result file.
- Tests cover the runner and failure reasons.
- No private data, secrets, external API calls, or ChaseOS canonical writes occur.

## Next documentation pass: ChaseOS-side proposal packet

The starter pack also recommends ChaseOS-side files under `06_AGENTS/`. That should be a separate proposal/approval pass, not an automatic write from this repo.

Recommended next document artifact inside this repo:

```text
docs/09_ChaseOS_Alignment/ChaseOS-Side-Proposal-Packet.md
```

That packet should list the proposed ChaseOS-side files, why each matters, whether it should become canonical, and what approval is needed. Only after operator approval should ChaseOS itself be modified.

## Do not do yet

- Do not fine-tune.
- Do not prepare LoRA/PEFT data.
- Do not ingest private user logs.
- Do not add external API/provider calls.
- Do not mutate ChaseOS canonical docs.
- Do not add broad autonomous runtime behavior.

## Operator decision needed

Choose the next lane:

1. **Recommended:** run venv + pytest and update handover/build log with real results.
2. Build eval harness v0.2 after pytest is verified.
3. Draft a ChaseOS-side proposal packet for the `06_AGENTS/` docs.
