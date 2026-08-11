# Chaser agent — Standalone-First Master Redesign Handover

**Document type:** Product-direction reset, architecture decision packet, repository-reconciliation brief, and bounded Codex implementation handover  
**Audience:** Codex working inside the local `Chaser-Agent` repository, the human operator, and ChatGPT architecture review  
**Project:** Chaser agent  
**Current maturity:** P0 / pre-alpha deterministic harness foundation  
**Execution posture:** redesign on a review branch; do not merge automatically to `main`

---

# 0. How Codex Must Use This Document

Read this entire document before changing any file.

This handover records an approved product-direction change:

> **Chaser agent is standalone-first and ChaseOS-enhanced.**

A user must be able to install, run, review, remember, and evolve Chaser agent without installing ChaseOS.

ChaseOS remains the strongest integrated control plane for:

- shared governance;
- cross-runtime orchestration;
- shared canonical state;
- policy enforcement;
- approvals;
- agent routing;
- cross-project memory;
- enterprise-style coordination.

However, ChaseOS is now an **optional adapter and deployment mode**, rather than a hard dependency of the Chaser agent core.

This pass is allowed to redesign the current P0 architecture around that decision and implement the bounded standalone foundations defined below.

This pass is **not** permission to:

- build the entire future V1 runtime;
- expose a public service;
- activate live model providers;
- execute external tools;
- browse or control a computer;
- fine-tune a model;
- modify ChaseOS canonical state;
- merge automatically to `main`.

Codex must:

1. inspect the local repository rather than assume GitHub `main` is the full truth;
2. preserve existing branches, stashes, ignored artifacts, logs, and uncommitted work;
3. reconcile architecture and documentation drift;
4. create logical commits on a review branch;
5. push the review branch;
6. stop at human decision gates;
7. return a detailed final handover.

Use the product name **“Chaser agent”** consistently in prose.

---

# 1. Approved Product Definition

## 1.1 Canonical Product Statement

Chaser agent is an open-source, local-first agent harness and runtime architecture for turning goals, source material, and bounded tasks into evidence-linked, reviewable work.

It should:

- preserve what a source actually says;
- separate source claims from agent inference;
- represent uncertainty and contradiction;
- propose safe next actions without silently executing them;
- remember human-approved information;
- retrieve relevant reviewed memory during future work;
- evolve memory through review, correction, staleness, dispute, archive, and supersession;
- curate a provenance-first knowledge map;
- improve through human feedback;
- improve through reviewed examples;
- improve through evals;
- improve through skills;
- improve through retrieval;
- support later model adaptation only after data and eval readiness;
- operate independently;
- integrate optionally with ChaseOS.

The concise public narrative is:

> **Chaser agent is an open-source, standalone-first, local-first agent harness that turns goals and sources into evidence-linked work, learns from human review, preserves approved memory, and curates a user-owned knowledge map. It works independently and becomes more powerful when connected to ChaseOS.**

## 1.2 Core Utility

The core utility of Chaser agent is not tied to one business, media workflow, website, trading system, or content engine.

The core should:

1. receive a goal, question, source, or bounded task;
2. classify the input and its trust/privacy state;
3. create source-grounded claims and evidence;
4. separate source truth from agent inference;
5. represent uncertainty;
6. identify contradictions or state when contradiction detection was not performed;
7. propose safe next actions;
8. retrieve relevant reviewed memory;
9. propose new memory candidates;
10. let the human approve, revise, reject, or promote;
11. persist approved local memory;
12. connect sources, claims, decisions, tasks, memories, skills, and runs in a knowledge map;
13. later route approved work to models, tools, runtimes, or ChaseOS.

## 1.3 What Chaser agent Is Not

Chaser agent is not currently:

- a foundation model;
- a production autonomous operator;
- a finished personal AI;
- a media-generation agent;
- a website-design agent;
- a trading executor;
- a public FastAPI service;
- a live provider router;
- a full RAG implementation;
- a live MCP/tool registry;
- a browser or computer-use runtime;
- an automatic canonical-memory owner;
- a fine-tuning pipeline;
- a complete implementation of all 17 architecture layers.

The project may eventually support these capabilities as governed modules, but none defines the core identity.

## 1.4 Open-Source and Licence Position

The repository uses the MIT licence.

The independent Chaser agent core must remain:

- free to use;
- self-hostable;
- modifiable;
- redistributable;
- extensible;
- suitable as a reusable agent-harness architecture;
- usable by people who do not use ChaseOS.

Do not introduce a proprietary dependency into the core.

Any future:

- hosted service;
- enterprise policy pack;
- managed connector;
- premium provider;
- commercial extension;
- proprietary ChaseOS product layer

must remain separable from the MIT-licensed core.

Those commercial concerns are outside this pass.

---

# 2. Why the Scope Is Changing

The previous architecture correctly protected users from:

- silent memory promotion;
- authority escalation;
- canonical-state mutation;
- unreviewed action execution.

However, its wording treated ChaseOS as the only possible owner of durable truth and memory.

That prevents Chaser agent from being a genuinely independent open-source architecture.

The revised model is **deployment-scoped**.

## 2.1 Standalone Mode

In standalone mode:

- Chaser agent runs without ChaseOS installed;
- the human operator is the approval authority;
- local governance rules protect the runtime;
- local reviewed memory can become approved durable local state;
- a local knowledge map stores provenance and relationships;
- local review decisions are persisted;
- no output promotes itself;
- no action executes without a defined permission and approval path;
- state remains user-owned;
- the user can export or remove their state.

## 2.2 ChaseOS-Integrated Mode

In ChaseOS-integrated mode:

- Chaser agent keeps the same core interfaces;
- approved proposals may be handed to the ChaseOS Gate;
- ChaseOS may own shared or cross-project canonical truth;
- ChaseOS may provide runtime routing;
- ChaseOS may provide policy;
- ChaseOS may provide permissions;
- ChaseOS may provide approval workflows;
- ChaseOS may provide shared memory;
- ChaseOS may provide graph intelligence;
- ChaseOS may provide cross-runtime orchestration;
- Chaser agent does not duplicate ChaseOS authority;
- integration remains additive and optional.

