# Build Log — Weekly Research Intake Phase 1B Start

**Date:** 2026-06-16  
**Runtime lane:** Hermes/Optimus under ChaseOS Agent Control Plane  
**Repo:** Chaser Agent  
**Scope:** bounded public arXiv API ingestion + JSONL normalization

## What changed

Added the first Phase 1B ingestion slice:

- `research_intake/__init__.py`
- `research_intake/ingest.py`
- `tests/test_research_intake_ingest.py`
- `research_intake/data/.gitkeep`
- `research_intake/data/raw/.gitkeep`
- `research_intake/data/normalized/.gitkeep`
- `.gitignore` entries for generated `research_intake/data/arxiv-ingest-*` artifacts

## Capabilities added

- Parse arXiv Atom XML into normalized `PaperRecord` objects.
- Parse arXiv RSS category feeds into normalized `PaperRecord` objects.
- Canonicalize arXiv IDs and URLs without version suffixes.
- Dedupe records by base arXiv ID.
- Run fixture-backed multi-query consolidation.
- Write local per-run artifacts:
  - raw `arxiv_api.xml`
  - `raw_records.jsonl`
  - Chase schema-compatible `papers.jsonl`
  - `manifest.json`
- Run bounded live arXiv API smoke with `--max-results`.

## Control-plane boundary

Allowed in this slice:

- public arXiv API read;
- local raw/normalized artifact writes under `research_intake/data/`;
- fixture-backed tests;
- no-op paper decisions initialized as `unread`.

Blocked:

- provider/model calls;
- credentials;
- candidate implementation;
- branch/PR automation from the workflow;
- canonical ChaseOS promotion;
- permission expansion;
- deployment.

## Verification

```text
PYTHONPATH=. .venv/bin/python -m research_intake.ingest --max-results 3 --query 'cat:cs.AI AND (agent OR harness OR tool use)' --out research_intake/data
status: pass
phase: phase_1b_primary_source_ingestion
raw_count: 3
deduped_count: 3
papers_jsonl: research_intake/data/arxiv-ingest-20260616T224018Z/normalized/papers.jsonl

PYTHONPATH=. .venv/bin/python -m pytest tests/test_research_intake_ingest.py tests/test_weekly_research_intake_config.py -q
8 passed in 1.49s

PYTHONPATH=. .venv/bin/python -m pytest tests/test_research_intake_ingest.py tests/test_weekly_research_intake_config.py tests/test_source_card_harness.py -q
12 passed in 1.81s

PYTHONPATH=. .venv/bin/python -m research_intake.ingest --rss-url https://rss.arxiv.org/rss/cs.AI --query rss:cs.AI --out research_intake/data
status: pass
phase: phase_1b_primary_source_ingestion
raw_count: 664
deduped_count: 664
papers_jsonl: research_intake/data/arxiv-rss-ingest-20260616T225028Z/normalized/papers.jsonl

bash /home/chaseos/runtimes/hermes-home/scripts/chaser_agent_weekly_research_intake_dry_run.sh
Chaser Agent weekly research intake dry-run: pass
Artifact: logs/runs/weekly-research-intake-dry-run-20260616T224423Z

.venv/bin/python scripts/weekly_research_intake_dry_run.py --out logs/runs
logs/runs/weekly-research-intake-dry-run-20260616T224026Z
```

Full `pytest -q` currently includes unrelated uncommitted SkillGate worktree files and fails on `tests/test_skillgate_harness.py` missing `build_agent_skills_sentinel_preflight`; this Phase 1B commit does not stage or modify that lane.

## Remaining Phase 1B work

- Add multi-query batch runner over `research_intake/queries.yaml` for live API/RSS runs.
- Add DOI extraction and DOI-based dedupe when metadata includes it.
- Add weekly consolidated `research_intake/data/papers.jsonl` output once batch ingestion exists.
