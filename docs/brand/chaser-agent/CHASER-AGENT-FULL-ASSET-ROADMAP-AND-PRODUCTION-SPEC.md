# Chaser Agent Full Asset Roadmap and Production Specification

**Document status:** Canonical production plan  
**Roadmap version:** `1.0.0`  
**Canon dependency:** `CHASER-AGENT-CHARACTER-CANON-AND-VISUAL-SPEC.md`  
**Current stage:** Selected base reference; definitive isolated production model pending

---

# 1. Objective

Build a complete, consistent, reusable Chaser Agent asset system from the operator-selected canonical base mascot.

The end state is not one attractive image. It is a versioned production system supporting:

- standalone Chaser Agent branding;
- ChaseOS companion and runtime profiles;
- Discord bot/application presentation;
- Knowledge Graph and control-plane UI;
- approvals and runtime states;
- documentation and GitHub;
- social media;
- motion;
- future user-instance personalisation.

---

# 2. Current truth

## Complete

- broad character exploration;
- rejection of mecha/robot directions;
- organic-digital species definition;
- operator selection of one base mascot;
- core personality and authority model;
- basic runtime-state language;
- core ChaseOS relationship;
- initial Hermes and OpenClaw ChaseOS identity treatments.

## Not complete

- isolated canonical character;
- perfectly consistent anatomy across views;
- final editable model/source;
- calibrated colour and material master;
- final marking vector masks;
- final profile icon;
- final runtime-state exports;
- final public banners;
- final ChaseOS UI implementation;
- final motion and audio;
- repository integration;
- production QA.

The selected reference is a **canon anchor**, not a ready-to-deploy source asset.

---

# 3. Production principles

1. Reconstruct; do not merely crop the selected sheet.
2. Preserve one exact anatomy across every output.
3. Separate character source files from presentation compositions.
4. Keep semantic state colour deterministic.
5. Keep the mascot recognisable without the ChaseOS logo.
6. Add ChaseOS framing at the composition/UI layer.
7. Publish versioned asset bundles from the Chaser Agent repository.
8. Consume released assets in ChaseOS rather than redrawing them there.
9. Preserve prompts, source files, dates, hashes, and approvals.
10. Verify every platform crop before publishing.

---

# 4. Status ladder

Use this lifecycle:

```text
raw
→ candidate
→ shortlisted
→ selected-reference
→ reconstructed
→ canonical-model
→ exported
→ QA
→ approved
→ released
→ integrated
→ published
```

Do not skip from `selected-reference` to `published`.

---

# 5. Phase 0 — Canon installation

## Deliverables

- Canon documents installed in both repositories.
- Selected reference copied under canonical filename.
- SHA-256 recorded.
- Sync manifest installed.
- Authority split acknowledged.
- Old robot/mecha variants excluded from active reference folders.
- Existing ChaseOS brand documents marked as superseded where they still state that the logo/mascot is unselected.

## Acceptance

- Both repositories expose the same `canon_version`.
- There is no competing “final” mascot in either repository.
- Agent instructions can locate the canonical documents.
- Design-history assets are separated from canonical assets.

---

# 6. Phase 1 — Definitive character reconstruction

## 6.1 Recommended production method

Because the selected style is dimensional but not fully photoreal, the strongest long-term method is:

- one stylised 3D base model and rig for consistency;
- one controlled shader/material system;
- one vector/2D derivative system for icons and diagrams.

A fully 2D master is acceptable only if the illustrator can maintain exact proportions and anatomy across all required poses.

## 6.2 Required source deliverables

At least one editable production source:

- `.blend` preferred for 3D;
- `.fbx` or `.glb` interoperability export;
- layered `.psd`, `.kra`, or equivalent for paintover;
- `.svg` for simplified icons and markings;
- material swatches;
- marking masks;
- visor-state sprite/vector source;
- rig documentation;
- render settings.

## 6.3 Required model views

- front orthographic;
- three-quarter front;
- side;
- back;
- three-quarter back;
- neutral full body;
- head close-up;
- hand close-up;
- foot close-up;
- black silhouette;
- height comparison beside a human.

## 6.4 Reconstruction constraints

- Target height: 0.90 m.
- Four digits per hand.
- Three toe forms per foot.
- No armour seams.
- No helmet rim.
- No visible robot joints.
- No physical tail.
- Visor embedded in the face.
- Markings use separate editable masks.
- Material must remain matte.
- Head/body ratio must stay within canon.
- A-pose or neutral rig pose must not distort the public silhouette.

