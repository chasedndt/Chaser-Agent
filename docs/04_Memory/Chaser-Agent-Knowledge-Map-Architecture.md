# Chaser agent Knowledge Map Architecture

**Layer:** 9 (Graph Intelligence) · **Status:** implemented in P0.1 · **Code:** `src/chaser_agent/knowledge/`

## Purpose

The knowledge map turns isolated runs into a traceable system. It answers provenance questions that no single artifact can:

- where did this claim come from?
- which evidence supports it?
- what was inferred rather than stated?
- which review decision approved this?
- which source does this memory trace back to?
- what did this run create?
- what superseded what?

It is a **relationship index**, not a replacement for source files, review records, memory records, or run artifacts. Those remain the content; the graph records how they connect.

## Model

Two frozen dataclasses in `knowledge/models.py`.

**Node** — `node_id`, `node_type`, `label`, `content_ref`, `scope`, `privacy_class`, `created_at`, `metadata_json`.

**Edge** — `edge_id`, `from_node_id`, `to_node_id`, `edge_type`, `created_at`, `run_id`, `review_id`, `metadata_json`.

Both validate their type against a closed vocabulary at construction; an unsupported type raises immediately.

### Node types

`source · claim · evidence · inference · concept · decision · action · memory · workflow · run · project · skill · agent · tool`

P0.1 actively populates: `source`, `claim`, `evidence`, `inference`, `decision`, `action`, `memory`, `workflow`, `run`.

### Edge types

`derived_from · supported_by · contradicts · inferred_from · relates_to · applies_to · proposed_by · approved_by · rejected_by · supersedes · generated_in · used_by · reviewed_in`

## Deterministic identity

IDs are **UUID v5** hashes (`uuid.uuid5`) over a namespaced identity string — never random:

```text
node: chaser-agent:node:{node_type}:{scope}:{content_identity}
edge: chaser-agent:edge:{edge_type}:{from}:{to}:{run_id}:{review_id}
```

Consequence: re-indexing the same reviewed run produces the **same** IDs, so the operation is idempotent and graphs are comparable across machines. Random IDs would make provenance untestable — this is why `Date.now()`-style nondeterminism is avoided in identity.

## Indexing a reviewed run

`knowledge/service.py::index_reviewed_run(store, run_folder, review, memories)` walks a completed run plus its review record and writes the full provenance subgraph:

```text
source --generated_in--> run
run --used_by--> workflow(profile)
claim --derived_from--> source
claim --supported_by--> evidence
inference --inferred_from--> claim
action --proposed_by--> run
decision --reviewed_in--> run
action --approved_by/rejected_by--> decision
memory --derived_from--> source and claims
memory --reviewed_in--> decision
```

Note the shape of the guarantee: **a memory node can only reach a source through claims and evidence that actually exist in that run.** Provenance is structural, not asserted.

It returns counts of nodes and edges written, and is only called for *reviewed* runs — the graph records judged work, not raw output.

## Storage and queries

`SQLiteKnowledgeMapStore` — standard-library SQLite, no external graph database. Supported queries: get node · list neighbours (optionally filtered by edge type) · evidence supporting a claim · claims derived from a source · memories derived from a source · decisions created by a review · items superseded by a memory · graph entries created by a run · trace a memory back to source and evidence.

## Why a graph, and the maths behind it

This is [graph theory](../08_Learning/Maths-For-Chaser-Agent.md) applied directly: nodes, directed typed edges, neighbourhood queries, and path traversal for provenance chains. The SQLite schema exercises database design — primary keys, foreign-key discipline, indexes, and transactions. Both are P0.1 concepts in the learning map, tied to this real code.

## ChaseOS relationship

Standalone, the knowledge map is a **local provenance graph** owned by the user. Under ChaseOS, the governed knowledge graph provides cross-project graph intelligence. Chaser agent does not duplicate ChaseOS authority — it produces local lineage that a ChaseOS deployment may later consume through the optional adapter.
