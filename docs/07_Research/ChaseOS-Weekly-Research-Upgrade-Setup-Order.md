# ChaseOS Weekly Research Upgrade — Setup Order

**Date:** 2026-06-16  
**Runtime lane:** Hermes/Optimus operating under ChaseOS Agent Control Plane  
**Repo:** Chaser Agent  
**Status:** Phase 1A complete; bounded dry-run cron active; Phase 1B next

## Control-plane boundary

This lane is a ChaseOS-governed research/eval pipeline, not an autonomous self-modification loop.

The first bounded Hermes cron is now active on this local ChaseOS machine:

- Name: `Chaser Agent weekly research intake dry-run`
- Job id: `88bb31188587`
- Schedule: `0 5 * * 1`
- Mode: script-backed `no_agent=true`
- Script: `/home/chaseos/runtimes/hermes-home/scripts/chaser_agent_weekly_research_intake_dry_run.sh`
- Scope: Phase 1A config validation and local artifact summary only

Allowed now:

- configure research sources and queries;
- validate source/ranking configs;
- write local research-intake run logs and draft digests;
- emit RFC candidates for human review;
- propose cron registrations.

Blocked until explicit approval and eval proof:

- canonical ChaseOS promotion;
- credential/provider activation;
- live browser/account automation;
- candidate branch implementation;
- PR creation/merge;
- permission expansion;
- production deployment;
- security/cyber capability changes.

## Recommended implementation order

1. **Phase 1A — deterministic intake scaffold** ✅ complete
   - Create source/query/ranking configs.
   - Add a dry-run script that validates configs and writes a run artifact.
   - Register bounded script-backed Hermes cron for local dry-run reporting.
   - Do not fetch network or call providers yet.

2. **Phase 1B — primary-source ingestion** ⏳ in progress
   - Add arXiv API/RSS ingestion first. ✅ arXiv API + RSS bounded ingest added
   - Normalize to JSONL paper records. ✅ fixture + live-smoke proven
   - Dedupe by arXiv ID/DOI/title hash. ✅ arXiv ID/title fallback dedupe added
   - Remaining: multi-query batch runner over `queries.yaml` for live API/RSS runs, then consolidated weekly `papers.jsonl`.

3. **Phase 1C — scholarly metadata enrichment**
   - Add Semantic Scholar and OpenAlex metadata/recommendation enrichment.
   - Keep rate limits explicit.
   - Store raw responses under `research_intake/data/raw/`, normalized records under `research_intake/data/normalized/`.

4. **Phase 1D — weekly digest and paper cards**
   - Score papers with the Chaser Agent rubric.
   - Write `paper_cards.jsonl` and `weekly_digests/YYYY-WW.md`.
   - Mark `implement_now` as advisory only until eval foundation exists.

5. **Phase 2 — eval foundation before implementation**
   - Build private eval suites for Chaser/ChaseOS task classes.
   - Establish baseline reports.
   - Only then allow candidate RFC branches.

6. **Phase 3+ — RFC/candidate loop**
   - Generate top RFCs.
   - Implement isolated candidate branches only after human approval.
   - Merge only when the eval gate passes.

## Cron order

1. First cron should be **script-backed dry-run only**: validate config and write local run artifact.
2. Second cron can summarize the latest verified artifact into a short Discord digest.
3. Network ingestion cron comes after the dry-run artifact proves local paths/configs.
4. Candidate implementation cron remains disabled/manual-dispatch until eval gates are mature.

## Files introduced by this setup pass

- `research_intake/sources.yaml`
- `research_intake/queries.yaml`
- `research_intake/ranking.yaml`
- `research_intake/cron_proposal.yaml`
- `scripts/weekly_research_intake_dry_run.py`
- `tests/test_weekly_research_intake_config.py`

## Phase 1A completion gate

Phase 1A is complete when all of these are true:

- source/query/ranking/cron configs validate;
- the local dry-run writes `manifest.json` and `digest.md` artifacts;
- the active Hermes cron is documented as `88bb31188587`;
- the manifest exposes the next phase as `phase_1b_primary_source_ingestion`;
- authority boundaries remain closed for network ingestion, providers, credentials, candidate implementation, PR/merge automation, permission expansion, and canonical promotion.

## Completed approval checkpoint

The first bounded Hermes cron registration is active:

```text
Job ID: 88bb31188587
Schedule: 0 5 * * 1
Mode: script-backed no_agent=true
Command: .venv/bin/python scripts/weekly_research_intake_dry_run.py --out logs/runs
Delivery: origin summary only
```

That approval does not authorize network ingestion, provider use, candidate branches, PRs, or merges.

## Next approval checkpoint — Phase 1B

Phase 1B should add arXiv API/RSS ingestion behind an explicit command and tests. The next approval should remain bounded to network reads from public research sources only, with no provider/model calls and no candidate implementation authority.
