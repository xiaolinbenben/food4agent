param(
  [Parameter(Mandatory = $true)]
  [string]$RawProductJson,

  [string]$OutputDir,

  [string]$ImageWorkspace
)

$ErrorActionPreference = "Stop"

Add-Type -AssemblyName System.Drawing

function Read-JsonFile {
  param([string]$Path)
  return Get-Content -Raw -Encoding UTF8 $Path | ConvertFrom-Json
}

function Write-JsonFile {
  param(
    [string]$Path,
    [object]$Value
  )

  $json = $Value | ConvertTo-Json -Depth 100
  [System.IO.File]::WriteAllText($Path, ($json -join [Environment]::NewLine) + [Environment]::NewLine, [System.Text.UTF8Encoding]::new($false))
}

function Get-UniqueStringArray {
  param([object[]]$Values)

  $result = [System.Collections.Generic.List[string]]::new()
  foreach ($value in $Values) {
    if ($null -eq $value) { continue }

    if ($value -is [System.Collections.IEnumerable] -and -not ($value -is [string])) {
      foreach ($nested in $value) {
        $text = ([string]$nested).Trim()
        if (-not $text) { continue }
        if (-not $result.Contains($text)) { $result.Add($text) }
      }
      continue
    }

    $text = ([string]$value).Trim()
    if (-not $text) { continue }
    if (-not $result.Contains($text)) { $result.Add($text) }
  }

  return $result.ToArray()
}

function Copy-ReusedCandidates {
  param(
    [Parameter(Mandatory = $true)][string]$SourceManifestPath,
    [Parameter(Mandatory = $true)][string]$SourceSheetPath,
    [Parameter(Mandatory = $true)][string]$TargetDir
  )

  New-Item -ItemType Directory -Force -Path $TargetDir | Out-Null
  $targetFilesDir = Join-Path $TargetDir "files"
  New-Item -ItemType Directory -Force -Path $targetFilesDir | Out-Null

  $sourceManifest = Read-JsonFile -Path $SourceManifestPath
  $records = @()

  if ($sourceManifest.records) {
    foreach ($item in @($sourceManifest.records)) {
      if (-not $item.local_file_path) { continue }
      $sourceFile = [string]$item.local_file_path
      if (-not (Test-Path -LiteralPath $sourceFile)) { continue }
      $fileName = Split-Path -Leaf $sourceFile
      $targetFile = Join-Path $targetFilesDir $fileName
      Copy-Item -LiteralPath $sourceFile -Destination $targetFile -Force

      $records += [pscustomobject]@{
        index = $item.index
        url = $item.image_url
        file = $targetFile
        ok = ($item.status -like 'downloaded*')
        width = $item.width
        height = $item.height
        reused_from = $sourceFile
      }
    }
  } else {
    foreach ($item in @($sourceManifest)) {
      if (-not $item.file) { continue }
      $sourceFile = [string]$item.file
      if (-not (Test-Path -LiteralPath $sourceFile)) { continue }
      $fileName = Split-Path -Leaf $sourceFile
      $targetFile = Join-Path $targetFilesDir $fileName
      Copy-Item -LiteralPath $sourceFile -Destination $targetFile -Force

      $records += [pscustomobject]@{
        index = $item.index
        url = $item.url
        file = $targetFile
        ok = [bool]$item.ok
        width = $item.width
        height = $item.height
        reused_from = $sourceFile
      }
    }
  }

  $targetManifestPath = Join-Path $TargetDir "manifest.json"
  Write-JsonFile -Path $TargetManifestPath -Value $records

  $sheetExt = [System.IO.Path]::GetExtension($SourceSheetPath)
  if (-not $sheetExt) { $sheetExt = ".jpg" }
  $targetSheetPath = Join-Path $TargetDir ("contact-sheet" + $sheetExt)
  Copy-Item -LiteralPath $SourceSheetPath -Destination $targetSheetPath -Force

  return [pscustomobject]@{
    manifest_path = $targetManifestPath
    contact_sheet_path = $targetSheetPath
    downloaded_count = @($records | Where-Object { $_.ok }).Count
  }
}

$rawPath = (Resolve-Path -LiteralPath $RawProductJson).Path
$raw = Read-JsonFile -Path $rawPath
$offerId = [string]$raw.source.offer_id
if (-not $offerId) { $offerId = "unknown-offer" }

$rawDir = Split-Path -Parent $rawPath
if (-not $ImageWorkspace) {
  $ImageWorkspace = Join-Path $rawDir "image"
}

if (-not $OutputDir) {
  $OutputDir = Join-Path $env:TEMP ("codex-sizechart-" + $offerId)
}

$reusedManifestPath = Join-Path $ImageWorkspace "candidates\\manifest.json"
$reusedSheetJpg = Join-Path $ImageWorkspace "candidates\\contact-sheet.jpg"
$reusedSheetPng = Join-Path $ImageWorkspace "candidates\\contact-sheet.png"
$reusedSheetPath = if (Test-Path -LiteralPath $reusedSheetJpg) { $reusedSheetJpg } elseif (Test-Path -LiteralPath $reusedSheetPng) { $reusedSheetPng } else { "" }

