# Chaser Agent Canon/Core Assets 1.0.0-rc.1

Status: `OPERATOR-APPROVED VISUAL MODEL / RELEASE CANDIDATE / NOT PUBLISHED`.

This bundle contains deterministic derivatives of production model v0.37.0:

- `masters/`: transparent neutral front, three-quarter, side, back, and head-and-shoulders PNG masters.
- `avatar/`: transparent size ladder from 1024 px to 16 px plus dark, light, round, and rounded previews.
- `silhouette/`: solid black and white transparent silhouettes.
- `model-sheet/`: four-view production sheet and canonical target-height comparison.
- `review/`: centered front and three-quarter studio stills for judging the mascot without website-layout offsets.
- `web/`: studio hero and optimized WebP/AVIF derivatives.
- `turntable/`: 48 clean studio frames, poster, H.264 MP4, and VP9 WebM.
- `interoperability/`: GLB model for downstream technical evaluation.

The preferred website starting points are the AVIF/WebP studio hero, transparent front or three-quarter WebP, head-and-shoulders WebP, and clean MP4/WebM turntable. The wide hero intentionally places the mascot to the right to preserve left-side copy space; use `review/` when evaluating centering and model quality. Use PNG masters where lossless alpha or print-quality review is required.

Do not use Blender viewport recordings, grids, axes, coordinate text, or XYZ gizmos in public presentation. These assets have not been deployed to chasintech.com or chaseos.ai, and the release candidate has not been published.
