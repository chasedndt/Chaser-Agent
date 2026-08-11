# Chaser Agent As-Built Map

> Baseline note: this map records the pre-P0.1 implementation inherited on 2026-08-11. The approved standalone-first redesign is defined separately and must not be marked implemented until code/tests prove each P0.1 surface.

**Purpose:** one honest page mapping what actually exists in `src/` and `tests/` to the 17-layer architecture, so nobody (human or agent) confuses scaffold with product. Source-card behavior was verified against a live run on 2026-08-01. The Phase 2 contract seed was added on 2026-08-08; all 33 collected tests were covered by a native 27 + WSL 6 split recorded in that session's build log.

**Rule of thumb for reading this repo:** every module has two jobs — do a small deterministic thing, and *prove in its output that it did nothing else*. The negative-authority stamps (`provider_calls: none`, `approval_consumed: False`, …) are not boilerplate; they are the product.

## What is genuinely built (runs today, tested)

| Capability | Code | CLI | Layer(s) |
|---|---|---|---|
| Source Card Harness V0 | `source_card.py`, `run_artifacts.py` | `source-card` | 3 Capture, 4 Source Package, 7 Summary Intelligence, 11 Harness |
| ChaseOS-native handoff packet | `chaseos_native.py` | `chaseos-native-source-card` | 4, 7, 16 Governance (proposal side), ChaseOS bridge |
| Skill gate (SkillOpt-style) | `skillgate.py` | `skill-gate` | 17 Extension/Skill |
| Visual completion evaluator | `visual_completion.py` | `visual-eval` | 11 Harness, 14 Browser/Computer-use (eval contract only) |
| Eval runners (JSONL, deterministic) | `evals/runner.py`, `evals/contract_runner.py`, `evals/rubric.py` | `contract-eval` for Layer 0 seeds | 11 Harness |
| Research intake config | `research_intake/*.yaml` + config tests | (cron-driven dry run) | 3 Capture |

Key mechanics worth knowing cold:

- **Pipeline:** input file → `SourceInput` → `extract_claims` (keyword-based sentence selection) → claims + evidence + uncertainties + inferences + action candidates + memory candidates → 7 JSON artifacts + `run_log.json` in a unique `logs/runs/<run-id>/` folder. `mkdir(exist_ok=False)` makes runs collision-proof and immutable-by-convention.
- **Everything defaults to blocked:** `ChaserAgentConfig.allow_external_calls = False`, every artifact carries `review_status: pending_review`, `promotion_status: not_promoted`, `requires_approval: True`, and the `PROMOTION_WARNING`.
- **ChaseOS bridge shape:** `chaseos_native_packet.json` + `operator_handoff.md` with an allowlisted workflow label (`hermes_review_execute`, `hermes_watch`, `hermes_research_synthesis`, `hermes_skill_review`, `chaser_agent_review_packet` — trued up 2026-08-02 against the active entries in ChaseOS's canonical workflow registry), ChaseOS graph links, and a recommended `07_LOGS/Agent-Activity/` path *if* an operator promotes it. This is the wiring point for real ChaseOS integration.
- **Skill gate policy:** a candidate `SKILL.md` patch is reviewable only if it strictly improves a held-out score, preserves the `CHASER:SLOW-STATE` protected block, and stays within an edit budget of 8. Baseline is never mutated. This is the template for every future self-improvement loop.
- **Visual evaluator policy:** screenshot-only evidence can never prove success (`attempted_unverified`); verified-advisory requires visual + non-visual evidence with ≥2 supporting items; any failure signal wins. `can_mark_complete` is hardcoded `False`.
- **Contract-eval policy:** real source-card artifacts are evaluated in memory through structured paths; results include Layer 0 clause and assertion details. The six current cases are Codex-authored, `pending_operator_review` seeds—one per family is not coverage.

## What is honest placeholder (exists so tests/imports pass, carries no behavior)

- `runtime_adapters/*.py` — five 6-line classes returning `"scaffold_only"` with `allow_external_calls = False`. The real content for Layer 12/13 is in `docs/05_Runtime_Adapters/` notes. **This is the biggest gap between docs and code.**
- `summary/source_card.py`, `summary/extract_actions.py`, `summary/memory_candidates.py` — first-sentence/marker-keyword stubs kept for old smoke tests. The real V0 builder is top-level `source_card.py`; the duplicated `build_source_card` compat shim exists in both.
- `memory/consolidation.py` — the 8 memory states as a list plus a 2-transition function. The state *vocabulary* is real (it matches `docs/04_Memory/`); the machine is not.
- `harness/artifact_writer.py`, `harness/run_log.py` — superseded by `run_artifacts.py`.
- `evals/result_schema.py` — a re-import, nothing more.

## Layer-by-layer status (code truth, not doc claims)

| # | Layer | As-built status |
|---|---|---|
| 0 | Behaviour contract | Enforced culturally + via authority stamps and boundary tests; no single programmatic gate object yet |
| 1 | User/Operator | Review packets + checklists exist; scores are `None` placeholders — no capture loop for operator decisions |
| 2 | Studio/Interface | Nothing (CLI + files only, by design) |
| 3 | Capture/Intake | File-based intake real; research-intake config real; no live fetch |
| 4 | Source Package | **Most-built layer.** Full artifact set, deterministic, tested |
| 5 | Workspace/Collection | Nothing (single-source runs only) |
| 6 | Retrieval/Evidence | Evidence snippets with line locations; no retrieval/RAG |
| 7 | Summary Intelligence | Deterministic keyword extraction — the layer LLM intelligence will eventually replace, behind the same schema |
| 8 | Memory Consolidation | State names only; candidates emitted but nothing consumes them |
| 9 | Graph Intelligence | Graph *links* stamped in packets; no graph logic |
| 10 | Agent Runtime/AOR | Nothing (by design) |
| 11 | Harness | Real: run folders, run logs, smoke/schema JSONL runner, artifact-field contract runner, and tests. Eval maturity = PARTIAL contract seed; operator review and family coverage remain open |
| 12 | Provider/Model Router | Stubs only |
| 13 | Tool/MCP | Stub only + docs |
| 14 | Browser/Computer-use | Eval contract only (`visual_completion.py`); no runtime |
| 15 | Runtime Memory/Repair | Nothing |
| 16 | Governance/Gate | Proposal side real (packets, warnings, blocked-action lists); approval side lives in ChaseOS, not here |
| 17 | Extension/Skill/Forge | `skill-gate` real; sentinel preflight consumes ChaseOS Sentinel reports; no apply path |

## The three seams where the system will grow

1. **The intelligence seam (Layer 7):** `extract_claims` is where a model call will one day replace keyword matching. The artifact schema, uncertainty labels, and review packet stay identical — that is the point of building the harness first.
2. **The authority seam (Layers 12–14):** adapters go from `scaffold_only` to dry-run contracts with denial tests (roadmap Phase 6). No adapter gets live authority without an eval that proves it refuses out-of-contract calls.
3. **The learning seam (Layers 1 + 8 + 17):** operator review decisions (currently `None` scores) become labelled data → contract evals → skill-gate metrics. The human's judgement is the dataset.

## Known cleanups (low priority, tracked here so they aren't forgotten)

- Duplicate `build_source_card` in `source_card.py` and `summary/source_card.py`.
- `harness/` package superseded by `run_artifacts.py`.
- `build_source_card_artifacts` takes `input_path` but never uses it.
- `.venv` is WSL-native (Linux symlinks), and cross-boundary `/mnt/c` I/O is slow. Native Windows pytest works with `PYTHONPATH=<repo>\src`, except the older weekly-research config file assumes POSIX path-string keys and should be verified under WSL until that unrelated portability issue is fixed.