## 2.3 Canonical-State Rule

Canonical state is deployment-scoped:

```text
Standalone deployment:
human-approved local durable state

ChaseOS deployment:
ChaseOS-governed shared canonical state
```

In both deployments:

```text
generated output != canonical truth
memory candidate != memory
action candidate != action
review packet != approval
integration packet != dispatch
agent confidence != authority
```

## 2.4 Independence Rule

The Chaser agent core must not import ChaseOS.

Use dependency inversion:

```text
Chaser agent core
    ↓ interfaces / protocols
Standalone local adapters     Optional ChaseOS adapters
```

ChaseOS integration must be additive.

---

# 3. Current As-Built Truth to Preserve

The latest truth-state audit established the following.

## 3.1 Implemented Today

Chaser agent currently has:

- a deterministic local Source Card Harness V0;
- CLI-driven local execution;
- local file intake;
- source-card generation;
- claims-table generation;
- evidence-snippet generation;
- uncertainty-label generation;
- action-candidate generation;
- memory-candidate generation;
- human-review packet generation;
- run-log generation;
- optional ChaseOS-shaped review-packet output without live dispatch;
- 33 deterministic tests in the audited local state;
- seven public golden JSONL files with three rows each;
- one local Layer 0 contract JSONL file with six rows;
- an artifact-field contract runner;
- a bounded SkillGate;
- a metadata-only visual-completion evaluator;
- public arXiv ingestion;
- a config-only weekly research dry-run lane;
- inactive provider/runtime/MCP stubs;
- architecture documentation;
- eval documentation;
- memory documentation;
- skill documentation;
- research documentation;
- maths documentation;
- university-learning documentation.

## 3.2 Not Implemented Today

The audit found no production implementation of:

- a provider router;
- a FastAPI service;
- a web UI;
- semantic RAG;
- embedding retrieval;
- a vector database;
- a live MCP/tool registry;
- a general agent planning/execution loop;
- a sandbox;
- browser/computer use;
- a standalone canonical-memory database;
- review writeback;
- broad general-domain source intelligence;
- model training;
- fine-tuning;
- LoRA;
- PEFT;
- live ChaseOS approval consumption.

## 3.3 What the Deterministic Harness Proves

It proves:

- the package runs;
- safe local input can enter a bounded pipeline;
- expected artifact files can be written;
- source claims and agent inference have separate fields;
- memory outputs can be marked candidate-only;
- action outputs can be marked approval-required;
- selected negative-authority fields can be tested;
- runs are repeatable;
- JSONL syntax is valid;
- selected invariants pass;
- no provider is required for the current path.

It does not prove:

- semantic intelligence;
- human usefulness;
- strong summaries;
- broad prompt-injection resistance;
- calibrated uncertainty;
- general-domain behaviour;
- reliable redaction;
- private-data safety;
- production security;
- readiness for training;
- live provider governance;
- live tool governance;
- safe autonomous execution.

## 3.4 Primary-Builder Defect

The current primary builder accepts arbitrary text but contains hard-coded website-design behaviour:

- design keywords;
- design-specific uncertainty messages;
- design-specific inference text;
- design-specific action candidates;
- design-specific memory candidates.

A generic-looking interface therefore behaves like a website-design reviewer.

That defect must be repaired.

## 3.5 Current Repository-State Risk

The latest audit reported:

- a Codex branch rather than `main`;
- inherited tracked modifications;
- inherited untracked implementation/docs/data;
- local-only ignored run/research artifacts;
- an existing stash that must not be applied or deleted automatically;
- remote `main` behind parts of the local working tree;
- a storage warning that must be checked before heavy work.

Codex must re-verify all of this before editing.

Do not assume the state is unchanged.

---

# 4. Approved Architecture Principles

## Principle 1 — Standalone-First

The core package must run without ChaseOS.

No core module may require a ChaseOS import.

## Principle 2 — ChaseOS Integration Through Interfaces

ChaseOS-specific behaviour belongs behind optional adapters.

The core depends on protocols, not on ChaseOS.

## Principle 3 — Human-Governed Promotion

The system may create candidates.

A human-approved governance backend controls promotion.

No generated output may approve itself.

## Principle 4 — Domain-Neutral Core

Website design, media creation, trading, business research, university learning, and other domains belong in workflow profiles or skill packs.

None may be hard-coded into the default core.

## Principle 5 — Evidence and Provenance Before Fluent Prose

The system must make it easy to answer:

- where did this claim come from?
- which source supports it?
- what was inferred?
- what is uncertain?
- what conflicts?
- which source or memory influenced this output?
- who reviewed it?
- what decision was made?
- what changed later?
- what was superseded?

## Principle 6 — Memory Is Not Model Training

Memory changes available context and state.

Fine-tuning changes model weights.

Do not confuse them.

## Principle 7 — Deterministic Foundations Before Live Intelligence

Keep the deterministic harness as:

- a reference implementation;
- a predictable baseline;
- a test oracle;
- a fallback mode;
- an auditable comparison point.

Introduce models later through provider-neutral interfaces.

## Principle 8 — Eval-Driven, but Behaviour-Defined First

Evals measure an approved behaviour contract.

JSONL files and passing syntax checks are not product proof.

## Principle 9 — Least Authority

A profile, skill, model, provider, or adapter does not grant permission.

Authority is:

- explicit;
- scoped;
- revocable;
- logged;
- reviewable.

## Principle 10 — User-Owned Local State

Standalone users own:

- their database;
- their memories;
- their review records;
- their knowledge map;
- their exports;
- their configuration.

## Principle 11 — Profiles Do Not Grant Permissions

A workflow profile can shape analysis.

It cannot grant tools, network access, credentials, or execution authority.

## Principle 12 — No Silent State Mutation

Original run artifacts must remain immutable.

Corrections, reviews, promotions, and supersessions must create new records.

---

# 5. Target P0.1 Architecture

This pass should produce a coherent **P0.1 standalone core**.

P0.1 is not the full flagship runtime.

P0.1 should include:

1. domain-neutral source-review core;
2. workflow profiles;
3. persisted human-review decisions;
4. local governance backend;
5. local memory lifecycle;
6. local provenance-first knowledge map;
7. simple local memory retrieval;
8. optional ChaseOS adapter boundary;
9. exact test-matrix export;
10. repository reconciliation;
11. documentation reconciliation;
12. a clean review branch.

P0.1 must remain:

- CLI-first;
- local-library first;
- provider-free;
- tool-free;
- browser-free;
- model-training-free;
- safe for public-toy test data;
- deterministic where practical;
- human-governed.

---

# 6. Target Package Boundaries

Adapt this layout to the existing codebase where necessary, but preserve the architectural separation.

```text
src/chaser_agent/
  core/
    source_review.py
    models.py
    ids.py
    policies.py

  workflows/
    protocols.py
    general_source_review.py
    ai_engineering_research_review.py
    website_design_review.py

  governance/
    protocols.py
    local.py

  reviews/
    models.py
    store.py
    service.py

  memory/
    protocols.py
    models.py
    lifecycle.py
    sqlite_store.py
    retrieval.py

  knowledge/
    models.py
    sqlite_graph.py
    service.py

  integrations/
    chaseos/
      adapter.py
      models.py

  runtime_adapters/
    ...existing inactive stubs...

  cli.py
```

Codex may preserve compatibility shims while migrating, but module ownership must become clear.

## 6.1 Required Protocols

Create or formalise:

```text
GovernanceBackend
ReviewStore
MemoryStore
KnowledgeMapStore
WorkflowProfile
```

Leave these future protocols inactive or stubbed:

```text
ProviderAdapter
ToolRegistry
RuntimeAdapter
Sandbox
```

## 6.2 Dependency Rule

```text
core -> protocols
local adapters -> protocols
ChaseOS adapter -> protocols
```

Forbidden:

```text
core -> ChaseOS
core -> live provider SDK
core -> MCP runtime
core -> browser runtime
```

## 6.3 Installation Rule

A clean Chaser agent installation must be able to:

- import the core;
- run the deterministic source-review path;
- create local review state;
- create local memory state;
- create local knowledge-map state

without ChaseOS installed.

---

# 7. Standalone and ChaseOS Architecture Diagram

```mermaid
flowchart LR
    U[Human operator] --> CA[Chaser agent core]

    CA --> P[Workflow profile]
    CA --> R[Review store]
    CA --> M[Memory store]
    CA --> K[Knowledge map]
    CA --> G[GovernanceBackend]

    G --> LG[Local standalone governance]
    G -. optional .-> CG[ChaseOS adapter]
    CG -. optional .-> COS[ChaseOS Gate and control plane]

    LG --> LC[Local approved durable state]
    COS --> SC[Shared ChaseOS canonical state]

    CA -. no automatic promotion .-> LC
    CA -. no automatic promotion .-> SC
```

Core rule:

```text
The same Chaser agent core works in both deployments.
Only governance, storage, and integration adapters change.
```

---

# 8. Layer-by-Layer Redesign Map

Layer 0 remains the constitution but must support standalone and ChaseOS-integrated deployments.

| Layer | Standalone responsibility | ChaseOS enhancement | P0.1 work |
|---|---|---|---|
| 0. Behaviour Contract | Allowed/forbidden behaviour, local human authority, no silent promotion | Shared policy and Gate authority | Rewrite for deployment modes; retain negative authority |
| 1. User / Operator | Run, inspect, score, correct, accept/reject, promote approved local memory | Shared identity, approval queues, projects | Implement persisted operator review |
| 2. Studio / Interface | Future local CLI/UI, review queue, memory browser | Embedded ChaseOS Studio | CLI only; document future interface |
| 3. Capture / Intake | Local files, trust/privacy classification, source metadata | Governed connectors | Formalise safe local intake |
| 4. Source Package | Claims, evidence, inference, uncertainty, actions, memory candidates | Shared source intelligence | Repair domain-neutral builder |
| 5. Workspace / Collection | Future project/source grouping | ChaseOS workspaces | Scope/tags only; no full workspace system |
| 6. Retrieval / Evidence | Local reviewed-memory retrieval and evidence links | Shared graph/RAG | Lexical/tag retrieval only |
| 7. Summary Intelligence | Profile-aware source review | Shared providers/skills/policy | General, AI research, website profiles |
| 8. Memory Consolidation | Reviewed local memory lifecycle | Shared ChaseOS memory sync | SQLite memory store, no embeddings |
| 9. Knowledge Map | Local provenance graph | ChaseOS graph intelligence | SQLite nodes/edges and queries |
| 10. Agent Runtime / AOR | Future bounded execution loop | Runtime routing/orchestration | Docs only; no autonomy |
| 11. Harness | Tests, review, replay, logs, evals | Shared observability | Review persistence and test export |
| 12. Provider Router | Future provider-neutral inference | Central provider policy | Remain inactive/stubbed |
| 13. Tool / MCP | Future capability registry | Shared tool governance | No execution |
| 14. Browser / Computer Use | Future bounded worker | Governed runtime evidence | Metadata-only evaluator remains |
| 15. Runtime Memory / Repair | Future checkpoint/retry/rollback | Cross-runtime repair | Docs only |
| 16. Governance / Approval | Local human governance and promotion | ChaseOS Gate adapter | Local governance protocol + optional adapter |
| 17. Extension / Skill / Forge | Profiles, skills, provenance, quarantine | ChaseOS Forge/shared registry | Profiles as safe specialisation; retain SkillGate |

---

# 9. Workflow-Profile Architecture

## 9.1 Why Profiles Are Required

The current core mixes generic extraction with website-design policy.

Workflow profiles separate domain-specific behaviour from the core.

## 9.2 Required Profile Contract

Each profile must declare:

```text
profile_id
display_name
version
purpose
allowed_input_types
claim_hints
uncertainty_rules
action_policy
memory_policy
forbidden_actions
required_review_dimensions
tags
```

A profile may:

- guide deterministic claim selection;
- add labelled domain inference;
- add domain-specific uncertainty checks;
- propose domain-specific review actions;
- propose memory candidates.

A profile may not:

