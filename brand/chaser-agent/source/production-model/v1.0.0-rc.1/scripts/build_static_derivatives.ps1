param()

$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.Drawing

$brandRoot = Split-Path (Split-Path (Split-Path (Split-Path $PSScriptRoot -Parent) -Parent) -Parent) -Parent
$exportRoot = Join-Path $brandRoot 'exports\canon-core\v1.0.0-rc.1'
$masterRoot = Join-Path $exportRoot 'masters'
$avatarRoot = Join-Path $exportRoot 'avatar'
$modelSheetRoot = Join-Path $exportRoot 'model-sheet'
$webRoot = Join-Path $exportRoot 'web'
$headMaster = Join-Path $masterRoot 'chaser-agent_head-shoulders_transparent_2048x2048.png'
$frontMaster = Join-Path $masterRoot 'chaser-agent_neutral-front_transparent_1800x2400.png'
$silhouetteWhite = Join-Path $exportRoot 'silhouette\chaser-agent_silhouette-white_1024x1536.png'

New-Item -ItemType Directory -Force -Path $avatarRoot, $modelSheetRoot, $webRoot | Out-Null

function New-Canvas([int]$width, [int]$height, [System.Drawing.Color]$colour) {
    $bitmap = New-Object System.Drawing.Bitmap($width, $height, [System.Drawing.Imaging.PixelFormat]::Format32bppArgb)
    $graphics = [System.Drawing.Graphics]::FromImage($bitmap)
    $graphics.Clear($colour)
    $graphics.CompositingMode = [System.Drawing.Drawing2D.CompositingMode]::SourceOver
    $graphics.CompositingQuality = [System.Drawing.Drawing2D.CompositingQuality]::HighQuality
    $graphics.InterpolationMode = [System.Drawing.Drawing2D.InterpolationMode]::HighQualityBicubic
    $graphics.SmoothingMode = [System.Drawing.Drawing2D.SmoothingMode]::HighQuality
    $graphics.PixelOffsetMode = [System.Drawing.Drawing2D.PixelOffsetMode]::HighQuality
    return @($bitmap, $graphics)
}

function Save-Png($bitmap, [string]$path) {
    $bitmap.Save($path, [System.Drawing.Imaging.ImageFormat]::Png)
    Write-Output "PNG=$path"
}

function Resize-Transparent([string]$inputPath, [string]$outputPath, [int]$width, [int]$height) {
    $source = [System.Drawing.Image]::FromFile($inputPath)
    $parts = New-Canvas $width $height ([System.Drawing.Color]::Transparent)
    $bitmap, $graphics = $parts
    $graphics.DrawImage($source, 0, 0, $width, $height)
    Save-Png $bitmap $outputPath
    $graphics.Dispose(); $bitmap.Dispose(); $source.Dispose()
}

function Rounded-Path([System.Drawing.RectangleF]$rect, [float]$radius) {
    $diameter = $radius * 2
    $path = New-Object System.Drawing.Drawing2D.GraphicsPath
    $path.AddArc($rect.X, $rect.Y, $diameter, $diameter, 180, 90)
    $path.AddArc($rect.Right - $diameter, $rect.Y, $diameter, $diameter, 270, 90)
    $path.AddArc($rect.Right - $diameter, $rect.Bottom - $diameter, $diameter, $diameter, 0, 90)
    $path.AddArc($rect.X, $rect.Bottom - $diameter, $diameter, $diameter, 90, 90)
    $path.CloseFigure()
    return $path
}

function Make-AvatarPreview([string]$outputPath, [bool]$circle, [System.Drawing.Color]$background) {
    $source = [System.Drawing.Image]::FromFile($headMaster)
    $parts = New-Canvas 512 512 ([System.Drawing.Color]::Transparent)
    $bitmap, $graphics = $parts
    $rect = New-Object System.Drawing.RectangleF(8, 8, 496, 496)
    if ($circle) {
        $path = New-Object System.Drawing.Drawing2D.GraphicsPath
        $path.AddEllipse($rect)
    } else {
        $path = Rounded-Path $rect 76
    }
    $graphics.FillPath((New-Object System.Drawing.SolidBrush($background)), $path)
    $graphics.SetClip($path)
    $graphics.DrawImage($source, 18, 18, 476, 476)
    $graphics.ResetClip()
    $ring = New-Object System.Drawing.Pen([System.Drawing.ColorTranslator]::FromHtml('#39E6D2'), 4)
    $graphics.DrawPath($ring, $path)
    Save-Png $bitmap $outputPath
    $ring.Dispose(); $path.Dispose(); $graphics.Dispose(); $bitmap.Dispose(); $source.Dispose()
}