## 6.5 Acceptance

- One model survives a four-view turntable without anatomy drift.
- Profile crop works at 64 px.
- Silhouette remains distinct in solid black.
- Model does not read as a toy robot.
- Operator approves a side-by-side comparison with the selected reference.

---

# 7. Phase 2 — Core static identity pack

## 7.1 Character masters

| Asset | Recommended master |
|---|---|
| Neutral full-body transparent | 3000×4000 PNG/WebP |
| Three-quarter full-body transparent | 3000×4000 PNG/WebP |
| Head-and-shoulders transparent | 3000×3000 PNG/WebP |
| Head close-up | 3000×3000 PNG/WebP |
| Front/side/back model sheet | 4096×3072 PNG/PDF |
| Black silhouette | SVG + PNG |
| White silhouette | SVG + PNG |
| Material/marking sheet | 4096×3072 PNG/PDF |

## 7.2 Profile/avatar pack

Create one canonical avatar composition first.

Required exports:

- 2048×2048 master;
- 1024×1024;
- 512×512;
- 256×256;
- 128×128;
- 64×64;
- 32×32;
- 16×16 simplified icon;
- circular crop preview;
- rounded-square crop preview;
- dark-ground version;
- light-ground version;
- transparent version where possible.

The 16 px export may use a simplified visor/head glyph rather than the full character.

## 7.3 Lockups

- `Chaser Agent` wordmark-only;
- `Chaser Agent // ChaseOS`;
- `Chaser Agent — A ChaseOS Native Runtime`;
- icon + name horizontal;
- icon + name stacked;
- monochrome lockup;
- dark/light versions.

Final typography must be deterministic and must not be generated inside an image model.

---

# 8. Phase 3 — Runtime-state pack

Create the same canonical mascot in:

1. dormant;
2. tracking;
3. compiling;
4. uncertain;
5. contradiction;
6. awaiting approval;
7. approved;
8. correction;
9. blocked;
10. complete.

## Per-state deliverables

- full-body transparent;
- half-body transparent;
- head/profile state;
- visor-only glyph;
- UI state badge;
- 64 px icon;
- 32 px icon;
- motion keyframe;
- semantic token record;
- alt text.

## State acceptance

- Each state reads without text at medium size.
- Teal, amber, and red retain their semantic meaning.
- The character does not change anatomy between states.
- Blocked and contradiction are not visually identical.
- Approved and complete are not visually identical.
- Uncertain does not look like a system failure.
- Awaiting approval does not imply that approval was granted.

---

# 9. Phase 4 — Evidence and interaction pack

Required poses:

- receiving raw source fragments;
- following a goal trail;
- compiling multiple sources;
- comparing two competing possibilities;
- presenting a review packet;
- waiting at an approval gate;
- accepting a correction;
- stopping an unsafe action;
- resolving a workflow;
- standing beside a Knowledge Graph projection;
- working with a second companion;
- idle beside the operator.

Required objects:

- source fragment;
- evidence shard;
- memory shard;
- unresolved node;
- compiled packet;
- verified proof object;
- approval gate;
- denied path;
- provenance ribbon;
- goal checkpoint.

Objects must be generic and privacy-safe unless real public evidence is intentionally supplied.

---

# 10. Phase 5 — ChaseOS product integration assets

## 10.1 Runtime selector

- 64 px head icon;
- selected-state ring;
- active-state indicator;
- native-runtime label;
- accessible alt text;
- fallback monochrome glyph.

## 10.2 Runtime profile card

Must support:

- canonical runtime name;
- user-instance/companion name;
- current state;
- approval mode;
- specialisation;
- health;
- asset version;
- provider relationship;
- last verified activity.

## 10.3 Knowledge Graph panels

Use:

- small head icon at node/profile level;
- provenance ribbon only for an active trace;
- full mascot only in expanded companion/profile view;
- deterministic state colour;
- no decorative mascot duplication across every node.

## 10.4 Control plane

Required visual states:

- online/dormant;
- active workflow;
- awaiting approval;
- degraded/error;
- blocked;
- disconnected;
- updating;
- version mismatch.

Runtime health must not be confused with character mood.

## 10.5 Approval surfaces

