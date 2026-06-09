# Chaser agent 17-Layer Architecture

Chaser agent borrows the ChaseOS layered worldview but implements only bounded, eval-backed product surfaces in this repository. The current build wedge is **source summary + eval harness**. The layers below describe the eventual map without claiming all layers are active.

## 1. User / Operator Layer

**Purpose:** Define the product concern for user / operator layer in a way that can be tested before authority expands.

**Plain-English explanation:** This layer answers: “what does Chaser agent need to know, produce, or reject at the user / operator layer?” It turns the ChaseOS concept into a bounded Chaser agent artifact, not a claim of full runtime implementation.

**What belongs here:** operator review rubric, checklists, approval/rejection examples.

**What does not belong here:** canonical ChaseOS mutation, hidden writeback, unreviewed private data, production provider/API calls, or broad autonomous execution.

**Current status:** planned.

**V0 artifact or module target:** `docs/02_Evals/Chaser-Agent-Human-Operator-Rubric.md`.

**First eval requirement:** create at least one golden or synthetic case showing the layer can distinguish grounded/reviewable output from unsafe, unsupported, or overbroad output.

**Authority risk:** overclaiming implementation status, silently promoting suggestions, treating a review artifact as canonical truth, or giving runtime/tool authority before eval evidence exists.

**Example workflow:** source or operator note enters the current source-summary wedge, produces a review packet, records uncertainty and evidence, and waits for human judgement before any downstream action.

**Later expansion:** after eval coverage exists, this layer can gain richer schemas, UI support, adapters, or automation while preserving ChaseOS Gate boundaries.

## 2. Studio / Interface Layer

**Purpose:** Define the product concern for studio / interface layer in a way that can be tested before authority expands.

**Plain-English explanation:** This layer answers: “what does Chaser agent need to know, produce, or reject at the studio / interface layer?” It turns the ChaseOS concept into a bounded Chaser agent artifact, not a claim of full runtime implementation.

**What belongs here:** future UI surfaces for review packets and run results.

**What does not belong here:** canonical ChaseOS mutation, hidden writeback, unreviewed private data, production provider/API calls, or broad autonomous execution.

**Current status:** later.

**V0 artifact or module target:** `docs/07_Research/ChaseOS-Website-Alignment.md`.

**First eval requirement:** create at least one golden or synthetic case showing the layer can distinguish grounded/reviewable output from unsafe, unsupported, or overbroad output.

**Authority risk:** overclaiming implementation status, silently promoting suggestions, treating a review artifact as canonical truth, or giving runtime/tool authority before eval evidence exists.

**Example workflow:** source or operator note enters the current source-summary wedge, produces a review packet, records uncertainty and evidence, and waits for human judgement before any downstream action.

**Later expansion:** after eval coverage exists, this layer can gain richer schemas, UI support, adapters, or automation while preserving ChaseOS Gate boundaries.

## 3. Capture / Intake Layer

**Purpose:** Define the product concern for capture / intake layer in a way that can be tested before authority expands.

**Plain-English explanation:** This layer answers: “what does Chaser agent need to know, produce, or reject at the capture / intake layer?” It turns the ChaseOS concept into a bounded Chaser agent artifact, not a claim of full runtime implementation.

**What belongs here:** safe source intake and source metadata classification.

**What does not belong here:** canonical ChaseOS mutation, hidden writeback, unreviewed private data, production provider/API calls, or broad autonomous execution.

**Current status:** planned.

**V0 artifact or module target:** `src/chaser_agent/summary/source_card.py`.

**First eval requirement:** create at least one golden or synthetic case showing the layer can distinguish grounded/reviewable output from unsafe, unsupported, or overbroad output.

**Authority risk:** overclaiming implementation status, silently promoting suggestions, treating a review artifact as canonical truth, or giving runtime/tool authority before eval evidence exists.

**Example workflow:** source or operator note enters the current source-summary wedge, produces a review packet, records uncertainty and evidence, and waits for human judgement before any downstream action.

**Later expansion:** after eval coverage exists, this layer can gain richer schemas, UI support, adapters, or automation while preserving ChaseOS Gate boundaries.

## 4. Source Package Layer

**Purpose:** Define the product concern for source package layer in a way that can be tested before authority expands.

**Plain-English explanation:** This layer answers: “what does Chaser agent need to know, produce, or reject at the source package layer?” It turns the ChaseOS concept into a bounded Chaser agent artifact, not a claim of full runtime implementation.

