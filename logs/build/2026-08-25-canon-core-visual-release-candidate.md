# 2026-08-25 - Chaser Agent Canon/Core Visual Release Candidate

## Repo-truth delta

The brand directory previously described production reconstruction as pending. The operator has now visually approved neutral production model v0.37.0, and the repository contains a deterministic Canon/Core asset release candidate `1.0.0-rc.1`.

This does not promote the asset pack to a public release, complete the runtime-state pack, implement either website, or deploy anything.

## Source and storage

- Worktree: `E:\ChaseOSBuilds\2026-08-25-chaser-agent-canon-core\worktree`
- Branch: `codex/2026-08-25-chaser-agent-canon-core`
- Approved source SHA-256: `ba2872e369b191592434ec702176b562af9f69f1e99b08aadac445faaa8d4608`
- Blender: `5.2.0 LTS`
- Export bundle: 77 files and 69,466,554 bytes before manifest generation
- No file is 100 MiB or larger

## Implemented

- Installed the approved `.blend` source without modifying it.
- Added hash-validating Blender export automation and deterministic PowerShell derivative builders.
- Rendered transparent turnaround/head masters, a studio web hero, avatars from 1024 px to 16 px, solid silhouettes, a four-view model sheet, and a target-height comparison.
- Rendered 48 clean 720 px turntable frames and encoded four-second H.264 and VP9 videos at 24 fps.
- Exported a GLB interoperability model.
- Added a hash, byte-length, format, dimension, policy, and release-boundary manifest containing 80 records including the locked source.
- Added QA and website-media handoff documentation.
- Marked binary media types in `.gitattributes`.

## Centered review correction

The initial wide hero intentionally positioned the mascot on the right for website copy space, but that composition was not suitable as the primary model-inspection image. Added centered 1920x1080 front and three-quarter studio renders under `exports/canon-core/v1.0.0-rc.1/review/`. The offset hero remains available and is now explicitly documented as a website-layout variant.

## Visual QA

The first framing draft was rejected for cropping. The corrected high-resolution stills passed technical readback. An eight-angle turntable contact sheet passed for framing, anatomy continuity, botanical-marking continuity, visor treatment, and clean studio presentation. Blender interface, grids, coordinate labels, axes, and XYZ gizmos are excluded from public media.

## Verification

```text
python -m pytest tests/test_brand_canon.py tests/test_brand_canon_conformance.py tests/test_brand_canon_core_release_candidate.py
15 passed in 14.82s

git diff --check
passed

ffprobe H.264: 720x720, yuv420p, 24 fps, 4.000 seconds
ffprobe VP9: 720x720, yuv420p, 24 fps, 4.000 seconds
```

The manifest tests rehash every recorded file, verify PNG dimensions, require exactly 48 turntable frames, and verify the GLB magic header.

## Untouched boundaries

- No push, merge, GitHub release, deployment, public upload, or consuming-site implementation.
- No mutation of the ChaseOS canonical vault.
- No change to the existing canon sync manifest's `asset_release_version: null`; the new bundle remains a separate release candidate.
- No modification of unrelated dirty work in the original C: checkout.

## Next safe action

The operator reviews the final stills, avatars, model sheet, and complete clean turntable. Once explicitly approved for promotion, assign the final asset release version, update the canonical sync manifest, and integrate exact hashed assets into chasintech.com and chaseos.ai in isolated website worktrees before browser QA and any deployment gate.
