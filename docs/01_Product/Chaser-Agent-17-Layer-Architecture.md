# Chaser agent 17-Layer Architecture

## Layer 0 — Behaviour Contract / Product Constitution

Layer 0 is not a runtime layer. It defines expected behavior, boundaries, public claims, and review requirements before the 17 architecture layers are interpreted. Every layer below must obey Layer 0: Chaser agent proposes reviewable artifacts; it does not silently promote canonical truth, activate tools, or claim production readiness.

Current Layer 0 artifact: `docs/01_Product/Chaser-Agent-Layer-0-Behaviour-Contract.md`.

## 1. User / Operator Layer

**Purpose:** Define the user / operator layer concern while staying subordinate to Layer 0.

**Plain-English meaning:** This layer explains where user / operator layer fits in the product model without claiming the layer is fully implemented.

**What belongs here:** human judgement, review checklists, acceptance/rejection examples.

**What does not belong:** automatic canonical promotion, secret access, unreviewed private data, production provider calls, or broad runtime autonomy.

**Current status:** planned.

**V0 relevance:** operator review is mandatory for promotion and public claims.

**First future proof requirement:** a contract or smoke test must show the layer preserves source truth, denies overreach, or produces reviewable output before the layer can expand.

**Authority risk:** overclaiming status, confusing notes with implementation, using generated text as truth, or bypassing human/ChaseOS review.

## 2. Studio / Interface Layer

**Purpose:** Define the studio / interface layer concern while staying subordinate to Layer 0.

**Plain-English meaning:** This layer explains where studio / interface layer fits in the product model without claiming the layer is fully implemented.

**What belongs here:** future review UI and source-card inspection surfaces.

**What does not belong:** automatic canonical promotion, secret access, unreviewed private data, production provider calls, or broad runtime autonomy.

**Current status:** later.

**V0 relevance:** V0 can work in files/CLI before UI exists.

**First future proof requirement:** a contract or smoke test must show the layer preserves source truth, denies overreach, or produces reviewable output before the layer can expand.

**Authority risk:** overclaiming status, confusing notes with implementation, using generated text as truth, or bypassing human/ChaseOS review.

## 3. Capture / Intake Layer

**Purpose:** Define the capture / intake layer concern while staying subordinate to Layer 0.

**Plain-English meaning:** This layer explains where capture / intake layer fits in the product model without claiming the layer is fully implemented.

**What belongs here:** safe input capture, metadata, privacy labels.

**What does not belong:** automatic canonical promotion, secret access, unreviewed private data, production provider calls, or broad runtime autonomy.

**Current status:** planned.

**V0 relevance:** V0 begins here with safe source input.

**First future proof requirement:** a contract or smoke test must show the layer preserves source truth, denies overreach, or produces reviewable output before the layer can expand.

**Authority risk:** overclaiming status, confusing notes with implementation, using generated text as truth, or bypassing human/ChaseOS review.

## 4. Source Package Layer

**Purpose:** Define the source package layer concern while staying subordinate to Layer 0.

**Plain-English meaning:** This layer explains where source package layer fits in the product model without claiming the layer is fully implemented.

**What belongs here:** source cards, evidence snippets, source metadata.

**What does not belong:** automatic canonical promotion, secret access, unreviewed private data, production provider calls, or broad runtime autonomy.

**Current status:** scaffolded.

**V0 relevance:** core to V0.

**First future proof requirement:** a contract or smoke test must show the layer preserves source truth, denies overreach, or produces reviewable output before the layer can expand.

**Authority risk:** overclaiming status, confusing notes with implementation, using generated text as truth, or bypassing human/ChaseOS review.

## 5. Workspace / Collection Layer

**Purpose:** Define the workspace / collection layer concern while staying subordinate to Layer 0.

**Plain-English meaning:** This layer explains where workspace / collection layer fits in the product model without claiming the layer is fully implemented.

**What belongs here:** grouping related sources and run outputs.

**What does not belong:** automatic canonical promotion, secret access, unreviewed private data, production provider calls, or broad runtime autonomy.

**Current status:** later.

**V0 relevance:** not required for first single-source V0 loop.

**First future proof requirement:** a contract or smoke test must show the layer preserves source truth, denies overreach, or produces reviewable output before the layer can expand.

**Authority risk:** overclaiming status, confusing notes with implementation, using generated text as truth, or bypassing human/ChaseOS review.

## 6. Retrieval / Evidence Layer

**Purpose:** Define the retrieval / evidence layer concern while staying subordinate to Layer 0.