**What belongs here:** source-card packages with evidence, claims, and provenance.

**What does not belong here:** canonical ChaseOS mutation, hidden writeback, unreviewed private data, production provider/API calls, or broad autonomous execution.

**Current status:** scaffolded.

**V0 artifact or module target:** `docs/03_Summary_Intelligence/Chaser-Agent-Source-Card-Format.md`.

**First eval requirement:** create at least one golden or synthetic case showing the layer can distinguish grounded/reviewable output from unsafe, unsupported, or overbroad output.

**Authority risk:** overclaiming implementation status, silently promoting suggestions, treating a review artifact as canonical truth, or giving runtime/tool authority before eval evidence exists.

**Example workflow:** source or operator note enters the current source-summary wedge, produces a review packet, records uncertainty and evidence, and waits for human judgement before any downstream action.

**Later expansion:** after eval coverage exists, this layer can gain richer schemas, UI support, adapters, or automation while preserving ChaseOS Gate boundaries.

## 5. Workspace / Collection Layer

**Purpose:** Define the product concern for workspace / collection layer in a way that can be tested before authority expands.

**Plain-English explanation:** This layer answers: “what does Chaser agent need to know, produce, or reject at the workspace / collection layer?” It turns the ChaseOS concept into a bounded Chaser agent artifact, not a claim of full runtime implementation.

**What belongs here:** grouping sources into reviewable workspaces/collections.

**What does not belong here:** canonical ChaseOS mutation, hidden writeback, unreviewed private data, production provider/API calls, or broad autonomous execution.

**Current status:** planned.

**V0 artifact or module target:** `logs/runs/ plus future workspace schema`.

**First eval requirement:** create at least one golden or synthetic case showing the layer can distinguish grounded/reviewable output from unsafe, unsupported, or overbroad output.

**Authority risk:** overclaiming implementation status, silently promoting suggestions, treating a review artifact as canonical truth, or giving runtime/tool authority before eval evidence exists.

**Example workflow:** source or operator note enters the current source-summary wedge, produces a review packet, records uncertainty and evidence, and waits for human judgement before any downstream action.

**Later expansion:** after eval coverage exists, this layer can gain richer schemas, UI support, adapters, or automation while preserving ChaseOS Gate boundaries.

## 6. Retrieval / Evidence Layer

**Purpose:** Define the product concern for retrieval / evidence layer in a way that can be tested before authority expands.

**Plain-English explanation:** This layer answers: “what does Chaser agent need to know, produce, or reject at the retrieval / evidence layer?” It turns the ChaseOS concept into a bounded Chaser agent artifact, not a claim of full runtime implementation.

**What belongs here:** evidence snippets, citations, and retrieval provenance.

**What does not belong here:** canonical ChaseOS mutation, hidden writeback, unreviewed private data, production provider/API calls, or broad autonomous execution.

**Current status:** planned.

**V0 artifact or module target:** `evals/datasets/golden/citation_grounding_eval.jsonl`.

**First eval requirement:** create at least one golden or synthetic case showing the layer can distinguish grounded/reviewable output from unsafe, unsupported, or overbroad output.

**Authority risk:** overclaiming implementation status, silently promoting suggestions, treating a review artifact as canonical truth, or giving runtime/tool authority before eval evidence exists.

**Example workflow:** source or operator note enters the current source-summary wedge, produces a review packet, records uncertainty and evidence, and waits for human judgement before any downstream action.

**Later expansion:** after eval coverage exists, this layer can gain richer schemas, UI support, adapters, or automation while preserving ChaseOS Gate boundaries.

## 7. Summary Intelligence Layer

**Purpose:** Define the product concern for summary intelligence layer in a way that can be tested before authority expands.

**Plain-English explanation:** This layer answers: “what does Chaser agent need to know, produce, or reject at the summary intelligence layer?” It turns the ChaseOS concept into a bounded Chaser agent artifact, not a claim of full runtime implementation.

**What belongs here:** source summaries, actions, uncertainty, contradictions.

**What does not belong here:** canonical ChaseOS mutation, hidden writeback, unreviewed private data, production provider/API calls, or broad autonomous execution.

**Current status:** scaffolded.

**V0 artifact or module target:** `docs/03_Summary_Intelligence/Chaser-Agent-Source-Summary-Spec.md`.

**First eval requirement:** create at least one golden or synthetic case showing the layer can distinguish grounded/reviewable output from unsafe, unsupported, or overbroad output.