foreach ($size in @(1024, 512, 256, 128, 64, 32, 16)) {
    Resize-Transparent $headMaster (Join-Path $avatarRoot "chaser-agent_avatar-transparent_${size}x${size}.png") $size $size
}

Make-AvatarPreview (Join-Path $avatarRoot 'chaser-agent_avatar-circle-dark_512x512.png') $true ([System.Drawing.ColorTranslator]::FromHtml('#070B14'))
Make-AvatarPreview (Join-Path $avatarRoot 'chaser-agent_avatar-rounded-dark_512x512.png') $false ([System.Drawing.ColorTranslator]::FromHtml('#070B14'))
Make-AvatarPreview (Join-Path $avatarRoot 'chaser-agent_avatar-rounded-light_512x512.png') $false ([System.Drawing.ColorTranslator]::FromHtml('#F4F1EA'))

# Four-view production model sheet.
$sheetParts = New-Canvas 4096 3072 ([System.Drawing.ColorTranslator]::FromHtml('#070B14'))
$sheet, $g = $sheetParts
$titleFont = New-Object System.Drawing.Font('Segoe UI Semibold', 62)
$subFont = New-Object System.Drawing.Font('Segoe UI', 28)
$labelFont = New-Object System.Drawing.Font('Cascadia Mono', 28)
$white = New-Object System.Drawing.SolidBrush([System.Drawing.ColorTranslator]::FromHtml('#F4F1EA'))
$teal = New-Object System.Drawing.SolidBrush([System.Drawing.ColorTranslator]::FromHtml('#39E6D2'))
$muted = New-Object System.Drawing.SolidBrush([System.Drawing.ColorTranslator]::FromHtml('#7EA1AC'))
$g.DrawString('CHASER AGENT', $titleFont, $teal, 112, 72)
$g.DrawString('Operator-approved visual model | v0.37.0 | Canon/Core asset release candidate 1.0.0-rc.1', $subFont, $white, 116, 158)

$views = @(
    @('FRONT', 'chaser-agent_neutral-front_transparent_1800x2400.png'),
    @('3/4', 'chaser-agent_neutral-three-quarter_transparent_1800x2400.png'),
    @('SIDE', 'chaser-agent_neutral-side_transparent_1800x2400.png'),
    @('BACK', 'chaser-agent_neutral-back_transparent_1800x2400.png')
)
for ($index = 0; $index -lt $views.Count; $index++) {
    $x = 112 + ($index * 990)
    $panel = New-Object System.Drawing.RectangleF($x, 270, 900, 2320)
    $panelPath = Rounded-Path $panel 36
    $g.FillPath((New-Object System.Drawing.SolidBrush([System.Drawing.Color]::FromArgb(92, 18, 30, 43))), $panelPath)
    $img = [System.Drawing.Image]::FromFile((Join-Path $masterRoot $views[$index][1]))
    $scale = [Math]::Min(810 / $img.Width, 2150 / $img.Height)
    $drawWidth = [int]($img.Width * $scale)
    $drawHeight = [int]($img.Height * $scale)
    $drawX = [int]($x + (900 - $drawWidth) / 2)
    $drawY = [int](340 + (2170 - $drawHeight) / 2)
    $g.DrawImage($img, $drawX, $drawY, $drawWidth, $drawHeight)
    $g.DrawString($views[$index][0], $labelFont, $white, $x + 28, 2510)
    $img.Dispose(); $panelPath.Dispose()
}

$swatches = @(
    @('INK', '#070B14'), @('MINERAL BODY', '#7EA1AC'), @('RUNTIME TEAL', '#39E6D2'),
    @('APPROVAL AMBER', '#F0B45A'), @('BLOCKED RED', '#FF4D6D'), @('BONE', '#F4F1EA')
)
for ($index = 0; $index -lt $swatches.Count; $index++) {
    $x = 118 + ($index * 650)
    $brush = New-Object System.Drawing.SolidBrush([System.Drawing.ColorTranslator]::FromHtml($swatches[$index][1]))
    $g.FillRectangle($brush, $x, 2760, 120, 80)
    $g.DrawString($swatches[$index][0], $labelFont, $white, $x + 142, 2773)
    $g.DrawString($swatches[$index][1], $labelFont, $muted, $x + 142, 2818)
    $brush.Dispose()
}
$g.DrawString('Visual approval recorded 2026-08-24 | Not yet a full canonical state pack or public release', $subFont, $white, 116, 2960)
Save-Png $sheet (Join-Path $modelSheetRoot 'chaser-agent_model-sheet_operator-approved_4096x3072.png')
$g.Dispose(); $sheet.Dispose(); $titleFont.Dispose(); $subFont.Dispose(); $labelFont.Dispose(); $white.Dispose(); $teal.Dispose(); $muted.Dispose()