**Plain-English meaning:** This layer explains where retrieval / evidence layer fits in the product model without claiming the layer is fully implemented.

**What belongs here:** citations, snippets, future retrieval.

**What does not belong:** automatic canonical promotion, secret access, unreviewed private data, production provider calls, or broad runtime autonomy.

**Current status:** planned.

**V0 relevance:** V0 needs evidence snippets, not full RAG.

**First future proof requirement:** a contract or smoke test must show the layer preserves source truth, denies overreach, or produces reviewable output before the layer can expand.

**Authority risk:** overclaiming status, confusing notes with implementation, using generated text as truth, or bypassing human/ChaseOS review.

## 7. Summary Intelligence Layer

**Purpose:** Define the summary intelligence layer concern while staying subordinate to Layer 0.

**Plain-English meaning:** This layer explains where summary intelligence layer fits in the product model without claiming the layer is fully implemented.

**What belongs here:** claims, uncertainty, contradictions, actions, memory candidates.

**What does not belong:** automatic canonical promotion, secret access, unreviewed private data, production provider calls, or broad runtime autonomy.

**Current status:** scaffolded.

**V0 relevance:** first V0 behavior implementation.

**First future proof requirement:** a contract or smoke test must show the layer preserves source truth, denies overreach, or produces reviewable output before the layer can expand.

**Authority risk:** overclaiming status, confusing notes with implementation, using generated text as truth, or bypassing human/ChaseOS review.

## 8. Memory Consolidation Layer

**Purpose:** Define the memory consolidation layer concern while staying subordinate to Layer 0.

**Plain-English meaning:** This layer explains where memory consolidation layer fits in the product model without claiming the layer is fully implemented.

**What belongs here:** memory candidate states and review transitions.

**What does not belong:** automatic canonical promotion, secret access, unreviewed private data, production provider calls, or broad runtime autonomy.

**Current status:** planned.

**V0 relevance:** candidate-only in V0.

**First future proof requirement:** a contract or smoke test must show the layer preserves source truth, denies overreach, or produces reviewable output before the layer can expand.

**Authority risk:** overclaiming status, confusing notes with implementation, using generated text as truth, or bypassing human/ChaseOS review.

## 9. Graph Intelligence Layer

**Purpose:** Define the graph intelligence layer concern while staying subordinate to Layer 0.

**Plain-English meaning:** This layer explains where graph intelligence layer fits in the product model without claiming the layer is fully implemented.

**What belongs here:** future relationships among claims, sources, actions, memories.

**What does not belong:** automatic canonical promotion, secret access, unreviewed private data, production provider calls, or broad runtime autonomy.

**Current status:** later.

**V0 relevance:** not needed for V0.

**First future proof requirement:** a contract or smoke test must show the layer preserves source truth, denies overreach, or produces reviewable output before the layer can expand.

**Authority risk:** overclaiming status, confusing notes with implementation, using generated text as truth, or bypassing human/ChaseOS review.

## 10. Agent Runtime / AOR Layer

**Purpose:** Define the agent runtime / aor layer concern while staying subordinate to Layer 0.

**Plain-English meaning:** This layer explains where agent runtime / aor layer fits in the product model without claiming the layer is fully implemented.

**What belongs here:** future bounded runtime experiments.

**What does not belong:** automatic canonical promotion, secret access, unreviewed private data, production provider calls, or broad runtime autonomy.

**Current status:** not active.

**V0 relevance:** not active in V0.

**First future proof requirement:** a contract or smoke test must show the layer preserves source truth, denies overreach, or produces reviewable output before the layer can expand.

**Authority risk:** overclaiming status, confusing notes with implementation, using generated text as truth, or bypassing human/ChaseOS review.

## 11. Harness Layer

**Purpose:** Define the harness layer concern while staying subordinate to Layer 0.

**Plain-English meaning:** This layer explains where harness layer fits in the product model without claiming the layer is fully implemented.

**What belongs here:** smoke/schema checks now; contract evals later.

**What does not belong:** automatic canonical promotion, secret access, unreviewed private data, production provider calls, or broad runtime autonomy.

**Current status:** scaffolded.

**V0 relevance:** supports V0 proof after behavior is defined.

**First future proof requirement:** a contract or smoke test must show the layer preserves source truth, denies overreach, or produces reviewable output before the layer can expand.

**Authority risk:** overclaiming status, confusing notes with implementation, using generated text as truth, or bypassing human/ChaseOS review.

## 12. Provider / Model Router Layer

**Purpose:** Define the provider / model router layer concern while staying subordinate to Layer 0.