**Authority risk:** overclaiming implementation status, silently promoting suggestions, treating a review artifact as canonical truth, or giving runtime/tool authority before eval evidence exists.

**Example workflow:** source or operator note enters the current source-summary wedge, produces a review packet, records uncertainty and evidence, and waits for human judgement before any downstream action.

**Later expansion:** after eval coverage exists, this layer can gain richer schemas, UI support, adapters, or automation while preserving ChaseOS Gate boundaries.

## 8. Memory Consolidation Layer

**Purpose:** Define the product concern for memory consolidation layer in a way that can be tested before authority expands.

**Plain-English explanation:** This layer answers: “what does Chaser agent need to know, produce, or reject at the memory consolidation layer?” It turns the ChaseOS concept into a bounded Chaser agent artifact, not a claim of full runtime implementation.

**What belongs here:** memory candidates and review-state transitions.

**What does not belong here:** canonical ChaseOS mutation, hidden writeback, unreviewed private data, production provider/API calls, or broad autonomous execution.

**Current status:** planned.

**V0 artifact or module target:** `docs/04_Memory/Chaser-Agent-Memory-States.md`.

**First eval requirement:** create at least one golden or synthetic case showing the layer can distinguish grounded/reviewable output from unsafe, unsupported, or overbroad output.

**Authority risk:** overclaiming implementation status, silently promoting suggestions, treating a review artifact as canonical truth, or giving runtime/tool authority before eval evidence exists.

**Example workflow:** source or operator note enters the current source-summary wedge, produces a review packet, records uncertainty and evidence, and waits for human judgement before any downstream action.

**Later expansion:** after eval coverage exists, this layer can gain richer schemas, UI support, adapters, or automation while preserving ChaseOS Gate boundaries.

## 9. Graph Intelligence Layer

**Purpose:** Define the product concern for graph intelligence layer in a way that can be tested before authority expands.

**Plain-English explanation:** This layer answers: “what does Chaser agent need to know, produce, or reject at the graph intelligence layer?” It turns the ChaseOS concept into a bounded Chaser agent artifact, not a claim of full runtime implementation.

**What belongs here:** future relationship maps across sources, claims, and memories.

**What does not belong here:** canonical ChaseOS mutation, hidden writeback, unreviewed private data, production provider/API calls, or broad autonomous execution.

**Current status:** later.

**V0 artifact or module target:** `future graph schema proposal`.

**First eval requirement:** create at least one golden or synthetic case showing the layer can distinguish grounded/reviewable output from unsafe, unsupported, or overbroad output.

**Authority risk:** overclaiming implementation status, silently promoting suggestions, treating a review artifact as canonical truth, or giving runtime/tool authority before eval evidence exists.

**Example workflow:** source or operator note enters the current source-summary wedge, produces a review packet, records uncertainty and evidence, and waits for human judgement before any downstream action.

**Later expansion:** after eval coverage exists, this layer can gain richer schemas, UI support, adapters, or automation while preserving ChaseOS Gate boundaries.

## 10. Agent Runtime / AOR Layer

**Purpose:** Define the product concern for agent runtime / aor layer in a way that can be tested before authority expands.

**Plain-English explanation:** This layer answers: “what does Chaser agent need to know, produce, or reject at the agent runtime / aor layer?” It turns the ChaseOS concept into a bounded Chaser agent artifact, not a claim of full runtime implementation.

**What belongs here:** bounded runtime-adapter experiments and no-op contracts.

**What does not belong here:** canonical ChaseOS mutation, hidden writeback, unreviewed private data, production provider/API calls, or broad autonomous execution.

**Current status:** later.

**V0 artifact or module target:** `docs/05_Runtime_Adapters/`.

**First eval requirement:** create at least one golden or synthetic case showing the layer can distinguish grounded/reviewable output from unsafe, unsupported, or overbroad output.

**Authority risk:** overclaiming implementation status, silently promoting suggestions, treating a review artifact as canonical truth, or giving runtime/tool authority before eval evidence exists.

**Example workflow:** source or operator note enters the current source-summary wedge, produces a review packet, records uncertainty and evidence, and waits for human judgement before any downstream action.

**Later expansion:** after eval coverage exists, this layer can gain richer schemas, UI support, adapters, or automation while preserving ChaseOS Gate boundaries.

## 11. Harness Layer

**Purpose:** Define the product concern for harness layer in a way that can be tested before authority expands.