if ((Test-Path -LiteralPath $reusedManifestPath) -and $reusedSheetPath) {
  $reused = Copy-ReusedCandidates -SourceManifestPath $reusedManifestPath -SourceSheetPath $reusedSheetPath -TargetDir $OutputDir
  [pscustomobject]@{
    offer_id = $offerId
    output_dir = $OutputDir
    manifest_path = $reused.manifest_path
    contact_sheet_path = $reused.contact_sheet_path
    candidate_count = @((Read-JsonFile -Path $reused.manifest_path)).Count
    downloaded_count = $reused.downloaded_count
    reused_existing_candidates = $true
    reused_manifest_path = $reusedManifestPath
    reused_contact_sheet_path = $reusedSheetPath
  } | ConvertTo-Json -Depth 10
  exit 0
}

New-Item -ItemType Directory -Force -Path $OutputDir | Out-Null
$filesDir = Join-Path $OutputDir "files"
New-Item -ItemType Directory -Force -Path $filesDir | Out-Null

$urls = Get-UniqueStringArray @(
  $raw.structured.shein_required_fields.size_chart.image_urls,
  $raw.structured.description.detail_images,
  $raw.structured.images.detail_images,
  $raw.structured.images.all
)

$records = [System.Collections.Generic.List[object]]::new()
$index = 0
foreach ($url in $urls) {
  $index++
  $ext = if ($url -match '\.webp($|\?)') { ".webp" } elseif ($url -match '\.png($|\?)') { ".png" } else { ".jpg" }
  $file = Join-Path $filesDir ("{0:D2}{1}" -f $index, $ext)

  try {
    Invoke-WebRequest -Uri $url -OutFile $file -TimeoutSec 20 -UseBasicParsing | Out-Null
    $img = [System.Drawing.Image]::FromFile($file)
    $records.Add([pscustomobject]@{
      index = $index
      url = $url
      file = $file
      ok = $true
      width = $img.Width
      height = $img.Height
      reused_from = ""
    })
    $img.Dispose()
  } catch {
    $records.Add([pscustomobject]@{
      index = $index
      url = $url
      file = $file
      ok = $false
      error = $_.Exception.Message
      reused_from = ""
    })
  }
}

$manifestPath = Join-Path $OutputDir "manifest.json"
Write-JsonFile -Path $manifestPath -Value $records.ToArray()

$okItems = @($records.ToArray() | Where-Object { $_.ok })
$sheetPath = Join-Path $OutputDir "contact-sheet.png"

if ($okItems.Count -gt 0) {
  $thumbW = 220
  $thumbH = 220
  $labelH = 32
  $cols = 4
  $rows = [Math]::Ceiling($okItems.Count / $cols)
  $bmp = New-Object System.Drawing.Bitmap ($cols * $thumbW), ($rows * ($thumbH + $labelH))
  $g = [System.Drawing.Graphics]::FromImage($bmp)
  $g.Clear([System.Drawing.Color]::White)
  $font = New-Object System.Drawing.Font("Arial", 12)
  $brush = [System.Drawing.Brushes]::Black

  try {
    for ($idx = 0; $idx -lt $okItems.Count; $idx++) {
      $item = $okItems[$idx]
      $img = [System.Drawing.Image]::FromFile($item.file)
      try {
        $col = $idx % $cols
        $row = [Math]::Floor($idx / $cols)
        $x = $col * $thumbW
        $y = $row * ($thumbH + $labelH)
        $scale = [Math]::Min(($thumbW - 10) / $img.Width, ($thumbH - 10) / $img.Height)
        $dw = [int]($img.Width * $scale)
        $dh = [int]($img.Height * $scale)
        $dx = $x + [int](($thumbW - $dw) / 2)
        $dy = $y + 5 + [int](($thumbH - $dh) / 2)

        $g.DrawImage($img, $dx, $dy, $dw, $dh)
        $g.DrawRectangle([System.Drawing.Pens]::LightGray, $x, $y, $thumbW - 1, $thumbH + $labelH - 1)
        $label = ("{0:D2}  {1}x{2}" -f $item.index, $img.Width, $img.Height)
        $g.DrawString($label, $font, $brush, $x + 6, $y + $thumbH + 6)
      } finally {
        $img.Dispose()
      }
    }

    $bmp.Save($sheetPath, [System.Drawing.Imaging.ImageFormat]::Png)
  } finally {
    $g.Dispose()
    $bmp.Dispose()
    $font.Dispose()
  }
}

[pscustomobject]@{
  offer_id = $offerId
  output_dir = $OutputDir
  manifest_path = $manifestPath
  contact_sheet_path = if (Test-Path $sheetPath) { $sheetPath } else { "" }
  candidate_count = $urls.Count
  downloaded_count = $okItems.Count
  reused_existing_candidates = $false
  reused_manifest_path = ""
  reused_contact_sheet_path = ""
} | ConvertTo-Json -Depth 10
