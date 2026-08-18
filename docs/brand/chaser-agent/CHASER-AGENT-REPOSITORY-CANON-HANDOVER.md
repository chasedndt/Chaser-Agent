# Chaser Agent Repository Canon Handover

**Target repository:** Chaser Agent  
**Handover version:** `1.0.0`  
**Canon version:** `1.0.0`  
**Role:** Authoritative home of Chaser Agent character, standalone product identity, editable brand sources, and released asset bundles.

---

# 1. Repository responsibility

This repository becomes the source of truth for:

- Chaser Agent public product name;
- standalone positioning;
- character canon;
- canonical mascot model;
- editable source assets;
- runtime identity exports;
- state assets;
- release manifests;
- brand usage rules;
- ChaseOS relationship copy.

The ChaseOS repository consumes released versions and owns integration.

---

# 2. Documents to install

Recommended:

```text
docs/brand/chaser-agent/
├── CHASER-AGENT-CHARACTER-CANON-AND-VISUAL-SPEC.md
├── CHASER-AGENT-FULL-ASSET-ROADMAP-AND-PRODUCTION-SPEC.md
├── CHASER-AGENT-REPOSITORY-CANON-HANDOVER.md
└── CHASER-AGENT-CANON-SYNC-MANIFEST.json
```

Place the selected reference under:

```text
brand/chaser-agent/reference/selected-base/
```

Do not put broad exploration sheets into the active reference folder.

---

# 3. Public positioning

Canonical name:

```text
Chaser Agent
```

Canonical category:

```text
Persistent approval-gated agent harness
```

Canonical short description:

```text
A 24/7 agent harness that compiles context, pursues goals, and acts within your boundaries.
```

Canonical ChaseOS relationship:

```text
Runs independently. Works best with ChaseOS.
```

Do not describe it primarily as:

- chatbot;
- copilot;
- generic assistant;
- robot employee;
- autonomous worker with unlimited authority.

---

# 4. README integration

The README should eventually contain:

1. what Chaser Agent is;
2. who it is for;
3. current product truth;
4. approval and authority model;
5. standalone operation;
6. ChaseOS integration;
7. quick start;
8. architecture;
9. security and permissions;
10. mascot/brand usage link;
11. trademarks/licensing;
12. contribution rules.

The mascot may appear in the README hero only after a clean released asset exists.

Do not use the generated presentation sheet as the final README hero.

---

# 5. Brand directory

Recommended:

```text
brand/chaser-agent/
├── canon/
├── reference/
├── source/
├── exports/
├── manifests/
├── qa/
├── releases/
└── design-history/
```

## `canon/`

Authoritative documents.

## `reference/`

Only operator-selected visual references.

## `source/`

Editable model, rig, materials, markings, visor, illustration, motion.

## `exports/`

Generated but approved output classes.

## `manifests/`

Hashes, versions, attribution, intended usage.

## `qa/`

Comparison sheets, small-size tests, crop tests, accessibility checks.

## `releases/`

Immutable versioned bundles consumed by ChaseOS and public surfaces.

## `design-history/`

Rejected and exploratory work clearly separated from canon.

---

# 6. Asset release contract

Every release should expose:

```text
chaser-agent-brand-assets-vX.Y.Z/
├── manifest.json
├── core/
├── profile/
├── states/
├── ui/
├── social/
├── docs/
└── licences/
```

Manifest fields:

- canon version;
- asset release version;
- build date;
- source commit;
- file hashes;
- asset IDs;
- dimensions;
- alpha/colour space;
- intended surfaces;
- deprecation status;
- operator approval.

ChaseOS should consume the release, not scrape working directories.

---

# 7. Character source policy

The selected reference is the base visual.

Before publishing official assets:

- reconstruct a consistent model;
- preserve exact anatomy;
- create a model sheet;
- create source-controlled markings;
- create deterministic visor states;
- create neutral and semantic lighting presets;
- export transparent masters;
- obtain operator approval.