**Plain-English explanation:** This layer answers: “what does Chaser agent need to know, produce, or reject at the harness layer?” It turns the ChaseOS concept into a bounded Chaser agent artifact, not a claim of full runtime implementation.

**What belongs here:** deterministic eval runner, result logs, regression checks.

**What does not belong here:** canonical ChaseOS mutation, hidden writeback, unreviewed private data, production provider/API calls, or broad autonomous execution.

**Current status:** scaffolded.

**V0 artifact or module target:** `src/chaser_agent/evals/runner.py`.

**First eval requirement:** create at least one golden or synthetic case showing the layer can distinguish grounded/reviewable output from unsafe, unsupported, or overbroad output.

**Authority risk:** overclaiming implementation status, silently promoting suggestions, treating a review artifact as canonical truth, or giving runtime/tool authority before eval evidence exists.

**Example workflow:** source or operator note enters the current source-summary wedge, produces a review packet, records uncertainty and evidence, and waits for human judgement before any downstream action.

**Later expansion:** after eval coverage exists, this layer can gain richer schemas, UI support, adapters, or automation while preserving ChaseOS Gate boundaries.

## 12. Provider / Model Router Layer

**Purpose:** Define the product concern for provider / model router layer in a way that can be tested before authority expands.

**Plain-English explanation:** This layer answers: “what does Chaser agent need to know, produce, or reject at the provider / model router layer?” It turns the ChaseOS concept into a bounded Chaser agent artifact, not a claim of full runtime implementation.

**What belongs here:** future provider selection and fallback policy.

**What does not belong here:** canonical ChaseOS mutation, hidden writeback, unreviewed private data, production provider/API calls, or broad autonomous execution.

**Current status:** not active.

**V0 artifact or module target:** `src/chaser_agent/runtime_adapters/openai_provider.py`.

**First eval requirement:** create at least one golden or synthetic case showing the layer can distinguish grounded/reviewable output from unsafe, unsupported, or overbroad output.

**Authority risk:** overclaiming implementation status, silently promoting suggestions, treating a review artifact as canonical truth, or giving runtime/tool authority before eval evidence exists.

**Example workflow:** source or operator note enters the current source-summary wedge, produces a review packet, records uncertainty and evidence, and waits for human judgement before any downstream action.

**Later expansion:** after eval coverage exists, this layer can gain richer schemas, UI support, adapters, or automation while preserving ChaseOS Gate boundaries.

## 13. Tool / MCP Layer

**Purpose:** Define the product concern for tool / mcp layer in a way that can be tested before authority expands.

**Plain-English explanation:** This layer answers: “what does Chaser agent need to know, produce, or reject at the tool / mcp layer?” It turns the ChaseOS concept into a bounded Chaser agent artifact, not a claim of full runtime implementation.

**What belongs here:** tool/resource/prompt classification and least-authority evals.

**What does not belong here:** canonical ChaseOS mutation, hidden writeback, unreviewed private data, production provider/API calls, or broad autonomous execution.

**Current status:** planned.

**V0 artifact or module target:** `docs/02_Evals/Chaser-Agent-Tool-Use-Mini-Eval.md`.

**First eval requirement:** create at least one golden or synthetic case showing the layer can distinguish grounded/reviewable output from unsafe, unsupported, or overbroad output.

**Authority risk:** overclaiming implementation status, silently promoting suggestions, treating a review artifact as canonical truth, or giving runtime/tool authority before eval evidence exists.

**Example workflow:** source or operator note enters the current source-summary wedge, produces a review packet, records uncertainty and evidence, and waits for human judgement before any downstream action.

**Later expansion:** after eval coverage exists, this layer can gain richer schemas, UI support, adapters, or automation while preserving ChaseOS Gate boundaries.

## 14. Browser / Computer-Use Runtime Layer

**Purpose:** Define the product concern for browser / computer-use runtime layer in a way that can be tested before authority expands.

**Plain-English explanation:** This layer answers: “what does Chaser agent need to know, produce, or reject at the browser / computer-use runtime layer?” It turns the ChaseOS concept into a bounded Chaser agent artifact, not a claim of full runtime implementation.

**What belongs here:** future browser/computer-use evaluation only after safety proof.

**What does not belong here:** canonical ChaseOS mutation, hidden writeback, unreviewed private data, production provider/API calls, or broad autonomous execution.

**Current status:** not active.

**V0 artifact or module target:** `future browser safety eval`.

**First eval requirement:** create at least one golden or synthetic case showing the layer can distinguish grounded/reviewable output from unsafe, unsupported, or overbroad output.