- execute an action;
- promote memory;
- call a provider;
- grant tool permission;
- modify governance;
- bypass review;
- increase runtime authority.

## 9.3 Required P0.1 Profiles

### `general_source_review`

This is the default profile.

Requirements:

- source-neutral;
- no website language unless present in the source;
- no media language unless present in the source;
- no trading language unless present in the source;
- conservative claims;
- generic uncertainty;
- safe review actions;
- memory defaults to empty unless durability is clear;
- no assumption that every source should create memory.

### `ai_engineering_research_review`

Requirements:

- identify technical and research claims;
- distinguish reported results from Chaser agent implications;
- identify methodology limitations;
- identify eval limitations;
- identify missing baselines;
- identify implementation questions;
- propose architecture questions;
- propose eval candidates;
- propose RFC candidates;
- preserve citation and provenance;
- never treat a paper claim as production truth.

### `website_design_review`

Requirements:

- preserve useful design-review concerns;
- hierarchy;
- contrast;
- spacing;
- readability;
- restraint;
- user intent;
- visual-context requirements;
- avoid over-decoration;
- request screenshots or visual proof when needed.

This profile is optional and explicit.

## 9.4 Future Profiles — Not Required in This Pass

```text
trading_research_review
business_research_review
university_learning_review
media_creation_review
cybersecurity_research_review
software_repository_review
```

Media creation must not be the default profile or define core behaviour.

---

# 10. Primary-Builder Repair

## 10.1 Remove Domain-Specific Constants from Core

The domain-neutral builder must not contain:

- `DESIGN_KEYWORDS`;
- fixed website uncertainty text;
- fixed website inference text;
- fixed website action candidates;
- fixed website memory candidates;
- media-generation assumptions.

Move valid design policy into `website_design_review`.

## 10.2 Generic Deterministic Extraction

The core may remain transparent and deterministic, but it should:

- normalise text;
- preserve headings separately;
- avoid treating Markdown headings as factual claims;
- split sentences and paragraphs;
- create evidence snippets;
- generate neutral claim candidates;
- attach source locations;
- use conservative confidence values;
- preserve source order;
- call the selected profile after generic extraction.

## 10.3 Claim Types

Support neutral claim types such as:

```text
fact
reported_result
constraint
requirement
recommendation
opinion
definition
decision
unknown
```

Do not assign `fact` merely because a sentence appeared in the source.

The claim type describes what the source presented, not whether it is globally true.

## 10.4 Contradiction Handling

P0.1 does not need advanced semantic contradiction detection.

Support:

- explicit contradiction records from profile rules;
- obvious deterministic markers where safe;
- direct opposing phrases where reliably identifiable;
- otherwise `not_evaluated`;
- or `none_detected_by_deterministic_rules`.

Do not claim that no contradiction exists merely because deterministic rules did not find one.

## 10.5 Duplicate Builder Reconciliation

The audit found multiple `build_source_card` implementations.

Codex must:

1. map every call site;
2. select one canonical core builder;
3. retain a compatibility shim where required;
4. mark deprecated paths;
5. migrate tests deliberately;
6. document ownership;
7. ensure the smoke runner and contract runner do not unknowingly test different products.

Do not silently delete compatibility code without evidence.

---

# 11. Human-Review Workflow

## 11.1 Why This Is the Highest-Value Human Contribution Now

The current review packet leaves every score as `null`.

The harness creates a review opportunity but has not captured product-quality evidence.

Human review now becomes an explicit part of:

- the product;
- the eval system;
- the memory system;
- the future training-data lifecycle.

## 11.2 Required Review Record

```text
review_id
run_id
reviewer_id
reviewed_at
source_fidelity_score
inference_separation_score
uncertainty_handling_score
action_usefulness_score
memory_safety_score
decision
reviewer_notes
corrected_claims
corrected_inferences
accepted_action_ids
rejected_action_ids
accepted_memory_ids
rejected_memory_ids
```

## 11.3 Score Meanings

```text
0 = incorrect, unsafe, or unusable
1 = weak; major revision needed
2 = acceptable; meaningful improvement remains
3 = strong and useful
```

## 11.4 Decisions

```text
pass
needs_revision
fail
```

## 11.5 Proposed Initial Pass Rule

Document this as a configurable proposal pending operator confirmation:

```text
total score >= 12 / 15
no dimension below 2
no critical safety failure
```

Do not hard-code this permanently without making it configurable.

## 11.6 Review CLI

Add a local flow such as:

```text
chaser-agent review <run-folder-or-run-id>
```

It should:

- load the original source;
- load the generated artifacts;
- display the relevant material;
- collect scores;
- collect reviewer notes;
- collect corrected claims;
- collect corrected inferences;
- collect accepted/rejected actions;
- collect accepted/rejected memory candidates;
- write an immutable review record;
- update the local review store;
- create reviewed memory candidates when selected;
- never auto-promote memory;
- never silently mutate original run artifacts.

## 11.7 Review Data and Future Training

Review records may later become:

- contract-eval cases;
- regression cases;
- strong-output examples;
- weak-output examples;
- error-taxonomy examples;
- privacy-cleared training candidates.

They do not become training data automatically.

---

# 12. Standalone Memory Architecture

## 12.1 Memory Categories

### Working Memory

Current-run or current-session context.

It may be temporary.

### Episodic Memory

Reviewed records of:

- prior runs;
- previous decisions;
- outcomes;
- operator feedback;
- project events.

### Semantic Memory

Reviewed durable:

- facts;
- preferences;
- concepts;
- definitions;
- project truths;
- operator constraints.

### Procedural Memory

Reviewed:

- skills;
- workflows;
- operating instructions;
- task procedures.

### Runtime/Repair Memory

Future records of:

- failures;
- retries;
- repair attempts;
- rollback;
- adapter behaviour;
- runtime incidents.

Runtime/repair memory is not an active execution requirement for P0.1.

## 12.2 Memory Lifecycle

```text
raw
-> candidate
-> reviewed
-> promoted
-> stale
-> disputed
-> archived
-> rejected
```

Rules:

- a run may create a candidate;
- review may accept or reject a candidate;
- only a governance backend may promote;
- promoted memory retains provenance;
- stale memory remains visible;
- disputed memory remains visible;
- supersession creates a link;
- nothing is silently overwritten;
- promotion must identify the approving reviewer.

## 12.3 Minimum Memory Schema

```text
memory_id
memory_type
content
status
scope
privacy_class
stability
confidence
source_refs
claim_refs
run_id
created_at
reviewed_at
reviewer_id
promoted_at
supersedes
tags
metadata_json
```

## 12.4 Local Persistence

Use Python standard-library SQLite.

Default location:

```text
~/.chaser-agent/chaser-agent.db
```

Allow a configurable path without requiring `.env`.

Tests must use temporary directories.

The database must not be created inside or committed to the public repository by default.

## 12.5 Retrieval for P0.1

Implement simple retrieval using:

- scope;
- memory type;
- tags;
- lexical term matching;
- recency;
- status.

Do not add embeddings yet.

Retrieved memory must be shown separately from source claims.

Every inference influenced by memory should reference the relevant memory IDs.

## 12.6 Memory Feedback

Allow the operator to mark retrieved memory as:

```text
useful
irrelevant
stale
disputed
```

Persist these as review or feedback records.

## 12.7 Promotion in Standalone Mode

Standalone promotion means:

- a candidate was reviewed;
- the operator accepted it;
- local governance allowed the transition;
- provenance was preserved;
- the promoted record became approved durable local state.

It does not mean the statement is globally or objectively true.

---

# 13. Knowledge-Map Architecture

## 13.1 Purpose

The knowledge map allows Chaser agent to evolve from isolated outputs into a traceable system of:

- sources;
- claims;
- evidence;
- inferences;
- concepts;
- decisions;
- actions;
- memories;
- workflows;
- runs;
- skills;
- projects.

It is a relationship index.

It is not a replacement for:

- source files;
- review records;
- memory records;
- run artifacts.

## 13.2 Initial Node Types

```text
source
claim
inference
concept
decision
action
memory
workflow
run
project
skill
agent
tool
```

P0.1 only needs working support for:

```text
source
claim
inference
decision
action
memory
workflow
run
```

## 13.3 Initial Edge Types

```text
derived_from
supported_by
contradicts
inferred_from
relates_to
applies_to
proposed_by
approved_by
rejected_by
supersedes
generated_in
used_by
reviewed_in
```

## 13.4 Node Schema

```text
node_id
node_type
label
content_ref
scope
privacy_class
created_at
metadata_json
```

## 13.5 Edge Schema

```text
edge_id
from_node_id
to_node_id
edge_type
created_at
run_id
review_id
metadata_json
```

## 13.6 Deterministic Identity

Use stable hashes or namespace UUIDs derived from:

- node or edge type;
- source identity;
- run identity;
- content identity;
- scope.

Avoid random IDs where stable identity is required.

## 13.7 Required P0.1 Queries

Support:

- get node;
- list neighbours;
- list evidence supporting a claim;
- list claims derived from a source;
- list memories derived from a source;
- list decisions created by a review;
- list items superseded by a memory;
- list graph entries created by a run;
- trace memory back to source and evidence.

Use SQLite, not an external graph database.

---

# 14. Standalone Governance Backend

## 14.1 Governance Protocol

The governance backend must answer:

```text
Can this candidate be reviewed?
Can this memory be promoted?
Can this action be executed?
Who approved it?
What policy applies?
What audit record results?
```

## 14.2 Local Governance

For P0.1:

- the human operator is the authority;
- local configuration defines review policy;
- local configuration defines promotion policy;
- no external side effects are enabled;
- local memory promotion is allowed only from reviewed candidates;
- every promotion creates an audit record;
- invalid lifecycle transitions are rejected.

## 14.3 Action Policy

P0.1 may propose actions such as:

- inspect a source;
- compare sources;
- request missing evidence;
- create an eval candidate;
- create a documentation candidate;
- create a bounded task candidate;
- propose a memory candidate.

P0.1 may not execute:

- public posts;
- messages;
- payments;
- trades;
- deployments;
- account changes;
- credential operations;
- destructive file changes;
- external tool calls.

## 14.4 Optional ChaseOS Adapter

Create an optional adapter that:

- converts Chaser agent proposals into ChaseOS-shaped packets;
- does not introduce ChaseOS imports into the core;
- does not dispatch live work in P0.1;
- remains explicitly inactive;
- documents where ChaseOS Gate consumption would happen later.

---

# 15. Current Tests, Visible Values, and Eventual Training Data

## 15.1 Verified Test State from the Audit

```text
33 tests passed
7 golden JSONL files x 3 rows
1 Layer 0 contract file x 6 rows
```

## 15.2 Public Golden Files

```text
action_extraction_eval.jsonl
citation_grounding_eval.jsonl
memory_candidate_eval.jsonl
source_card_summary_eval.jsonl
trading_research_workflow_eval.jsonl
visual_completion_eval.jsonl
website_design_workflow_eval.jsonl
```

## 15.3 Common Rubric Weights

Six public text-seed files use:

```text
claim_recall: 0.4
citation_grounding: 0.3
uncertainty: 0.2
brevity: 0.1
```

These are weights, not achieved scores.

## 15.4 Current Seed Values

### Source-Card Summary

```text
source_card_001
input:
A system should keep raw source text separate from reviewed memory.

must include:
- raw source text
- reviewed memory

must not include:
- automatic promotion
```

```text
source_card_002
input:
Roadmap updates should be suggestions only and never automatic promotion.

must include:
- suggestions only
- automatic promotion
```

```text
source_card_003
input:
A feature needs an eval, a failure mode, and a regression check before it is real.

must include:
- eval
- regression check

must not include:
- automatic promotion
```

### Action Extraction

```text
action_001
must include:
- reviewed source card
```

```text
action_002
must include:
- validate JSONL
```

```text
action_003
must include:
- label uncertainty
```

### Citation Grounding

```text
citation_001
must include:
- Evidence
```

```text
citation_002
must include:
- contrast checks
```

```text
citation_003
must include:
- automatic canonical writes
```

### Memory Candidates

```text
memory_001
must include:
- private datasets
```

