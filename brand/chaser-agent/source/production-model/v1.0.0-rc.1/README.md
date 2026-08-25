# Chaser Agent Production Model v0.37.0

Status: `OPERATOR VISUAL APPROVED / CANON-CORE RELEASE CANDIDATE / NOT A PUBLIC RELEASE`.

The Blender source in this directory is the operator-approved neutral Chaser Agent model recorded on 2026-08-24. It is the source for Canon/Core asset candidate `1.0.0-rc.1`.

## Locked source

- File: `chaser-agent_production-model_operator-approved_v0.37.0_20260824.blend`
- SHA-256: `ba2872e369b191592434ec702176b562af9f69f1e99b08aadac445faaa8d4608`
- Authoring/render version: Blender `5.2.0 LTS`
- Approval scope: neutral visual anatomy, materials, markings, and presentation

Do not alter the approved source while creating derivatives. The export script validates the source hash and approval marker before rendering. Camera, background, output, and temporary silhouette-material changes are export-only and are not saved into the source.

## Deterministic export sequence

Run from the repository root. Set `CHASER_EXPORT_MODE` to `masters`, `silhouette`, or `turntable`, then run Blender in background mode with `scripts/export_canon_core.py`. Run the PowerShell builders after their inputs exist:

```powershell
$env:CHASER_EXPORT_MODE = 'masters'
& 'E:\ChaserAgentCreative\Apps\blender-5.2.0-windows-x64\blender.exe' -b '.\brand\chaser-agent\source\production-model\v1.0.0-rc.1\chaser-agent_production-model_operator-approved_v0.37.0_20260824.blend' -P '.\brand\chaser-agent\source\production-model\v1.0.0-rc.1\scripts\export_canon_core.py'

$env:CHASER_EXPORT_MODE = 'silhouette'
& 'E:\ChaserAgentCreative\Apps\blender-5.2.0-windows-x64\blender.exe' -b '.\brand\chaser-agent\source\production-model\v1.0.0-rc.1\chaser-agent_production-model_operator-approved_v0.37.0_20260824.blend' -P '.\brand\chaser-agent\source\production-model\v1.0.0-rc.1\scripts\export_canon_core.py'

& '.\brand\chaser-agent\source\production-model\v1.0.0-rc.1\scripts\build_static_derivatives.ps1'

$env:CHASER_EXPORT_MODE = 'turntable'
& 'E:\ChaserAgentCreative\Apps\blender-5.2.0-windows-x64\blender.exe' -b '.\brand\chaser-agent\source\production-model\v1.0.0-rc.1\chaser-agent_production-model_operator-approved_v0.37.0_20260824.blend' -P '.\brand\chaser-agent\source\production-model\v1.0.0-rc.1\scripts\export_canon_core.py'

& '.\brand\chaser-agent\source\production-model\v1.0.0-rc.1\scripts\build_turntable_video.ps1'
& '.\brand\chaser-agent\source\production-model\v1.0.0-rc.1\scripts\build_release_manifest.ps1'
```

The manifest records byte lengths, dimensions, and SHA-256 hashes for the source and every output.