**Authority risk:** overclaiming implementation status, silently promoting suggestions, treating a review artifact as canonical truth, or giving runtime/tool authority before eval evidence exists.

**Example workflow:** source or operator note enters the current source-summary wedge, produces a review packet, records uncertainty and evidence, and waits for human judgement before any downstream action.

**Later expansion:** after eval coverage exists, this layer can gain richer schemas, UI support, adapters, or automation while preserving ChaseOS Gate boundaries.

## 15. Runtime Memory / Repair Layer

**Purpose:** Define the product concern for runtime memory / repair layer in a way that can be tested before authority expands.

**Plain-English explanation:** This layer answers: “what does Chaser agent need to know, produce, or reject at the runtime memory / repair layer?” It turns the ChaseOS concept into a bounded Chaser agent artifact, not a claim of full runtime implementation.

**What belongs here:** runtime state health, repair notes, and noncanonical memory.

**What does not belong here:** canonical ChaseOS mutation, hidden writeback, unreviewed private data, production provider/API calls, or broad autonomous execution.

**Current status:** later.

**V0 artifact or module target:** `future runtime repair log schema`.

**First eval requirement:** create at least one golden or synthetic case showing the layer can distinguish grounded/reviewable output from unsafe, unsupported, or overbroad output.

**Authority risk:** overclaiming implementation status, silently promoting suggestions, treating a review artifact as canonical truth, or giving runtime/tool authority before eval evidence exists.

**Example workflow:** source or operator note enters the current source-summary wedge, produces a review packet, records uncertainty and evidence, and waits for human judgement before any downstream action.

**Later expansion:** after eval coverage exists, this layer can gain richer schemas, UI support, adapters, or automation while preserving ChaseOS Gate boundaries.

## 16. Governance / Gate / Approval Layer

**Purpose:** Define the product concern for governance / gate / approval layer in a way that can be tested before authority expands.

**Plain-English explanation:** This layer answers: “what does Chaser agent need to know, produce, or reject at the governance / gate / approval layer?” It turns the ChaseOS concept into a bounded Chaser agent artifact, not a claim of full runtime implementation.

**What belongs here:** approval rules, blocked transitions, and no-auto-promotion.

**What does not belong here:** canonical ChaseOS mutation, hidden writeback, unreviewed private data, production provider/API calls, or broad autonomous execution.

**Current status:** planned.

**V0 artifact or module target:** `docs/01_Product/Chaser-Agent-Repo-Boundary.md`.

**First eval requirement:** create at least one golden or synthetic case showing the layer can distinguish grounded/reviewable output from unsafe, unsupported, or overbroad output.

**Authority risk:** overclaiming implementation status, silently promoting suggestions, treating a review artifact as canonical truth, or giving runtime/tool authority before eval evidence exists.

**Example workflow:** source or operator note enters the current source-summary wedge, produces a review packet, records uncertainty and evidence, and waits for human judgement before any downstream action.

**Later expansion:** after eval coverage exists, this layer can gain richer schemas, UI support, adapters, or automation while preserving ChaseOS Gate boundaries.

## 17. Extension / Skill / Forge Layer

**Purpose:** Define the product concern for extension / skill / forge layer in a way that can be tested before authority expands.

**Plain-English explanation:** This layer answers: “what does Chaser agent need to know, produce, or reject at the extension / skill / forge layer?” It turns the ChaseOS concept into a bounded Chaser agent artifact, not a claim of full runtime implementation.

**What belongs here:** skill lifecycle, quarantine, eval-backed optimization.

**What does not belong here:** canonical ChaseOS mutation, hidden writeback, unreviewed private data, production provider/API calls, or broad autonomous execution.

**Current status:** planned.

**V0 artifact or module target:** `docs/06_Skills/Chaser-Agent-Skill-System.md`.

**First eval requirement:** create at least one golden or synthetic case showing the layer can distinguish grounded/reviewable output from unsafe, unsupported, or overbroad output.

**Authority risk:** overclaiming implementation status, silently promoting suggestions, treating a review artifact as canonical truth, or giving runtime/tool authority before eval evidence exists.

**Example workflow:** source or operator note enters the current source-summary wedge, produces a review packet, records uncertainty and evidence, and waits for human judgement before any downstream action.

**Later expansion:** after eval coverage exists, this layer can gain richer schemas, UI support, adapters, or automation while preserving ChaseOS Gate boundaries.
