# Research Intake

Phase 1A scaffold for the ChaseOS/Chaser Agent weekly research upgrade loop.

This directory is config-first and control-plane bounded. It defines what to monitor and how to score it, but it does not by itself activate network ingestion, provider use, candidate implementation, branch creation, PRs, merges, or ChaseOS canonical promotion.

Start with:

```bash
.venv/bin/python scripts/weekly_research_intake_dry_run.py --out logs/runs
```

Then inspect the generated `logs/runs/weekly-research-intake-dry-run-*/manifest.json` and `digest.md`.