```text
memory_002
must include:
- review before promotion
```

```text
memory_003
must include:
- stale memory
```

### Trading Research

```text
trade_001
must include:
- market data source
- uncertainty
```

```text
trade_002
must include:
- TradingView
- unverified data
```

```text
trade_003
must include:
- provenance
```

### Website Design

```text
web_001
must include:
- contrast readable
- subtle
```

```text
web_002
must include:
- visual noise
```

```text
web_003
must include:
- visual context
```

### Visual Completion

```text
screenshot-only-export
-> screenshot alone must not prove completion
```

```text
export-with-file-and-content-proof
-> screenshot + file existence + content/schema proof
```

```text
failed-form-submit
-> validation-error screenshot should classify as failed
```

## 15.5 Layer 0 Contract Families

```text
no_auto_promotion
injection_resistance
claim_evidence_integrity
uncertainty_honesty
action_boundary
authority_stamps
```

The six local rows were pending operator review in the audit.

## 15.6 Exact Test-Matrix Export

Create:

```text
scripts/export_test_matrix.py
docs/02_Evals/Chaser-Agent-Current-Test-Matrix.md
```

The generated report must show:

- dataset;
- row ID;
- task;
- input;
- expected includes;
- forbidden output;
- rubric or weights;
- execution path;
- automated result;
- maturity category;
- operator-review status;
- exact local contract assertions.

Use honest maturity labels:

```text
smoke
schema
contract_seed
visual_evidence
operator_reviewed
product_quality
regression
held_out
training_candidate
```

Unreviewed seeds must never be labelled product-quality.

## 15.7 Data Lifecycle Before Fine-Tuning

```text
raw run
-> human review
-> corrected example
-> privacy classification
-> accepted eval/regression example
-> repeated failure pattern
-> provider/model baseline comparison
-> training decision
-> train/validation/test split
-> fine-tuning experiment
-> held-out evaluation
```

Fine-tuning must wait.

A future planning threshold might be 100–200 high-quality reviewed examples for one stable workflow, but:

- quality;
- privacy;
- coverage;
- consistency;
- error diversity

matter more than raw count.

---

# 16. Maths and University-Module Integration

Update learning documents so each concept points to real Chaser agent code.

## 16.1 P0.1 Concepts

### Sets and Functions

Used for:

- state sets;
- allowed transitions;
- profile policies;
- action allow/deny lists;
- memory-status sets.

### Boolean Logic

Used for:

- promotion predicates;
- review pass/fail;
- contract assertions;
- permission rules.

### Finite-State Machines

Used for:

- memory lifecycle;
- review lifecycle;
- candidate-to-promotion transitions.

### Graph Theory

Used for:

- knowledge-map nodes;
- edges;
- traversal;
- neighbourhood queries;
- provenance chains.

### Database Design

Used for:

- SQLite schemas;
- primary keys;
- foreign keys;
- constraints;
- indexes;
- normalisation;
- transactions.

## 16.2 Eval Concepts

### Precision

Of the items Chaser agent proposed, how many were correct or useful?

### Recall

Of the important source items, how many were captured?

### F1

A balance between precision and recall.

### Confusion Matrix

Useful for:

- safe versus unsafe;
- grounded versus ungrounded;
- promote versus reject;
- complete versus incomplete.

### Confidence Intervals

Used later to decide whether improvements are likely reliable.

### A/B Testing

Compare:

- profile versions;
- prompt versions;
- skill versions;
- harness versions;
- model versions.

## 16.3 RAG Concepts — Later

- vectors;
- matrices;
- dot product;
- cosine similarity;
- ranking metrics;
- recall at K;
- mean reciprocal rank;
- retrieval freshness.

## 16.4 Fine-Tuning Concepts — Later

- distributions;
- entropy;
- cross-entropy;
- loss functions;
- gradient descent;
- generalisation;
- overfitting;
- data leakage;
- LoRA;
- PEFT.

---

# 17. Repository Reconciliation and Safety Plan

## 17.1 Preflight Commands

Run and record:

```text
git status --short --branch
git branch --show-current
git log --oneline -20
git remote -v
git stash list
git diff --stat
git diff --check
storage/free-space check
full pytest suite
golden and contract JSONL validation
```

## 17.2 Preserve All Current Work

Codex must:

- create a safety patch or branch;
- preserve the existing stash;
- not apply the stash automatically;
- not delete the stash automatically;
- not delete ignored run artifacts;
- not delete ignored research artifacts;
- not publish ignored artifacts;
- not reset inherited work.

## 17.3 Working Branch

Create and work on:

```text
codex/standalone-first-memory-realignment
```

Do not work directly on `main`.

## 17.4 File Classification

Classify every dirty or untracked file as:

```text
KEEP_COMMIT
GENERATED_IGNORE
ARCHIVE
REJECT_WITH_REASON
NEEDS_OPERATOR_DECISION
```

Include the classification in the final handover.

## 17.5 Storage Gate

Before heavy tests or commits, require:

```text
at least 10 GiB free
and
at least 5% free
```

If the gate fails:

- stop;
- report;
- do not delete files without operator approval.

## 17.6 Secret and Privacy Checks

At minimum:

- confirm no real `.env` is staged;
- confirm databases are ignored;
- confirm run outputs are ignored;
- inspect staged files for tokens;
- inspect staged files for API keys;
- inspect staged files for private keys;
- inspect staged files for credentials;
- inspect staged files for absolute private paths;
- do not commit raw research feeds;
- do not commit copied private source material;
- do not commit operator-private review data.

---

# 18. Implementation Phases and Checkpoints

## Phase A — Truth-State Reconciliation

### Deliverables

- verified branch/worktree/stash truth;
- safety backup;
- file classification;
- baseline test results;
- baseline JSONL results;
- clean working branch.

### Stop Condition

Stop if local work cannot be classified safely.

---

## Phase B — Product and Architecture Realignment

### Update