**Plain-English meaning:** This layer explains where provider / model router layer fits in the product model without claiming the layer is fully implemented.

**What belongs here:** future model/provider selection and fallback.

**What does not belong:** automatic canonical promotion, secret access, unreviewed private data, production provider calls, or broad runtime autonomy.

**Current status:** not active.

**V0 relevance:** not active; no provider calls by default.

**First future proof requirement:** a contract or smoke test must show the layer preserves source truth, denies overreach, or produces reviewable output before the layer can expand.

**Authority risk:** overclaiming status, confusing notes with implementation, using generated text as truth, or bypassing human/ChaseOS review.

## 13. Tool / MCP Layer

**Purpose:** Define the tool / mcp layer concern while staying subordinate to Layer 0.

**Plain-English meaning:** This layer explains where tool / mcp layer fits in the product model without claiming the layer is fully implemented.

**What belongs here:** future least-authority resource/tool/prompt evals.

**What does not belong:** automatic canonical promotion, secret access, unreviewed private data, production provider calls, or broad runtime autonomy.

**Current status:** planned.

**V0 relevance:** not active until contract evals.

**First future proof requirement:** a contract or smoke test must show the layer preserves source truth, denies overreach, or produces reviewable output before the layer can expand.

**Authority risk:** overclaiming status, confusing notes with implementation, using generated text as truth, or bypassing human/ChaseOS review.

## 14. Browser / Computer-Use Runtime Layer

**Purpose:** Define the browser / computer-use runtime layer concern while staying subordinate to Layer 0.

**Plain-English meaning:** This layer explains where browser / computer-use runtime layer fits in the product model without claiming the layer is fully implemented.

**What belongs here:** future browser/computer-use safety research.

**What does not belong:** automatic canonical promotion, secret access, unreviewed private data, production provider calls, or broad runtime autonomy.

**Current status:** not active.

**V0 relevance:** blocked by default.

**First future proof requirement:** a contract or smoke test must show the layer preserves source truth, denies overreach, or produces reviewable output before the layer can expand.

**Authority risk:** overclaiming status, confusing notes with implementation, using generated text as truth, or bypassing human/ChaseOS review.

## 15. Runtime Memory / Repair Layer

**Purpose:** Define the runtime memory / repair layer concern while staying subordinate to Layer 0.

**Plain-English meaning:** This layer explains where runtime memory / repair layer fits in the product model without claiming the layer is fully implemented.

**What belongs here:** future runtime state and repair logs.

**What does not belong:** automatic canonical promotion, secret access, unreviewed private data, production provider calls, or broad runtime autonomy.

**Current status:** later.

**V0 relevance:** not V0 canonical memory.

**First future proof requirement:** a contract or smoke test must show the layer preserves source truth, denies overreach, or produces reviewable output before the layer can expand.

**Authority risk:** overclaiming status, confusing notes with implementation, using generated text as truth, or bypassing human/ChaseOS review.

## 16. Governance / Gate / Approval Layer

**Purpose:** Define the governance / gate / approval layer concern while staying subordinate to Layer 0.

**Plain-English meaning:** This layer explains where governance / gate / approval layer fits in the product model without claiming the layer is fully implemented.

**What belongs here:** approval boundaries and no-auto-promotion rules.

**What does not belong:** automatic canonical promotion, secret access, unreviewed private data, production provider calls, or broad runtime autonomy.

**Current status:** planned.

**V0 relevance:** Layer 0 depends on this boundary.

**First future proof requirement:** a contract or smoke test must show the layer preserves source truth, denies overreach, or produces reviewable output before the layer can expand.

**Authority risk:** overclaiming status, confusing notes with implementation, using generated text as truth, or bypassing human/ChaseOS review.

## 17. Extension / Skill / Forge Layer

**Purpose:** Define the extension / skill / forge layer concern while staying subordinate to Layer 0.

**Plain-English meaning:** This layer explains where extension / skill / forge layer fits in the product model without claiming the layer is fully implemented.

**What belongs here:** skills, quarantine, review, rollback.

**What does not belong:** automatic canonical promotion, secret access, unreviewed private data, production provider calls, or broad runtime autonomy.

**Current status:** planned.

**V0 relevance:** skills can guide V0 but not grant authority.

**First future proof requirement:** a contract or smoke test must show the layer preserves source truth, denies overreach, or produces reviewable output before the layer can expand.

**Authority risk:** overclaiming status, confusing notes with implementation, using generated text as truth, or bypassing human/ChaseOS review.
