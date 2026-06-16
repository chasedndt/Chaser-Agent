# Build Log — Weekly Research Intake Phase 1A

**Date:** 2026-06-16  
**Runtime identity:** Hermes/Optimus under ChaseOS Agent Control Plane  
**Repo:** `/mnt/c/Users/chaseos/Documents/Projects/chaser-agent`  
**Scope:** deterministic local setup scaffold only

## Authority boundary

This pass starts the ChaseOS/Chaser Agent weekly research upgrade loop as a bounded research-intake lane. It does not activate live self-upgrade authority.

Allowed in this pass:

- local config files for research sources, queries, ranking, and cron proposals;
- deterministic dry-run script;
- tests for control-plane bounds;
- build-log documentation.

Not performed:

- no live Hermes cron registration;
- no network ingestion;
- no provider/API/credential activation;
- no candidate branch implementation;
- no PR/merge;
- no ChaseOS canonical promotion;
- no protected-file edits.

## Files added

- `research_intake/sources.yaml`
- `research_intake/queries.yaml`
- `research_intake/ranking.yaml`
- `research_intake/cron_proposal.yaml`
- `scripts/weekly_research_intake_dry_run.py`
- `tests/test_weekly_research_intake_config.py`
- `docs/07_Research/ChaseOS-Weekly-Research-Upgrade-Setup-Order.md`

## Recommended next order

1. Prove Phase 1A dry run locally.
2. Approve/monitor the active script-backed weekly Hermes cron for dry-run reporting (`88bb31188587`).
3. Add arXiv API/RSS ingestion and normalization.
4. Add paper scoring and weekly digest writer.
5. Build private eval foundation before any candidate implementation.

## Phase 1A closeout update — 2026-06-16

Phase 1A is now marked complete in repo documentation and dry-run artifacts. The manifest now includes:

- `phase_1a_completion.status = complete`
- `active_cron_job_id = 88bb31188587`
- `next_phase = phase_1b_primary_source_ingestion`
- explicit authority boundaries for no network ingestion, no providers/credentials, no candidate implementation, no PR/merge automation, no permission expansion, and no canonical promotion

Phase 1B should start with arXiv API/RSS ingestion only, behind an explicit command and tests.

## Verification

Verification should run:

```bash
.venv/bin/python scripts/weekly_research_intake_dry_run.py --out logs/runs
PYTHONPATH=. .venv/bin/python -m pytest -q
```

Results:

```text
logs/runs/weekly-research-intake-dry-run-20260616T154659Z
...........                                                              [100%]
11 passed in 15.73s
```

Dry-run manifest status: `pass`.

Dry-run artifact:

- `logs/runs/weekly-research-intake-dry-run-20260616T154659Z/manifest.json`
- `logs/runs/weekly-research-intake-dry-run-20260616T154659Z/digest.md`

Cron wrapper proof:

```text
Chaser Agent weekly research intake dry-run: pass
Artifact: logs/runs/weekly-research-intake-dry-run-20260616T222602Z
Enabled sources: arxiv_api, arxiv_rss
arXiv queries: 4
Control-plane: no canonical promotion, no candidate implementation, no provider/credential activation
```

Full post-activation verification:

```text
5 passed in 0.87s
logs/runs/weekly-research-intake-dry-run-20260616T223602Z
Chaser Agent weekly research intake dry-run: pass
Artifact: logs/runs/weekly-research-intake-dry-run-20260616T223603Z
14 passed in 5.51s
```

Latest closeout manifest proof:

```text
status: pass
phase_1a_completion.status: complete
active_cron_job_id: 88bb31188587
next_phase: phase_1b_primary_source_ingestion
```

Hermes cron wrapper created and active bounded cron registered:

- Job id: `88bb31188587`
- `/home/chaseos/runtimes/hermes-home/scripts/chaser_agent_weekly_research_intake_dry_run.sh`