```text
README.md
START_HERE.md
NEXT_STEPS.md
HANDOVER.md
docs/00_START_HERE.md
docs/01_Product/Chaser-Agent-Layer-0-Behaviour-Contract.md
docs/01_Product/Chaser-Agent-Product-Thesis.md
docs/01_Product/Chaser-Agent-V0-Definition.md
docs/01_Product/Chaser-Agent-V0-Blueprint.md
docs/01_Product/Chaser-Agent-Roadmap.md
docs/01_Product/Chaser-Agent-17-Layer-Architecture.md
```

### Create

```text
docs/01_Product/Chaser-Agent-Standalone-vs-ChaseOS-Architecture.md
docs/01_Product/Chaser-Agent-Product-Narrative-and-Utility.md
```

### Checkpoint

All public wording must be:

```text
standalone-first
ChaseOS-enhanced
open-source
domain-neutral
human-governed
```

---

## Phase C — Core Interface Boundary

### Deliverables

- `GovernanceBackend` protocol;
- `ReviewStore` protocol;
- `MemoryStore` protocol;
- `KnowledgeMapStore` protocol;
- `WorkflowProfile` protocol;
- local implementations;
- optional inactive ChaseOS adapter;
- proof the core imports and runs without ChaseOS.

### Checkpoint

Architecture-import tests pass.

---

## Phase D — Builder Generalisation

### Deliverables

- `general_source_review` default profile;
- `ai_engineering_research_review` profile;
- `website_design_review` profile;
- domain-neutral builder;
- heading-safe claim extraction;
- no media/design boilerplate in core;
- duplicate builder ownership resolved.

### Generate and Compare

```text
general source
AI-engineering source
website-design source
```

### Stop Condition

Stop if profile leakage occurs.

---

## Phase E — Human-Review Writeback

### Deliverables

- review models;
- review store;
- CLI review command;
- immutable review record;
- original artifacts preserved;
- accepted/rejected action decisions;
- accepted/rejected memory decisions.

### Operator Gate

Example review records must be inspected before promotion logic is treated as accepted.

---

## Phase F — Standalone Memory

### Deliverables

- SQLite schema;
- candidate lifecycle;
- review lifecycle;
- promote lifecycle;
- reject lifecycle;
- stale lifecycle;
- dispute lifecycle;
- archive lifecycle;
- provenance;
- lexical/tag retrieval;
- database outside repository;
- temporary-database tests;
- no auto-promotion.

### Operator Gate

Review the local durable-state terminology and transition policy.

---

## Phase G — Knowledge Map

### Deliverables

- node table;
- edge table;
- deterministic identifiers;
- source links;
- claim links;
- evidence links;
- inference links;
- action links;
- review links;
- memory links;
- run links;
- basic queries;
- provenance tests.

### Demonstration

```text
source
-> claim
-> evidence
-> inference
-> review
-> approved memory
```

---

## Phase H — Test Visibility

### Deliverables

- test-matrix exporter;
- current matrix Markdown;
- exact contract assertions;
- maturity labels;
- operator-review status.

### Checkpoint

A human can see all current values without opening raw JSONL manually.

---

## Phase I — Documentation, Testing, and Commits

### Deliverables

- updated learning docs;
- updated architecture docs;
- complete tests;
- JSONL validation;
- secret/privacy checks;
- storage check;
- logical commits;
- pushed review branch;
- final handover.

Do not merge.

---

# 19. Required Tests

## 19.1 Standalone Independence

- package runs without ChaseOS installed;
- core modules contain no ChaseOS import;
- optional ChaseOS adapter remains inactive;
- standalone mode creates review state;
- standalone mode persists review state;
- standalone mode creates memory state;
- standalone mode persists memory state.

## 19.2 Profile Isolation

- general profile is default;
- general profile emits no design boilerplate;
- general profile emits no media boilerplate;
- AI-research profile produces research-oriented inference;
- website profile produces design-oriented inference only when selected;
- profiles cannot grant permission;
- profiles cannot auto-promote memory.

## 19.3 Source Integrity

- headings are not treated as factual claims;
- claims remain evidence-linked;
- source claims remain separate from inference;
- uncertainty remains honest;
- no automatic promotion;
- memory influence is referenced explicitly.

## 19.4 Review Flow

- scores validate 0–3;
- decisions validate allowed values;
- review records are immutable;
- original artifacts remain unchanged;
- accepted IDs resolve;
- rejected IDs resolve;
- review alone does not promote memory;
- reviewer identity is preserved.

## 19.5 Memory

- candidate persists;
- reviewed candidate promotes only through governance;
- rejected memory cannot promote;
- stale transition works;
- disputed transition works;
- archive transition works;
- invalid transitions fail clearly;
- promoted memory survives process restart;
- database is outside repository by default;
- retrieval respects status;
- retrieval respects scope;
- retrieval respects privacy.

## 19.6 Knowledge Map

- deterministic node IDs;
- deterministic edge IDs where appropriate;
- provenance links resolve;
- review links to decision;
- promoted memory links to source;
- promoted memory links to evidence;
- neighbours can be queried;
- run-created graph entries can be listed.

## 19.7 Test Matrix

- exporter reads real JSONL;
- all row IDs appear;
- rubric weights appear;
- local contract assertions appear;
- maturity labels are accurate;
- unreviewed rows are not called product-quality;
- output is reproducible.

## 19.8 Regression

- existing tests remain passing or are migrated with explanation;
- visual evaluator remains metadata-only;
- research intake remains a separate lane;
- no live provider activation;
- no tool activation;
- no browser activation;
- no model-training activation.

---

# 20. Documentation Requirements

Create or update the following.

## Product

```text
docs/01_Product/Chaser-Agent-Standalone-vs-ChaseOS-Architecture.md
docs/01_Product/Chaser-Agent-Product-Narrative-and-Utility.md
```

## Evals and Review

```text
docs/02_Evals/Chaser-Agent-Current-Test-Matrix.md
docs/02_Evals/Chaser-Agent-Operator-Review-Workflow.md
```

## Summary and Profiles

```text
docs/03_Summary_Intelligence/Chaser-Agent-Workflow-Profile-Architecture.md
```

## Memory and Knowledge

```text
docs/04_Memory/Chaser-Agent-Standalone-Memory-Architecture.md
docs/04_Memory/Chaser-Agent-Knowledge-Map-Architecture.md
```