# Height comparison: canonical target height, not Blender scene-unit measurement.
$heightParts = New-Canvas 2048 2048 ([System.Drawing.ColorTranslator]::FromHtml('#070B14'))
$heightSheet, $hg = $heightParts
$humanPen = New-Object System.Drawing.Pen([System.Drawing.ColorTranslator]::FromHtml('#F4F1EA'), 18)
$guidePen = New-Object System.Drawing.Pen([System.Drawing.ColorTranslator]::FromHtml('#39E6D2'), 5)
$label = New-Object System.Drawing.Font('Segoe UI Semibold', 40)
$small = New-Object System.Drawing.Font('Cascadia Mono', 26)
$hg.DrawString('CANONICAL HEIGHT COMPARISON', $label, (New-Object System.Drawing.SolidBrush([System.Drawing.ColorTranslator]::FromHtml('#39E6D2'))), 96, 64)
$floorY = 1820
$hg.DrawLine($guidePen, 100, $floorY, 1948, $floorY)
$humanTop = 250; $humanBottom = $floorY; $humanX = 1480
$hg.DrawEllipse($humanPen, $humanX - 92, $humanTop, 184, 184)
$hg.DrawLine($humanPen, $humanX, $humanTop + 184, $humanX, 1130)
$hg.DrawLine($humanPen, $humanX, 520, $humanX - 250, 980)
$hg.DrawLine($humanPen, $humanX, 520, $humanX + 250, 980)
$hg.DrawLine($humanPen, $humanX, 1130, $humanX - 170, $humanBottom)
$hg.DrawLine($humanPen, $humanX, 1130, $humanX + 170, $humanBottom)
$model = [System.Drawing.Image]::FromFile($silhouetteWhite)
$modelHeight = [int](($humanBottom - $humanTop) * (0.90 / 1.75))
$modelWidth = [int]($modelHeight * ($model.Width / $model.Height))
$hg.DrawImage($model, 390 - [int]($modelWidth / 2), $floorY - $modelHeight, $modelWidth, $modelHeight)
$hg.DrawString('CHASER AGENT', $small, (New-Object System.Drawing.SolidBrush([System.Drawing.ColorTranslator]::FromHtml('#39E6D2'))), 205, 1870)
$hg.DrawString('0.90 m target', $small, (New-Object System.Drawing.SolidBrush([System.Drawing.ColorTranslator]::FromHtml('#F4F1EA'))), 210, 1910)
$hg.DrawString('REFERENCE HUMAN', $small, (New-Object System.Drawing.SolidBrush([System.Drawing.ColorTranslator]::FromHtml('#F4F1EA'))), 1300, 1870)
$hg.DrawString('1.75 m', $small, (New-Object System.Drawing.SolidBrush([System.Drawing.ColorTranslator]::FromHtml('#7EA1AC'))), 1390, 1910)
Save-Png $heightSheet (Join-Path $modelSheetRoot 'chaser-agent_height-comparison_2048x2048.png')
$model.Dispose(); $hg.Dispose(); $heightSheet.Dispose(); $humanPen.Dispose(); $guidePen.Dispose(); $label.Dispose(); $small.Dispose()

# Web-ready deterministic derivatives.
$heroPng = Join-Path $webRoot 'chaser-agent_web-hero_studio-dark_1920x1080.png'
& ffmpeg -loglevel error -y -i $heroPng -c:v libwebp -quality 90 (Join-Path $webRoot 'chaser-agent_web-hero_studio-dark_1920x1080.webp')
& ffmpeg -loglevel error -y -i $heroPng -c:v libaom-av1 -crf 28 -still-picture 1 (Join-Path $webRoot 'chaser-agent_web-hero_studio-dark_1920x1080.avif')
& ffmpeg -loglevel error -y -i $frontMaster -c:v libwebp -quality 92 (Join-Path $webRoot 'chaser-agent_neutral-front_transparent_1800x2400.webp')
& ffmpeg -loglevel error -y -i $headMaster -c:v libwebp -quality 92 (Join-Path $webRoot 'chaser-agent_head-shoulders_transparent_2048x2048.webp')
Write-Output "DERIVATIVES_COMPLETE=$exportRoot"
