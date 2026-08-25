param()

$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.Drawing

$repoRoot = (& git -C $PSScriptRoot rev-parse --show-toplevel).Trim()
$brandRoot = Join-Path $repoRoot 'brand\chaser-agent'
$sourceModel = Join-Path $brandRoot 'source\production-model\v1.0.0-rc.1\chaser-agent_production-model_operator-approved_v0.37.0_20260824.blend'
$exportRoot = Join-Path $brandRoot 'exports\canon-core\v1.0.0-rc.1'
$manifestPath = Join-Path $brandRoot 'manifests\chaser-agent_canon-core_v1.0.0-rc.1.json'

function Relative-Path([string]$path) {
    $rootPrefix = [System.IO.Path]::GetFullPath($repoRoot).TrimEnd('\') + '\'
    $resolved = [System.IO.Path]::GetFullPath($path)
    if (-not $resolved.StartsWith($rootPrefix, [System.StringComparison]::OrdinalIgnoreCase)) {
        throw "Asset is outside the repository root: $resolved"
    }
    return $resolved.Substring($rootPrefix.Length).Replace('\', '/')
}

function Asset-Role([string]$path) {
    $normal = $path.Replace('\', '/').ToLowerInvariant()
    if ($normal.EndsWith('.blend')) { return 'editable-source-model' }
    if ($normal.Contains('/masters/')) { return 'character-master' }
    if ($normal.Contains('/avatar/')) { return 'avatar' }
    if ($normal.Contains('/silhouette/')) { return 'silhouette' }
    if ($normal.Contains('/model-sheet/')) { return 'model-sheet' }
    if ($normal.Contains('/interoperability/')) { return 'interoperability-model' }
    if ($normal.Contains('/turntable/frames/')) { return 'turntable-frame' }
    if ($normal.Contains('/turntable/')) { return 'turntable-media' }
    if ($normal.Contains('/web/')) { return 'web-media' }
    return 'supporting-asset'
}

function Dimensions([System.IO.FileInfo]$file) {
    if ($file.Extension.ToLowerInvariant() -eq '.png') {
        $image = [System.Drawing.Image]::FromFile($file.FullName)
        $result = @($image.Width, $image.Height)
        $image.Dispose()
        return $result
    }
    if ($file.Extension.ToLowerInvariant() -in @('.webp', '.avif', '.mp4', '.webm')) {
        $value = (& ffprobe -v error -select_streams v:0 -show_entries stream=width,height -of csv=s=x:p=0 $file.FullName).Trim()
        if ($LASTEXITCODE -eq 0 -and $value -match '^(\d+)x(\d+)$') {
            return @([int]$Matches[1], [int]$Matches[2])
        }
    }
    return @($null, $null)
}

$files = @((Get-Item $sourceModel)) + @(Get-ChildItem $exportRoot -Recurse -File)
$assets = foreach ($file in ($files | Sort-Object FullName)) {
    $width, $height = Dimensions $file
    [ordered]@{
        path = Relative-Path $file.FullName
        role = Asset-Role $file.FullName
        format = $file.Extension.TrimStart('.').ToLowerInvariant()
        bytes = $file.Length
        width = $width
        height = $height
        sha256 = (Get-FileHash $file.FullName -Algorithm SHA256).Hash.ToLowerInvariant()
    }
}

$manifest = [ordered]@{
    schema_version = 1
    canon_id = 'chaser-agent'
    canon_version = '1.0.0'
    asset_release_version = '1.0.0-rc.1'
    model_version = 'v0.37.0'
    status = 'operator-approved-canon-core-release-candidate-not-public-release'
    generated_on = '2026-08-25'
    public_name = 'Chaser Agent'
    source_model = [ordered]@{
        path = Relative-Path $sourceModel
        sha256 = (Get-FileHash $sourceModel -Algorithm SHA256).Hash.ToLowerInvariant()
        operator_visual_approved = $true
        operator_approved_on = '2026-08-24'
    }
    content = [ordered]@{
        transparent_turnaround_masters = 4
        head_shoulders_master = 1
        avatar_png_sizes = @(1024, 512, 256, 128, 64, 32, 16)
        avatar_previews = @('circle-dark', 'rounded-dark', 'rounded-light')
        silhouette_variants = @('black', 'white')
        model_sheets = @('four-view', 'height-comparison')
        centered_review_stills = 2
        clean_turntable_frames = 48
        clean_turntable_video_formats = @('mp4', 'webm')
        interoperability = @('glb')
    }
    public_media_policy = [ordered]@{
        clean_camera_renders_only = $true
        blender_viewport_ui_public_use = $false
        xyz_gizmo_public_use = $false
        recordly_product_capture = 'deferred-separate-pass'
    }
    boundaries = [ordered]@{
        full_runtime_state_pack_complete = $false
        canonical_asset_release_published = $false
        github_release_published = $false
        chasintech_implemented = $false
        chaseos_ai_implemented = $false
        deployed = $false
    }
    assets = @($assets)
}

New-Item -ItemType Directory -Force -Path (Split-Path $manifestPath) | Out-Null
$json = $manifest | ConvertTo-Json -Depth 8
[System.IO.File]::WriteAllText($manifestPath, $json + [Environment]::NewLine, [System.Text.UTF8Encoding]::new($false))
Write-Output "MANIFEST=$manifestPath"
Write-Output "ASSETS=$($assets.Count)"