- grounded pose;
- amber authority gate;
- visible proposed action;
- explicit operator buttons outside the artwork;
- no implied approval before interaction;
- screenshot and mobile QA.

## 10.6 Notifications

- simplified head glyph;
- state-specific visor;
- no full-body art in dense notification surfaces;
- red only for actual blocked/unsafe/error conditions.

## 10.7 Onboarding

- full-body introduction;
- concise explanation of Chaser Agent;
- distinction between runtime product and personal companion name;
- permission/approval explanation;
- personal marking setup only after the canonical default is shown.

---

# 11. Phase 6 — Public runtime identity pack

## 11.1 Chaser Agent standalone assets

- GitHub repository avatar;
- GitHub social preview;
- README hero;
- documentation cover;
- release card;
- project website hero;
- X profile image;
- X banner;
- Discord bot/application avatar;
- Discord/community introduction card;
- YouTube thumbnail template;
- vertical social cover;
- launch poster;
- press/media kit image.

## 11.2 Planning dimensions

These are production planning targets and must be verified against live platform requirements before final export.

| Surface | Planning target |
|---|---:|
| X header | 1500×500 |
| LinkedIn company cover | 1128×191 |
| Discord/event adaptable master | 1920×1080 plus tested crop |
| YouTube channel art | 2560×1440 |
| General cinematic master | 3840×2160 |
| Open Graph card | 1200×630 |
| GitHub social preview | 1280×640 |
| README hero | 1600×900 |
| Square social post | 1080×1080 |
| Portrait social post | 1080×1350 |
| Vertical story/short cover | 1080×1920 |

Do not blind-crop one universal banner. Recompose around each platform safe area.

## 11.3 Copy discipline

Profile/banner assets should usually contain:

```text
CHASER AGENT
```

Optional:

```text
Your 24/7 approval-gated agent harness.
```

Do not automatically add feature bullets.

---

# 12. Phase 7 — ChaseOS companion ecosystem pack

Create coordinated assets showing:

- Chaser Agent;
- Hermes Agent;
- OpenClaw;
- Codex;
- Claude Code;
- future companion slot.

## Shared rules

- same ChaseOS environment;
- same parent typography and status grammar;
- same state semantics;
- same framing and safe areas;
- distinct canonical identities;
- operator remains conceptually above all companions.

## Required assets

- runtime/companion lineup;
- native vs connected relationship diagram;
- companion selector mockup;
- Knowledge Graph profile set;
- collaborative workflow composition;
- operator-approval composition;
- development-agent composition for Codex/Claude Code;
- neutral group image without implying equal technical capabilities.

Do not redraw every companion into the Chaser Agent species.

---

# 13. Phase 8 — Motion and sound

## 13.1 Motion assets

- dormant breathing/idle;
- tracking ribbon emergence;
- compiling fragments;
- uncertainty pulse;
- approval grounding;
- approved path continuation;
- correction/retraction;
- blocked stop;
- complete settle;
- profile-avatar loop;
- loading animation;
- onboarding reveal.

Preferred output formats:

- Rive;
- Lottie where appropriate;
- WebM with alpha;
- MP4;
- PNG sequence;
- sprite sheet;
- source timeline/project.

## 13.2 Motion grammar

- deliberate;
- quiet;
- smooth;
- nearly weightless;
- no glitch montage;
- no particle explosion;
- no generic logo spin;
- no frantic bouncing.

## 13.3 Sound identity

Future sound pack:

- dormant acknowledgement;
- source acquired;
- uncertainty;
- approval requested;
- approval accepted;
- blocked;
- correction;
- complete.

Sounds should be non-human, concise, warm enough to feel companion-like, and never toy-like.

---

# 14. Phase 9 — Personalisation pack

Initially permitted:

- companion display name;
- small approved surface markings.

Required implementation assets:

- default marking;
- marking-zone masks;
- marking preview;
- invalid-marking guard;
- profile preview;
- reset-to-canonical action;
- audit record of personalisation.

Do not allow anatomy, body colour semantics, or state colours to drift.

---

# 15. File and folder structure

Recommended authoritative structure in the Chaser Agent repository:

```text
brand/chaser-agent/
├── canon/
│   ├── character-canon.md
│   ├── asset-roadmap.md
│   └── manifest.json
├── reference/
│   └── selected-base/
├── source/
│   ├── model/
│   ├── rig/
│   ├── materials/
│   ├── markings/
│   ├── visor/
│   ├── illustration/
│   └── motion/
├── exports/
│   ├── core/
│   ├── profile/
│   ├── states/
│   ├── interaction/
│   ├── ui/
│   ├── social/
│   ├── docs/
│   ├── motion/
│   └── audio/
├── manifests/
├── qa/
└── releases/
```

