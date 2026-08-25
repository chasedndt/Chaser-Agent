param()

$ErrorActionPreference = 'Stop'
$brandRoot = Split-Path (Split-Path (Split-Path (Split-Path $PSScriptRoot -Parent) -Parent) -Parent) -Parent
$turntableRoot = Join-Path $brandRoot 'exports\canon-core\v1.0.0-rc.1\turntable'
$framePattern = Join-Path $turntableRoot 'frames\chaser-agent_turntable_%03d.png'
$frames = Get-ChildItem (Join-Path $turntableRoot 'frames') -Filter 'chaser-agent_turntable_*.png'
if ($frames.Count -ne 48) {
    throw "Expected 48 clean turntable frames, found $($frames.Count)"
}

$mp4 = Join-Path $turntableRoot 'chaser-agent_turntable-studio_720x720_h264.mp4'
$webm = Join-Path $turntableRoot 'chaser-agent_turntable-studio_720x720_vp9.webm'
$poster = Join-Path $turntableRoot 'chaser-agent_turntable-studio_poster.png'

& ffmpeg -loglevel error -y -framerate 12 -i $framePattern -vf 'fps=24,format=yuv420p' -c:v libx264 -preset slow -crf 18 -movflags +faststart $mp4
if ($LASTEXITCODE -ne 0) { throw 'H.264 turntable encoding failed' }
& ffmpeg -loglevel error -y -framerate 12 -i $framePattern -vf 'fps=24,format=yuv420p' -c:v libvpx-vp9 -crf 28 -b:v 0 -row-mt 1 $webm
if ($LASTEXITCODE -ne 0) { throw 'VP9 turntable encoding failed' }
Copy-Item -LiteralPath (Join-Path $turntableRoot 'frames\chaser-agent_turntable_006.png') -Destination $poster -Force

Write-Output "MP4=$mp4"
Write-Output "WEBM=$webm"
Write-Output "POSTER=$poster"
