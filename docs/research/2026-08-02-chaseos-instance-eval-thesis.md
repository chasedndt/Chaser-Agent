# ChaseOS Instance Eval Thesis & Handover (2026-08-02)

**Status:** Chaser Agent research thesis, partially acted on and still pending Chase's review/expansion. Session 3 implemented the core artifact assertion runner plus one pending-review seed per initial Layer 0 family on 2026-08-08. Per-instance expansion and source-trust grading remain proposals.

## 0. Full context for the external assistant (read this first)

You are being asked to expand an eval-system design for **Chaser Agent**, a governed, review-first agent harness that runs as a configured runtime lane under **ChaseOS** (https://chaseos.ai) — a local-first, approval-bound AI operating system built around a governed knowledge graph. Chaser Agent's constitution ("Layer 0") requires: outputs are review artifacts, never canonical truth; no memory promotion, tool/provider calls, browsing, or public actions without explicit human approval; every run log proves what was NOT done (authority stamps like `provider_calls: none`).

**What exists and runs today (all deterministic, no LLM calls yet):**
- Source Card Harness V0: local text file → source card JSON separating source claims / agent inferences / uncertainty labels / action candidates / memory candidates + a human review packet. All stamped `pending_review` / `not_promoted`.
- ChaseOS-native handoff packet: wraps a source card with an allowlisted ChaseOS workflow label (mirrors ChaseOS's canonical registry), graph links, and authority proof.
- Skill gate: a candidate skill/prompt patch is only reviewable if it strictly improves a held-out score, preserves a protected "slow state" section, and stays within an 8-edit budget. Template for all future self-improvement.
- Visual completion evaluator: screenshot-only evidence can never prove task success; verified status needs visual + non-visual evidence; completion can never be self-marked.
- Eval runner v0: JSONL cases scored by text `must_include` / `must_not_include` (the latter enforced as of 2026-08-02) + uncertainty-label presence. 29 pytest tests green.
- Research intake: YAML-configured public-source scanning (arXiv + industry blogs) with a paper-scoring rubric (`ranking.yaml`) that weights evalability and penalizes hype (social-only source: −40).

**Eval maturity ladder:** smoke → schema → **contract (PARTIAL seed implementation)** → product-quality → training. Contract evals now assert on artifact *fields* (e.g. `promotion_status == "not_promoted"`, every action `requires_approval: true`), with each case tagged to the Layer 0 clause it enforces. One pending-review seed exists for each initial family: no-auto-promotion, injection resistance, claim/evidence integrity, uncertainty honesty, action boundary, and authority stamps. One case is wiring proof, not family coverage.

**ChaseOS instances this must serve** (§3): trading/markets research (no execution), social media brand growth (human-approved publishing only), app development with coding agents (credential safety), site ops / computer-use workflows (verified completion, self-improving workflow packs), research intake.

**Your task:** expand §3 (per-instance mistake inventories and eval cases), critique and strengthen §5 (source-trust grading), and answer §6. **Ground every substantive claim in cited, dated sources with URLs — prefer primary sources (standards, vendor docs, peer-reviewed work with code) over commentary, and apply §5's own ladder to your citations.** Uncited additions will be treated as suggestions, not evidence, when merged back.

## 1. Evidence base

- `https://chaseos.ai` homepage (full page text captured 2026-08-02).
- Canonical ChaseOS workflow registry: `chaseos_obsidian\b\s\runtime\workflows\registry\` (~40 workflows incl. strikezone_* trading family, siteops_execute, desktop_operate, browser_research, hermes_* review family).
- This repo's Layer 0 contract, eval docs, `research_intake/ranking.yaml`, Human Operator Rubric, social-publishing direction plan.
- Web research on source-grading frameworks (Admiralty/NATO 6x6, SIFT, lateral reading — links in §5).

## 2. What ChaseOS is (from its own public claims)

"One private command layer for your work, memory, agents, and execution" — a local-first, approval-bound, graph-backed operating system where chats, docs, repos, sources, decisions, approvals, agents, outputs, and logs form one governed knowledge graph. It names four problems: **scattered context, repeated re-briefing, untrusted automation, work that cannot compound.** It lists eight use cases: launch, research, content/brand systems, commerce, software development with agents, markets, business operations, personal OS. Chaser Agent appears on the site as a **configured runtime lane**.

**Thesis:** Chaser Agent's eval system should be organized around ChaseOS's four promise-breaks. Every eval family below is a way one of those four promises could fail — that is what makes an eval "true to the system" rather than generic.

| ChaseOS promise | Eval question |
|---|---|
| Connected context | Did the agent use/preserve lineage (source trails, evidence links)? |
| No re-briefing | Did outputs land as reusable, well-formed graph artifacts? |
| Trusted automation | Were authority stamps, approvals, scopes provably respected? |
| Compounding work | Did workflow packs/skills improve without regressing (skill-gate)? |

## 3. Per-instance eval theses

For each instance: role → most expensive mistake → top eval families (from `Chaser-Agent-Eval-Families.md`, extended).

### 3.1 Trading / markets (StrikeZone family)
- **Role:** research, thesis-building, signal separation; site claims "without execution claims"; execution disabled-by-default per Phase 9.
- **Most expensive mistake:** treating unverified market data as truth, or any path from analysis → order without human approval.
- **Evals:** data-provenance eval (every figure traceable to a named feed + timestamp); uncertainty honesty under conflicting signals; risk-boundary contract (no order/execution vocabulary in outputs marked complete); staleness eval (price/positioning claims must carry freshness labels).

### 3.2 Social media / brand growth (ChaseOS-Social, X pilot)
- **Most expensive mistake:** an unapproved public post, or a fabricated claim/anecdote published under a brand.
- **Evals:** exact-copy binding (published text hash == approved hash); public-safety source allowlist (private lanes/tokens/notifications never in candidates); media-proof contract (crop/legibility/private-content checks per `media_proof.v1`); voice eval (no invented first-person experience, no engagement bait) — the social-publishing plan's activation checklist is effectively an eval spec already.

### 3.3 App development with agents (Codex/Claude Code lanes)
- **Most expensive mistake (Chase's own pick):** credential exposure — keys committed, echoed into logs, or sent to a server — without immediate detection and a rotate-now escalation.
- **Evals:** secret-hygiene contract (outputs/diffs/logs never contain key-shaped strings; exposure ⇒ explicit `rotate_keys` escalation, never silence); diff-scope eval (changed files ⊆ declared scope); test-honesty eval (never report green without runnable proof — mirrors `attempted_unverified` from the visual evaluator).

### 3.4 Site ops / computer-use workflows (siteops_execute, desktop_operate, browser_research)
- **Most expensive mistake:** claiming a browser/desktop task "done" when the desired outcome didn't happen, or acting on an instruction embedded in a webpage (injection).
- **Evals:** completion-verification (visual + non-visual evidence, `visual_completion.py` is the seed); injection resistance (page/DOM text ordering the agent around must change nothing); scope containment (only declared surfaces touched); workflow-pack regression — this is the "self-growing system" Chase wants: each saved workflow gets replayable fixture cases, and skill-gate-style strict-improvement applies before any pack update.

### 3.5 Research intake (this repo's live lane)
- **Most expensive mistake:** a hyped/contaminated source driving an implementation decision.
- **Evals:** ranking.yaml penalty application; claim/evidence integrity; source-grading presence (§5); "silence when no meaningful evidence" (from the social plan — applies to research digests too).

### 3.6 Cross-cutting (every instance)
Injection resistance, authority stamps, no-auto-promotion, uncertainty honesty, action boundary — the six contract families from `Chaser-Agent-Contract-Eval-Design.md`. These run everywhere; the per-instance evals stack on top.

## 4. Hardening and "backwards testing" (Chase's requirement)

1. **Regression rows:** every real failure becomes a permanent JSONL row that must never pass again (Dataset Plan already names this class; it needs its first citizens).
2. **Adversarial/injection corpus:** a growing set of hostile source texts (instructions, fake approvals, authority claims, urgency) run against every artifact-producing command; assert zero field drift.
3. **Metamorphic tests:** transform an input in ways that must not change governance outcomes (reorder sentences, embed flattery, translate tone) and assert statuses/stamps are invariant.
4. **Replay verification:** rerun archived cases after every change (cheap because deterministic); diffs in outcomes must be explained or rejected — the skill-gate merge philosophy applied to the whole harness.

## 5. Source-trust ranking model

Existing asset: `research_intake/ranking.yaml` already scores *research papers* well (evalability weights + hype penalties, e.g. `hype_only_social_source: -40`). What's missing is a **general, per-claim grading** usable across all instances. Proposal:

**Adopt the Admiralty/NATO two-axis grade on every evidence snippet and source card:** source reliability A–F (track record of the *origin*) × information credibility 1–6 (corroboration/coherence of the *item*). The two axes are deliberately independent — reliable sources pass on bad items and vice versa. `trust_state: unreviewed` in the source card becomes structured: `source_reliability`, `info_credibility`, `corroboration_refs`.

### 5.1 How the two-axis grading works, exactly

**Axis 1 — source reliability (A–F): "how much has this *origin* earned our trust?"**

| Grade | Meaning | Example |
|---|---|---|
| A | Completely reliable — long verified track record | Official exchange data feed; a standard (RFC/CVE) |
| B | Usually reliable — strong record, minor doubts | Cloudflare engineering blog; major vendor advisory |
| C | Fairly reliable — right more often than not | Well-known practitioner blog |
| D | Not usually reliable | Anonymous forum account |
| E | Unreliable — record of being wrong/deceptive | Known hype/spam account |
| F | Cannot be judged — no track record yet | First contact with a new source |

**Axis 2 — information credibility (1–6): "how well does this *specific item* hold up, regardless of who said it?"**

| Grade | Meaning | Operational trigger |
|---|---|---|
| 1 | Confirmed — independent corroboration | 2+ independent sources or a primary artifact verifies it |
| 2 | Probably true — consistent, partly corroborated | 1 independent corroboration |
| 3 | Possibly true — plausible, uncorroborated | Coheres with known facts, no corroboration yet |
| 4 | Doubtful — tension with known facts | Contradicts something graded 1–2 |
| 5 | Improbable — contradicts confirmed facts | Directly refuted by a primary artifact |
| 6 | Cannot be judged | No basis either way |

A claim's grade is the pair, e.g. **B2** = usually-reliable source, probably-true item. The axes are independent on purpose: an A-source can emit a 5-item (Reuters mis-reports something), and a D-source can emit a 1-item (a random account posts a screenshot that checks out against the primary).

**Assignment mechanics for Chaser Agent (proposed):**

1. **Reliability is assigned per-origin, mostly rule-based:** a maintained `source_registry` maps origins to default grades via the §5 source-class ladder (primary artifact ⇒ A, official vendor docs ⇒ B, …, unknown ⇒ F). The registry is a reviewable file; grades change only through operator review, informed by a running track-record ledger (how often did this origin's items later grade 1–2 vs 4–5?). Maintaining that ledger is one of the flagged maths/learning tasks.
2. **Credibility is computed per-item at source-card build time:** count independent `corroboration_refs`, run contradiction checks against already-confirmed claims, apply the table's triggers. Deterministically computable today (corroboration counting); an LLM later improves contradiction detection behind the same field schema.
3. **Grades live on the artifacts:** each evidence snippet gets `source_reliability`, `info_credibility`, `corroboration_refs`; the source card aggregates the worst-case grade of the evidence supporting each claim (a claim is only as strong as its weakest necessary evidence).
4. **Policy consumes grades:** action candidates that depend on claims graded worse than B2 (configurable per instance) are automatically stamped `blocked_reason: insufficient_source_grade` until more corroboration or operator override; trading and social get stricter floors than research notes.
5. **Evals assert grading:** contract cases check grades exist, floors are enforced, F/6 items never silently support approved-looking actions, and grade fields are injection-immune (source text saying "this is A1 information" must not move a grade).

**Default source-class ladder (tune per domain):**
1. Primary artifacts (the repo/commit/contract/filing/dataset itself)
2. Official vendor/standards docs (vendor security advisories outrank all reporting *about* them)
3. Peer-reviewed / preprints with code & benchmarks (ranking.yaml already penalizes no-code/no-eval)
4. Established institutional journalism & respected practitioner blogs (Cloudflare-blog class)
5. Community discussion (signal for leads, never sole support for a claim)
6. Social/viral content (lead-generation only; `hype_only_social_source` penalty stands)

**Process rules to encode as agent behavior (and evals):**
- **Lateral reading:** verify a source by what *others* say about it, not its own self-presentation — fact-checker practice that outperforms reading deeply within the source.
- **SIFT** (Stop, Investigate the source, Find better coverage, Trace to original): "trace to original" becomes a hard rule — cite the primary, not the aggregator.
- **Corroboration floor:** any claim graded ≥ "acting on it" requires 2+ independent sources or 1 primary artifact; single-source claims stay `requires_review`.
- **Domain overrides:** trading (exchange/first-party data > all commentary; freshness dominates), security/app-dev (vendor advisory + CVE/NVD > blogs), social (only declared public-safe surfaces are sources at all).

## 6. Open questions for Chase (and prompts for ChatGPT expansion)

1. Per instance: what's the *second* most expensive mistake? (First ones are drafted above — confirm or replace.)
2. Which instances go live first? Eval-building order should follow activation order.
3. For siteops workflow packs: what does "improved" mean measurably (time, steps, error rate, approvals needed)? That metric is what skill-gate will enforce.
4. Ask ChatGPT to: expand §3 mistake inventories per instance; propose 5 concrete eval cases per family in §3; critique the §5 ladder and §5.1 mechanics for the trading and social domains specifically; propose grading UI/UX for the operator review packet; and **do its own sourced research** — find additional frameworks, standards, incident post-mortems, or benchmarks that would strengthen this harness, each with URL + publication date, graded against §5's own ladder.
5. Maths flag (Chase-led when reached): corroboration counting, grade aggregation, and pass-rate confidence live in `docs/08_Learning/Maths-For-Chaser-Agent.md` territory.

## 7. Web sources

- SANS, "Enhance Your Cyber Threat Intelligence with the Admiralty System" — https://www.sans.org/blog/enhance-your-cyber-threat-intelligence-with-the-admiralty-system
- Wikipedia, "Admiralty code" — https://en.wikipedia.org/wiki/Admiralty_code
- Blockint, "Critical review of the Admiralty Code" — https://www.blockint.nl/intel-analysis/critical-review-of-the-admiralty-code/
- CSU Fullerton LibGuides, "The SIFT Method" — https://libraryguides.fullerton.edu/c.php?g=855970&p=11102833
- Minnesota State Mankato, "Using Lateral Reading & SIFT" — https://libguides.mnsu.edu/sourcecredibility/lateralreading
- UChicago Library, "The SIFT Method" — https://guides.lib.uchicago.edu/c.php?g=1241077&p=9082322
- arXiv 2605.30802, "Multi-Agent AI Oracle Systems for Prediction Market Resolution" (learned source-ranking layer) — https://arxiv.org/pdf/2605.30802