## Integration

```text
docs/05_Runtime_Adapters/Chaser-Agent-ChaseOS-Optional-Integration.md
```

## Learning

Update:

```text
docs/08_Learning/AI-Engineering-Learning-Map.md
docs/08_Learning/Harness-Engineering-Glossary.md
docs/08_Learning/Maths-For-Chaser-Agent.md
docs/08_Learning/University-Module-Linkage.md
```

Explain each new technical term in plain English and connect it to real code.

---

# 21. Forbidden Scope

Do not implement:

- FastAPI;
- web UI;
- hosted deployment;
- live OpenAI;
- live Anthropic;
- live local-model inference;
- provider router;
- MCP execution;
- tool execution;
- browser/computer use;
- autonomous planner/executor loop;
- vector embeddings;
- vector database;
- fine-tuning;
- LoRA;
- PEFT;
- automatic skill optimisation;
- public posting;
- payments;
- trading execution;
- credential access;
- ChaseOS canonical mutation;
- automatic merge to `main`.

Do not let P0.1 become an uncontrolled V1 build.

---

# 22. Approved Commit Strategy

After each logical phase passes tests, Codex may create commits.

Suggested sequence:

```text
chore: reconcile Chaser agent local truth state

docs: realign Chaser agent as standalone-first and ChaseOS-enhanced

refactor: introduce domain-neutral source review profiles

feat: add standalone operator review persistence

feat: add standalone memory and knowledge-map foundations

test: export current eval matrix and verify standalone boundaries

docs: update learning and architecture handover
```

Codex is approved to push:

```text
codex/standalone-first-memory-realignment
```

Codex is not approved to:

- merge the branch;
- force push;
- rewrite public history;
- delete the old stash;
- apply the old stash;
- commit ignored generated artifacts;
- commit private data.

---

# 23. Definition of Done

## Product

- README says standalone-first and ChaseOS-enhanced;
- product is not described as media-specific;
- product is not described as website-specific;
- MIT/open-source independence is clear;
- ChaseOS origins remain acknowledged;
- ChaseOS integration benefits remain acknowledged.

## Architecture

- core has no ChaseOS dependency;
- optional ChaseOS adapter exists behind interfaces;
- local governance works independently;
- builder is profile-driven;
- SQLite state lives outside the repository.

## Behaviour

- general profile is default;
- no design boilerplate remains in core;
- no media boilerplate remains in core;
- AI-engineering profile is isolated;
- website profile is isolated;
- claims remain distinct from inference;
- uncertainty remains distinct;
- actions remain candidates;
- memory remains governed.

## Human Review

- operator scores persist;
- operator corrections persist;
- review records are immutable;
- original run artifacts remain unchanged;
- review does not auto-promote.

## Memory

- reviewed local memory persists;
- lifecycle transitions are enforced;
- provenance is retained;
- retrieval works without embeddings;
- database lives outside the repository.

## Knowledge Map

- nodes persist;
- edges persist;
- provenance queries work;
- source-to-memory trace is demonstrable.

## Evals

- current test values are exported;
- exact contract assertions are visible;
- maturity labels are honest;
- all tests pass;
- all JSONL validation passes.

## Repository

- dirty work is reconciled or explicitly classified;
- existing stash remains preserved;
- generated/private state remains ignored;
- review branch is pushed;
- branch is clean after commits;
- no automatic merge occurs.

---

# 24. Operator Decisions That Remain Open

Codex must not invent final answers for these.

1. Final pass threshold for human-review scores.
2. Exact public data definition.
3. Exact scrubbed data definition.
4. Exact internal-safe data definition.
5. Exact private data definition.
6. Exact secret data definition.
7. Whether locally promoted memory is called “canonical memory” or “approved durable memory” in public UX.
8. Whether AI-engineering research becomes the first official domain pack.
9. Exact profile package/discovery mechanism after P0.1.
10. Whether FastAPI belongs in V1 or V1.5.
11. First provider to evaluate later.
12. First RAG corpus.
13. First read-only tool capability.
14. Sandbox architecture before execution.
15. Synchronisation semantics between standalone memory and ChaseOS.
16. Conflict resolution when standalone and ChaseOS memory disagree.
17. Export and deletion policy for local memory.
18. Retention policy for review records.

Create a decision log for any additional unresolved item.

---

# 25. Required Final Codex Handover

Return a large Markdown handover containing:

1. starting branch;
2. starting commit;
3. working-tree truth;
4. stash truth;
5. storage truth;
6. baseline test results;
7. file classification;
8. branch created;
9. files created;
10. files modified;
11. architecture changes;
12. proof the core runs without ChaseOS;
13. optional ChaseOS-adapter proof;
14. proof builder hard-coding was removed;
15. workflow profiles created;
16. three cross-domain output paths;
17. review-flow demonstration;
18. memory-lifecycle demonstration;
19. knowledge-map demonstration;
20. test-matrix path;
21. final test results;
22. JSONL results;
23. secret/privacy checks;
24. logical commits;
25. pushed branch;
26. remaining risks;
27. operator decisions required;
28. exact recommended next pass.

Also include:

```text
git status --short --branch
git log --oneline -10
git stash list
```

Do not provide a vague summary.

---

# 26. Recommended Later Pass — Do Not Start Automatically

The likely next bounded pass after operator review is:

> **Provider-neutral fake model adapter + reviewed AI-engineering research workflow + first product-quality eval set**

That later pass would:

- preserve the deterministic baseline;
- introduce a fake provider interface;
- exercise provider envelopes without network calls;
- use reviewed AI-engineering examples;
- compare deterministic output against model-assisted output;
- measure source fidelity;
- measure inference quality;
- measure uncertainty;
- add no live provider until data and eval policy are approved.

FastAPI, live providers, RAG embeddings, tools, browser use, autonomous loops, and fine-tuning remain later.

---

# 27. Codex Execution Instruction

Execute this handover as a bounded P0.1 redesign.

Work carefully.

Preserve current state.

Use tests.

Stop at operator decision gates.

Make logical commits.

Push only the approved review branch.

Return the complete handover.

Do not expand scope.
