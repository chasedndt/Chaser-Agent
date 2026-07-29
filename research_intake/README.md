# Research Intake

Phase 1A completed scaffold for the ChaseOS/Chaser Agent weekly research upgrade loop.

This directory is config-first and control-plane bounded. It defines what to monitor and how to score it, but it does not by itself activate network ingestion, provider use, candidate implementation, branch creation, PRs, merges, or ChaseOS canonical promotion.

Start with:

```bash
.venv/bin/python scripts/weekly_research_intake_dry_run.py --out logs/runs
```

Then inspect the generated `logs/runs/weekly-research-intake-dry-run-*/manifest.json` and `digest.md`.

## Phase 1B arXiv ingestion

Phase 1B starts with bounded public arXiv ingestion plus explicit configuration for public industry-practice sources. Industry links are research inputs only; they do not authorize browser automation, provider calls, paid access, MCP activation, monetization changes, or candidate implementation.

### Industry-practice source queue

`research_intake/sources.yaml` now includes `industry_practice_blogs` for public-web research sources such as Cloudflare. The first priority URL is:

- https://blog.cloudflare.com/monetization-gateway/

These sources should produce source cards / monetization-risk notes before any implementation. Any payment, x402, billing, wallet, stablecoin, MCP activation, customer-facing, or production action requires separate human approval.

### arXiv ingestion

Bounded public arXiv ingestion:

Search API:

```bash
PYTHONPATH=. .venv/bin/python -m research_intake.ingest \
  --max-results 25 \
  --query 'cat:cs.AI AND (agent OR harness OR tool use)' \
  --out research_intake/data
```

RSS category feed:

```bash
PYTHONPATH=. .venv/bin/python -m research_intake.ingest \
  --rss-url https://rss.arxiv.org/rss/cs.AI \
  --query rss:cs.AI \
  --out research_intake/data
```

It writes per-run artifacts under ignored timestamped folders:

- `research_intake/data/arxiv-ingest-*/raw/arxiv_api.xml`
- `research_intake/data/arxiv-ingest-*/normalized/raw_records.jsonl`
- `research_intake/data/arxiv-ingest-*/normalized/papers.jsonl`
- `research_intake/data/arxiv-ingest-*/manifest.json`

Control-plane boundary remains closed for providers, credentials, candidate implementation, branch/PR automation, canonical promotion, and permission expansion.
