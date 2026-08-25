# Chaser Agent Canon/Core 1.0.0-rc.1 QA

Date: `2026-08-25`

## Source and approval boundary

- The operator approved the v0.37.0 visual model on 2026-08-24.
- The source SHA-256 is locked to `ba2872e369b191592434ec702176b562af9f69f1e99b08aadac445faaa8d4608`.
- Export work changed cameras, framing, backgrounds, and derivative presentation only. It did not modify or save over the approved model.
- Approval covers the neutral visual model. It does not cover a complete runtime-state pack, website implementation, deployment, or public release.

## Visual readback

- Draft 1 exposed full-body crop and spacing problems and was rejected.
- Draft 2 corrected full-body padding, avatar crop safety, and hero copy space.
- High-resolution front, three-quarter, side, back, head, hero, avatar, silhouette, model-sheet, and height-comparison outputs received technical readback.
- The avatar remains recognizable at 64 px. The 32 px and 16 px variants are utility fallbacks and intentionally lose surface detail.
- Public turntable media is camera-rendered studio imagery without Blender interface, grid, axis, or XYZ overlays.
- `turntable-contact-sheet.png` samples eight evenly spaced angles and passed technical readback for framing and visual continuity.

## Mechanical checks

The release-candidate manifest is the byte-level evidence record. Repository tests verify the locked source hash, required files and dimensions, all listed SHA-256 values, 48 turntable frames, GLB identity, and the not-published boundaries.

Focused verification result: `15 passed in 14.82s` for the canon lock, naming conformance, and Canon/Core release-candidate contract tests.

Human operator approval remains the final authority for canonical promotion and website use.