Do not use image-generation variation to create each state independently after the canonical model exists.

AI generation may support ideation and backgrounds, but final character anatomy should come from the controlled source model.

---

# 8. Product behaviour reflected by the brand

The repository documentation and mascot states must align.

## Uncertain

Chaser Agent asks or presents options rather than guessing.

## Approval

Chaser Agent pauses before consequential or ambiguous action.

## Learning

Chaser Agent may learn operator preferences but cannot grant itself permanent authority.

## Correction

Chaser Agent preserves correction provenance.

## Standalone

Chaser Agent can function without ChaseOS.

## ChaseOS-enhanced

ChaseOS provides the broader private memory, Knowledge Graph, companion profiles, permissions, workflow surfaces, and control plane.

---

# 9. User-instance naming

The repository may document that downstream deployments can use a personal companion name.

Example:

```text
Atlas — a personal Chaser Agent instance
```

However:

- the official repository remains `Chaser Agent`;
- package names remain canonical;
- audit logs identify the runtime;
- third parties must not imply that a personal name is a separate official product.

---

# 10. Trademark and visual-use boundary

The code licence does not automatically grant unrestricted use of the Chaser Agent name, mascot, or official identity.

Before public release, retain or create:

- trademark notice;
- logo/mascot usage policy;
- community derivative policy;
- fork naming rule;
- official/unofficial distinction;
- merchandise policy;
- attribution rule.

Do not embed a permissive code licence header into the mascot files unless the operator explicitly chooses that policy.

---

# 11. CI and QA recommendations

Add checks for:

- manifest JSON validity;
- duplicate asset IDs;
- missing required sizes;
- wrong image dimensions;
- absent alpha where required;
- unexpected colour profiles;
- hash mismatch;
- filename convention;
- unapproved status in release folders;
- canon-version mismatch;
- rejected design-history asset imported into production.

Optional visual tests:

- perceptual diff;
- circular-crop snapshot;
- 64 px snapshot;
- dark/light snapshot;
- state-semantic snapshot.

---

# 12. Versioning

Use two versions:

```text
canon_version
asset_release_version
```

Examples:

- Anatomy unchanged, new banner: asset `1.1.0`, canon `1.0.0`.
- New state animation, same character: asset `1.2.0`, canon `1.0.0`.
- Changed visor architecture: canon `2.0.0`, asset `2.0.0`.
- Corrected typo in docs: canon `1.0.1`, asset unchanged.

---

# 13. ChaseOS publication flow

1. Publish Chaser Agent asset release.
2. Record release commit and manifest.
3. Open/update ChaseOS integration branch.
4. Consume exact release.
5. Run ChaseOS visual and behaviour QA.
6. Approve.
7. Deploy.
8. Record the ChaseOS commit that consumed the asset release.

This creates traceability across both repositories.

---

# 14. Immediate repository tasks

1. Install this canon pack.
2. Add the selected reference.
3. Add canon/version manifest.
4. Archive non-selected explorations.
5. Add brand folder structure.
6. Update README positioning where it conflicts.
7. Add standalone/ChaseOS relationship.
8. Create production-model work item.
9. Create asset-roadmap issues/milestones.
10. Add trademark/visual policy work item.
11. Prepare first canonical asset release.
12. Coordinate ChaseOS consumption.

---

# 15. Agent implementation instruction

Before editing:

- inspect the repository;
- locate existing branding, README, docs, package metadata, public assets, and trademark files;
- report conflicts with this canon;
- preserve current working product truth;
- do not claim unimplemented capabilities;
- make reversible commits;
- keep generated exploration separate;
- do not publish the selected sheet as a clean final asset;
- return a complete changed-file and QA report.

---

# 16. Completion evidence

Required:

- installed canon paths;
- selected reference path/hash;
- README diff;
- manifest;
- issues/milestones created;
- archive path for rejected exploration;
- source-model plan;
- tests;
- unresolved questions;
- ChaseOS handoff version.