Recommended ChaseOS consumer structure:

```text
packages/brand-assets/chaser-agent/
├── v1/
│   ├── core/
│   ├── profile/
│   ├── states/
│   ├── ui/
│   └── manifest.json
└── current -> v1
```

Adapt paths to the real repository rather than creating duplicate trees blindly.

---

# 16. Naming convention

Use:

```text
chaser-agent_[asset-class]_[view-or-state]_[variant]_[status]_v[asset-version]_[YYYYMMDD].[ext]
```

Examples:

```text
chaser-agent_character_front_canonical_approved_v1.0.0_20260817.png
chaser-agent_profile_default_round_approved_v1.0.0_20260817.webp
chaser-agent_state_awaiting-approval_fullbody_approved_v1.0.0_20260817.png
chaser-agent_banner_x_default_approved_v1.0.0_20260817.png
```

Use lowercase kebab-case for code paths.

---

# 17. Manifest requirements

Every released asset records:

- asset ID;
- canon version;
- asset release version;
- source file;
- export file;
- dimensions;
- colour space;
- alpha;
- SHA-256;
- intended surfaces;
- state;
- approval date;
- operator approval;
- alt text;
- licence/usage status;
- replacement/deprecation history.

---

# 18. QA matrix

## Visual fidelity

- anatomy consistent;
- markings consistent;
- visor correct;
- no mecha cues;
- no unwanted logo fusion;
- no generated text distortion.

## Size and crop

- 16/32/64 px;
- square;
- circular;
- rounded-square;
- wide banner;
- mobile crop;
- dark/light ground.

## Semantic state

- teal only live;
- amber only human authority;
- red only blocked/unsafe/failed;
- bone for verified clarity;
- contradiction not automatically red.

## Technical

- correct dimensions;
- correct colour profile;
- alpha intact;
- file size acceptable;
- no private metadata;
- deterministic filename;
- manifest hash matches;
- public URL returns expected file.

## Product truth

- runtime name correct;
- personal name does not replace canonical runtime in audit/permissions;
- approval state accurate;
- no unsupported capability claims;
- standalone/ChaseOS relationship accurate.

## Accessibility

- state not communicated by colour alone;
- alt text;
- minimum contrast;
- reduced-motion alternative;
- no rapid flashing;
- legible small-size glyphs.

---

# 19. Release bundles

## Bundle A — Canon Core

- model sheet;
- source hashes;
- neutral full body;
- head close-up;
- silhouettes;
- colour/material tokens;
- canon docs.

## Bundle B — Product UI

- profile icons;
- state glyphs;
- runtime card art;
- Knowledge Graph assets;
- approval assets;
- notification assets.

## Bundle C — Public Identity

- profile images;
- banners;
- README hero;
- GitHub social;
- launch cards;
- documentation cover.

## Bundle D — Motion

- runtime-state animations;
- avatar loop;
- loading;
- approval;
- correction;
- blocked;
- sound cues.

Each bundle receives its own asset release version but must declare the same character canon version.

---

# 20. Execution priority

## Priority 0

- install canon documents;
- secure selected reference;
- create manifest.

## Priority 1

- definitive reconstruction;
- full turnaround;
- avatar;
- state pack.

## Priority 2

- ChaseOS runtime profile;
- Knowledge Graph integration;
- approval UI;
- Discord app/avatar;
- GitHub identity.

## Priority 3

- social banners;
- public launch assets;
- cross-companion group pack.

## Priority 4

- motion;
- sound;
- user markings;
- merchandise/physical derivatives.

---

# 21. Definition of done

The final pack is complete when:

- one canonical model exists;
- editable source is retained;
- front/side/back/three-quarter views match;
- core avatar works at 64 px;
- all ten runtime states are approved;
- ChaseOS UI uses released assets;
- user-instance naming is implemented without identity confusion;
- surface-marking personalisation is bounded;
- Hermes/OpenClaw/Codex/Claude Code coexistence rules are implemented;
- all files have manifests and hashes;
- both repositories share the same canon version;
- public assets pass platform QA;
- operator approval is recorded.
