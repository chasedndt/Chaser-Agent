# Codex Handover — Provider & Tool Authority Boundaries + Operator Review

**Date:** 2026-08-12
**Branch:** `codex/standalone-first-memory-realignment` (pushed; **24 commits ahead of `origin/main`**; **not merged — merge is the operator's decision**)
**Suite at handover:** **177 passed**
**Repo:** `git@github.com:chasedndt/Chaser-Agent.git`

---

## 0. How to use this document

Read sections 1–3 before touching anything. Section 3 is the authoritative state; section 6 is the work queue; section 9 lists what must not be done.

This handover covers a Claude session that ran from the standalone-first P0.1 closeout through two new authority boundaries (providers and tools). Everything described is committed and pushed except one deliberately untracked working file (§7.2).

**One-line summary of the arc:** the project moved from *a harness whose guarantees were documented* to *a harness whose guarantees are executed*, and gained two complete authority boundaries — inference and tools — both proven against scripted adversaries before either capability exists.

---

## 1. What changed this session

| Area | Before | After |
|---|---|---|
| Test suite | 28 passed | **177 passed** |
| Layer 0 enforcement | Convention | 30 contract cases, 154 assertions, mutation-verified |
| Standalone-first rule | Documentation only | AST-enforced per core package |
| Layer 12 (provider) | 6-line stub | Envelope + fake adapter + budget + quarantine + comparison rig |
| Layer 13 (tool/MCP) | 6-line stub | Capability registry, 3 gates, scope containment, hostile-result quarantine |
| Claim extraction | Metadata + fragments as claims | Metadata separated, paragraph-aware |
| Operator review data | None | 3 runs generated, **awaiting scores** |

---

## 2. Branch commits (newest first)

```text
9d8ae51 docs: document the tool capability boundary
ea1d540 feat: add least-authority tool and MCP capability boundary
aee51b4 fix: stop extracting document metadata and line fragments as claims
d055d8b perf: memoise the repo commit lookup used by run logs
cf5d28e test: assert contract coverage properties instead of frozen counts
3f86f8d test: expand Layer 0 contract evaluation coverage
76a4a29 docs: record how each provider limit was narrowed
5efac67 feat: add model-assisted review path and calibrated comparison rig
cfacd3e feat: enforce provider cost, latency, and rate ceilings
5639771 feat: contain model output structurally rather than by pattern
02ac71e docs: document the provider boundary and fake adapter
bfe43c1 feat: add provider-neutral fake adapter and inference boundary
fed64a7 docs: document P0.1 subsystem architecture
da2d175 test: enforce standalone-first dependency rule
ec3e6f6 docs: record P0.1 push and closeout          <- concurrent agent
f636135 docs: add standalone P0.1 session records     <- concurrent agent
4670c10 docs: record standalone P0.1 as-built truth
7411883 feat: export exact eval seed matrix
4dd847f feat: add local provenance knowledge map
cdcbcb1 feat: add governed local memory lifecycle
0a4196b feat: persist immutable human review records
9d15a58 feat: add standalone workflow profiles and neutral builder
356741d docs: realign Chaser agent as standalone-first
7caf7ac chore: reconcile Chaser agent local truth state
```

---

## 3. Authoritative current state

### 3.1 Package map

```text
src/chaser_agent/
  core/protocols.py        WorkflowProfile, ReviewStore, MemoryStore, KnowledgeMapStore,
                           ProviderAdapter, ToolRegistry, GovernanceBackend
  workflows/               general_source_review (default), ai_engineering_research_review,
                           website_design_review, base.SafeReviewProfile, registry
  governance/local.py      LocalGovernance, ReviewPolicyProposal (enforced=False)
  reviews/                 ReviewRecord (frozen, hashed), sqlite_store, service
  memory/                  MemoryRecord, lifecycle FSM, append-only sqlite_store, feedback
  knowledge/               KnowledgeNode/Edge (uuid5 identity), sqlite_store, service
  providers/               models, envelope, fake, budget, quarantine, assisted_review   [NEW]
  tools/                   models, registry, fake, quarantine                            [NEW]
  evals/                   runner (smoke), contract_runner, rubric, comparison           [comparison NEW]
  integrations/chaseos/    ChaseOSProposalAdapter (inactive, dispatch raises)
  runtime_adapters/        5 x 6-line stubs — UNCHANGED, still scaffold_only
  source_card.py           canonical builder; metadata + paragraph-aware extraction
  cli.py                   6 commands
```

### 3.2 CLI commands

`source-card` · `skill-gate` · `chaseos-native-source-card` · `visual-eval` · `contract-eval` · `review`

### 3.3 Running things

```bash
# Full suite (WSL venv is Linux-native; Windows python cannot run it)
wsl -- bash -c "cd <repo-root> && PYTHONPATH=src .venv/bin/python -m pytest -q"

# Fast path for pure-python tests (works on Windows python, seconds not minutes)
PYTHONPATH=src python -m pytest tests/test_tool_capability_boundary.py -q

# Contract evals (non-zero exit on any failure)
PYTHONPATH=src .venv/bin/python -m chaser_agent.cli contract-eval \
  --input evals/datasets/contract/layer0_contract_seed.jsonl \
  --out logs/runs/contract-eval-results.jsonl

# Regenerate the test matrix after any dataset change
PYTHONPATH=src .venv/bin/python -m scripts.export_test_matrix
```

### 3.4 Layer status

| # | Layer | Status |
|---|---|---|
| 0 | Behaviour contract | **Enforced** — contract evals + independence tests |
| 1 | Operator | Immutable review records + `review` CLI; **zero reviews recorded** |
| 2 | Studio/Interface | Not started (CLI only, by design) |
| 3 | Capture/Intake | File intake; metadata separated; research-intake config |
| 4 | Source Package | Domain-neutral, profile-driven, `source_metadata` field |
| 5 | Workspace | Not started |
| 6 | Retrieval/Evidence | Evidence links + lexical memory retrieval (no embeddings) |
| 7 | Summary Intelligence | Deterministic + model-assisted path behind the fake |
| 8 | Memory | Append-only SQLite FSM, governance-gated promotion |
| 9 | Knowledge map | uuid5 identity, provenance queries |
| 10 | Runtime/AOR | Not started (deliberate) |
| 11 | Harness | 177 tests, contract runner, comparison rig, matrix export |
| 12 | Provider router | Boundary complete; **no live provider** |
| 13 | Tool/MCP | Boundary complete; **no execution** |
| 14 | Browser/Computer-use | Metadata-only evaluator |
| 15 | Runtime memory/repair | Not started |
| 16 | Governance | Local backend + audit records |
| 17 | Skill/Forge | `skill-gate` unchanged |

---

## 4. What was built, and why it is shaped that way

### 4.1 Standalone independence enforcement — `tests/test_standalone_independence.py`

The redesign's Principle 1/2 (core must never import ChaseOS, a provider SDK, an MCP runtime, or a browser runtime) held **by luck** — nothing tested it. Now an AST scan parses every module in `core`, `workflows`, `governance`, `reviews`, `memory`, `knowledge` and fails on any forbidden import, including `chaser_agent.integrations`, `chaser_agent.providers`, and `chaser_agent.tools` so the core cannot reach an adapter indirectly.

**Mutation-verified:** appending `import openai` to `memory/lifecycle.py` produced 2 failures; file restored, diff clean.

### 4.2 Provider boundary — `src/chaser_agent/providers/`

Built as a **fake only**. Rationale: boundary tests need an adversary that misbehaves *reliably*; a real provider is nondeterministic and mostly well-behaved, so such tests would pass by luck.

- **`envelope.py`** — `build_request()` fails closed on disallowed privacy class or credential-shaped strings. `ALLOWED_PURPOSES` deliberately excludes any authority-shaped purpose (no "promote memory", no "approve"). `describe_envelope()` is the privacy dry run.
- **`fake.py`** — scriptable by reply / sequence / purpose-map; records every request; 6 named `HOSTILE_PAYLOADS`.
- **`quarantine.py`** — output is `untrusted_model_output`, zero authority. **`MERGE_WRITABLE_KEYS` whitelist + `assert_only_whitelisted_changes()`** performs a full recursive artifact diff; anything outside three keys raises `GovernanceDrift`. Pattern detection is advisory only.
- **`budget.py`** — `BudgetPolicy` ceilings refused **pre-send** (tests assert `adapter.request_count == 0`); `enforce_deadline()` converts a late reply to `timeout`; usage ledger with estimates flagged as estimates.
- **`assisted_review.py`** — deterministic artifacts built first; provider output strictly additive; any failure leaves the baseline standing with `degraded: true`.

**Key design principle to preserve:** *blacklists are enumerable and therefore incomplete; whitelists are complete.* A 400-payload seeded fuzzer asserts the invariant across shapes nobody scripted.

### 4.3 Comparison rig — `src/chaser_agent/evals/comparison.py`

Scores model-assisted output against its deterministic baseline: statement-level grounding, unsupported statements, uncertainty preservation, governance violations, composite `quality_score` (forced to 0 on violation or unusable output).

**The calibration is the deliverable:** `test_ruler_ranks_known_quality_outputs_in_the_correct_order` scripts three outputs of *known* quality (grounded > partial > fabricated) and requires correct ranking. A fake cannot say whether a real model is good; it can prove the ruler measures what it claims.

### 4.4 Tool/MCP boundary — `src/chaser_agent/tools/`

**Three gates, all required:** registered → granted → in scope. **Registration is not permission.**

- `PERMITTED_SIDE_EFFECTS_P0_1 = {"read_only"}`; `local_write` / `external_effect` are declarable but never authorizable.
- Path scopes **normalised before comparison** (blocks `docs/../../etc/passwd`); URL scopes match host **and** path (blocks `blog.cloudflare.com.evil.test`).
- **Denied calls do not consume call budget** — otherwise hostile input could exhaust a legitimate allowance by triggering refusals.
- `plan()` stamps `executed: False` with an all-false authority block; `execute()` raises `execution_not_implemented`.
- Results quarantined as `untrusted_tool_output`; 6 `HOSTILE_TOOL_RESULTS`.

**Load-bearing test:** `test_hostile_tool_output_cannot_widen_a_scope` — tool output cannot influence tool authority.

### 4.5 Contract eval coverage

30 cases (5 per family × 6 families), 154 assertions. **Mutation-verified:** flipping `review_status` to `reviewed` in the builder failed 13/30 across four families.

All cases carry `provenance.review_status = pending_operator_review`. **Coverage is a count, not operator-reviewed golden data.**

---

## 5. Defects found and fixed (the recurring pattern)

Five instances of the same failure mode: **a stated guarantee with nothing enforcing it.**

1. **`must_not_include` was never read** by the eval runner — every golden row declared forbidden phrases and nothing checked them. (`6b9dbeb`, earlier session)
2. **Core-purity rule unenforced** — held by luck. (`da2d175`)
3. **Blacklist containment** — pattern matching is enumerable; replaced with structural whitelist. (`5639771`)
4. **Tests froze a seed size** — `len(rows) == 6` meant *improving* coverage read as a regression. Rewritten to assert the property. (`cf5d28e`)
5. **Metadata + fragments extracted as claims** — found by operator review of a real run; `URL:`/`Title:`/`Published:`/`Authors:` became claims, and line-by-line splitting turned wrapped sentences into fragments (`"Operators must review"`). (`aee51b4`)

**Carry this forward:** when a doc states a guarantee, grep for the test that would fail if it were violated. If there isn't one, the guarantee is decorative.

### Corrections made during the session (for accuracy of the record)

- A reported "contract-eval exits 0 on failure" bug was **not real** — it was shell escaping in a nested `wsl.exe -- bash -c` call. Verified `EXIT_CODE=1` against a deliberately failing case.
- A reported 23-minute suite regression was **mostly contention** with concurrent background jobs; the clean figure was 3:42, later 64s after memoising `current_repo_commit` (`d055d8b`).

---

## 6. Outstanding work — the queue

### 6.1 BLOCKING — operator review (only Chase can do this)

**Nothing downstream should proceed until this is done.** There are **zero** reviews recorded; `~/.chaser-agent/` does not exist yet.

Three runs await scoring:

```text
logs/runs/source-card-20260812T181101z-...-3e1cfd2a61   ai_engineering_research_review
logs/runs/source-card-20260812T181106z-...-e98acffcd9   general_source_review
logs/runs/source-card-20260812T181110z-toy-website-design-note-cc07795c57   website_design_review
```

Working packet (untracked): `logs/review/2026-08-12-operator-review-packet.md`

Command per run:

```bash
PYTHONPATH=src python -m chaser_agent.cli review <RUN_FOLDER> \
  --reviewer-id chase \
  --source-fidelity-score 0-3 \
  --inference-separation-score 0-3 \
  --uncertainty-handling-score 0-3 \
  --action-usefulness-score 0-3 \
  --memory-safety-score 0-3 \
  --decision pass|needs_revision|fail \
  --reviewer-notes "..."
```

Scale: 0 unusable · 1 weak · 2 acceptable · 3 strong. Proposed (not enforced) bar: total ≥12/15, no dimension below 2.

**Known open question for the reviewer:** run 1 claim `"It is evidence that agent harnesses are becoming economic actors that need:"` is a fragment ending in a colon before a list. Arguably still a fidelity defect. Score it honestly.

**After scores exist, the analysis owed is:** extraction precision (substantive claims ÷ total), score distribution and weakest dimension, mapping of findings onto contract-eval families, an honest statement that 3 runs is a seed not coverage, and a live-provider recommendation.

### 6.2 Recommended next build passes (bounded, in order)

| # | Pass | Scope | Gate |
|---|---|---|---|
| 1 | Wire an authorized read-only tool plan into a review run | Tool-sourced evidence carries provenance + trust grade; still no execution | None |
| 2 | Source-trust grading | Admiralty two-axis (reliability A–F × credibility 1–6) on evidence snippets per `docs/research/2026-08-02-chaseos-instance-eval-thesis.md` §5.1 | None |
| 3 | Product-quality eval set | Built from §6.1 review records | **Needs §6.1** |
| 4 | Live provider (read-only, budgeted) | First real inference behind the existing envelope/budget/quarantine | **Operator approval — authority expansion** |
| 5 | Real read-only MCP client | Behind the existing capability contract | **Operator approval** |
| 6 | ChaseOS wiring (Session 5) | Activate the adapter | Needs §8 decisions 15–16 |

### 6.3 Deferred / not started

Layers 2, 5, 10, 14 (runtime), 15. Embeddings/RAG. Fine-tuning. FastAPI or any server. `runtime_adapters/` are still 6-line stubs and were **not** touched — note the new `providers/` package supersedes `openai_provider.py`/`ollama.py` conceptually; a future pass should either migrate or delete those stubs deliberately (do not silently delete — §9).

---

## 7. Environment, risks, and gotchas

### 7.1 Concurrent agents — read this before committing

Codex/Hermes write to this repo **live**. During this session, commit `3f86f8d` was created by another process from this session's working tree **without** the accompanying test fixes, leaving `HEAD` red (tests asserted `len(rows) == 6` against a 30-case dataset). It was repaired by `cf5d28e`.

**Always:** `git fetch` → `git status` → `git log --oneline -5` before assuming state, and commit your own work promptly rather than leaving it in the working tree.

### 7.2 Untracked by design

- `logs/review/2026-08-12-operator-review-packet.md` — working document; references local-only run folders.
- `logs/runs/**` — git-ignored.
- `stash@{0}` (`pre-layer0-reset-uncommitted-work-2026-06-09`) — **preserved, do not apply or drop without operator approval.**

### 7.3 Environment

- `.venv` is **WSL/Linux-native** with broken symlinks from Windows. Run pytest through WSL.
- Windows `python` (3.11) *can* run pure-python tests and the CLI — vastly faster for iteration; use it for quick loops, WSL for the full suite.
- Cross-boundary `/mnt/c` I/O is the main cost. `current_repo_commit` is memoised because it shelled out to git once per run log.
- Storage gate at last check: **13.18 GiB free, 5.54%** — passes the 10 GiB / 5% bar but narrowly. Re-check before heavy work.
- Bash heredocs with complex unicode/quoting have failed repeatedly in this environment; prefer writing files directly.

---

## 8. Open operator decisions (unchanged — do not invent answers)

The redesign brief's §24 list stands. Most relevant now:

1. Final pass threshold for review scores (currently `ReviewPolicyProposal`, `enforced=False`).
2. Whether locally promoted memory is publicly called "canonical memory" or "approved durable memory".
3. Whether AI-engineering research becomes the first official domain pack.
4. First provider to evaluate.
5. First read-only tool capability to enable for real.
6. Sandbox architecture before any execution.
7. Sync semantics between standalone memory and ChaseOS memory.
8. Conflict resolution when standalone and ChaseOS memory disagree.
9. Export/deletion policy for local memory; retention policy for review records.
10. Whether `runtime_adapters/` stubs are migrated into `providers/`/`tools/` or removed.

---

## 9. Forbidden without explicit operator approval

- Merging this branch to `main`; force-pushing; rewriting history.
- Applying or dropping `stash@{0}`.
- Activating a live provider, real tool execution, MCP runtime, browser/computer use, or any network call.
- Any fine-tuning, LoRA, PEFT, or training.
- ChaseOS canonical mutation or approval consumption.
- Committing `.env`, databases, run outputs, or private data.
- Deleting compatibility shims or stub modules without evidence they are unused.
- Inventing operator review scores. **The operator's judgement is the dataset; fabricating it destroys the only ground truth the system has.**

---

## 10. Key documents

| Topic | Path |
|---|---|
| As-built map | `docs/01_Product/Chaser-Agent-As-Built-Map.md` |
| Standalone vs ChaseOS | `docs/01_Product/Chaser-Agent-Standalone-vs-ChaseOS-Architecture.md` |
| Contract eval design | `docs/02_Evals/Chaser-Agent-Contract-Eval-Design.md` |
| Current test matrix | `docs/02_Evals/Chaser-Agent-Current-Test-Matrix.md` |
| Operator review workflow | `docs/02_Evals/Chaser-Agent-Operator-Review-Workflow.md` |
| Workflow profiles | `docs/03_Summary_Intelligence/Chaser-Agent-Workflow-Profile-Architecture.md` |
| Standalone memory | `docs/04_Memory/Chaser-Agent-Standalone-Memory-Architecture.md` |
| Knowledge map | `docs/04_Memory/Chaser-Agent-Knowledge-Map-Architecture.md` |
| Provider boundary | `docs/05_Runtime_Adapters/Chaser-Agent-Provider-Boundary-And-Fake-Adapter.md` |
| ChaseOS optional integration | `docs/05_Runtime_Adapters/Chaser-Agent-ChaseOS-Optional-Integration.md` |
| Tool capability boundary | `docs/06_Skills/Chaser-Agent-Tool-Capability-Boundary.md` |
| Instance eval thesis + source grading | `docs/research/2026-08-02-chaseos-instance-eval-thesis.md` |

Build logs for every pass are in `logs/build/2026-08-*`.

---

## 11. Suggested first actions for the next Codex session

1. `git fetch && git status && git log --oneline -5` — confirm nobody moved the branch.
2. Run the full suite; confirm **177 passed** before changing anything. If it is red, repair before building (see §7.1).
3. Ask the operator whether §6.1 review scores exist yet. If not, that is the blocking item and nothing in §6.2 rows 3–6 should start.
4. If proceeding with a build pass, take §6.2 row 1 or 2 — both are unblocked and need no new authority.
5. Write a build log under `logs/build/` for whatever you do, matching the existing format.
