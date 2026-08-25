# Chaser Agent Website Media Handoff

This release candidate is prepared for a later implementation pass across chasintech.com, chaseos.ai, and repository presentation. No website or public endpoint has been changed by this work.

## Recommended placements

| Surface | Preferred asset | Use |
| --- | --- | --- |
| chasintech.com hero | `web/chaser-agent_web-hero_studio-dark_1920x1080.avif` with WebP/PNG fallback | Wide introductory hero with copy space on the left |
| Product section | `web/chaser-agent_neutral-front_transparent_1800x2400.webp` | Transparent full-body composition |
| chaseos.ai agent identity | `web/chaser-agent_head-shoulders_transparent_2048x2048.webp` | Agent card, feature panel, or onboarding |
| GitHub README/docs | `model-sheet/chaser-agent_model-sheet_operator-approved_4096x3072.png` | Canon and implementation reference |
| Model review | `review/chaser-agent_review-front-centered_studio-dark_1920x1080.png` | Centered, distraction-free visual inspection |
| Profile/icon | `avatar/chaser-agent_avatar-circle-dark_512x512.png` or transparent size ladder | Platform-specific identity |
| Motion showcase | `turntable/chaser-agent_turntable-studio_720x720_h264.mp4` with WebM alternative | Clean model reveal or loop |

## Video direction

Use the clean studio turntable for mascot presentation. Blender viewport video showing the grid, coordinates, axes, panels, or XYZ gizmo is behind-the-scenes evidence only. When Recordly capture begins, record the real product interaction separately and combine it with approved clean mascot media during editing.

The website hero is compositionally offset by design so text can occupy the left side. Do not use that crop to judge model centering; use the centered review stills, model sheet, or turntable.

## Remaining gate

Before website implementation, the operator should review the final full-resolution stills, avatars, model sheet, and complete turntable. After approval, copy exact versioned assets by hash into each consuming repository, preserve attribution to `1.0.0-rc.1` (or its promoted final version), and run responsive/browser QA before any deployment.
