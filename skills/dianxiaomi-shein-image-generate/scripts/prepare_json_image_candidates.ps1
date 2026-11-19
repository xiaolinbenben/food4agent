[CmdletBinding(PositionalBinding = $false)]
param(
  [Parameter(Mandatory = $true)]
  [string] $RawProductJson,

  [string] $ImageWorkspace = '',

  [int] $Columns = 5,

  [int] $ThumbSize = 180
)

$ErrorActionPreference = 'Stop'

function Resolve-RequiredFile {
  param([Parameter(Mandatory = $true)][string] $Path)
  $resolved = Resolve-Path -LiteralPath $Path -ErrorAction Stop
  return $resolved.ProviderPath
}

function Get-ImageExtension {
  param([Parameter(Mandatory = $true)][string] $Url)
  $path = ([uri] $Url).AbsolutePath
  $ext = [IO.Path]::GetExtension($path).ToLowerInvariant()
  if ($ext -in @('.jpg', '.jpeg', '.png', '.webp')) {
    return $ext
  }
  return '.jpg'
}

function Save-Json {
  param(
    [Parameter(Mandatory = $true)] $Value,
    [Parameter(Mandatory = $true)][string] $Path
  )
  $jsonLines = ConvertTo-Json -InputObject $Value -Depth 20
  $jsonText = @($jsonLines) -join [Environment]::NewLine
  Set-Content -LiteralPath $Path -Value $jsonText -Encoding UTF8
}

$rawPath = Resolve-RequiredFile -Path $RawProductJson
$jsonDir = Split-Path -Parent $rawPath
if ([string]::IsNullOrWhiteSpace($ImageWorkspace)) {
  $ImageWorkspace = Join-Path $jsonDir 'image'
}

$candidateDir = Join-Path $ImageWorkspace 'candidates'
$fileDir = Join-Path $candidateDir 'files'
New-Item -ItemType Directory -Force -Path $fileDir | Out-Null

$rawText = Get-Content -LiteralPath $rawPath -Raw -Encoding UTF8
$normalized = $rawText -replace '\\/', '/'
$matches = [regex]::Matches($normalized, 'https?://[^"''<>\s\\]+?\.(?:jpg|jpeg|png|webp)(?:\?[^"''<>\s\\]*)?', [Text.RegularExpressions.RegexOptions]::IgnoreCase)
$urls = New-Object System.Collections.Generic.List[string]
$seen = @{}
foreach ($match in $matches) {
  $url = $match.Value
  if (-not $seen.ContainsKey($url)) {
    $seen[$url] = $true
    [void] $urls.Add($url)
  }
}

if ($urls.Count -eq 0) {
  throw "No image URLs found in $rawPath"
}

Add-Type -AssemblyName System.Drawing
$records = New-Object System.Collections.Generic.List[object]
$index = 1
foreach ($url in $urls) {
  $ext = Get-ImageExtension -Url $url
  $fileName = ('candidate-{0:000}{1}' -f $index, $ext)
  $localPath = Join-Path $fileDir $fileName
  $status = 'downloaded'
  $errorText = $null
  $width = $null
  $height = $null
  $bytes = $null

  try {
    Invoke-WebRequest -Uri $url -OutFile $localPath -TimeoutSec 60
    $bytes = (Get-Item -LiteralPath $localPath).Length
    try {
      $img = [Drawing.Image]::FromFile($localPath)
      $width = $img.Width
      $height = $img.Height
      $img.Dispose()
    } catch {
      $status = 'downloaded_dimension_unreadable'
      $errorText = $_.Exception.Message
    }
  } catch {
    $status = 'download_failed'
    $errorText = $_.Exception.Message
  }

  [void] $records.Add([ordered]@{
    index = $index
    image_url = $url
    local_file_path = $localPath
    width = $width
    height = $height
    file_size_bytes = $bytes
    status = $status
    selected = $true
    exclusion_reason = $null
    error = $errorText
  })
  $index++
}

$sheetPath = Join-Path $candidateDir 'contact-sheet.jpg'
$validRecords = @($records | Where-Object { $_.status -like 'downloaded*' -and (Test-Path -LiteralPath $_.local_file_path) })
if ($validRecords.Count -gt 0) {
  $labelHeight = 34
  $columns = [Math]::Max(1, $Columns)
  $rows = [Math]::Ceiling($validRecords.Count / $columns)
  $cellWidth = $ThumbSize
  $cellHeight = $ThumbSize + $labelHeight
  $sheet = New-Object Drawing.Bitmap ($cellWidth * $columns), ($cellHeight * $rows)
  $graphics = [Drawing.Graphics]::FromImage($sheet)
  $graphics.Clear([Drawing.Color]::White)
  $font = New-Object Drawing.Font 'Arial', 10
  $brush = [Drawing.Brushes]::Black

  for ($i = 0; $i -lt $validRecords.Count; $i++) {
    $record = $validRecords[$i]
    $col = $i % $columns
    $row = [Math]::Floor($i / $columns)
    $x = $col * $cellWidth
    $y = $row * $cellHeight
    try {
      $img = [Drawing.Image]::FromFile($record.local_file_path)
      $scale = [Math]::Min($ThumbSize / $img.Width, $ThumbSize / $img.Height)
      $drawWidth = [int]($img.Width * $scale)
      $drawHeight = [int]($img.Height * $scale)
      $dx = $x + [int](($ThumbSize - $drawWidth) / 2)
      $dy = $y + [int](($ThumbSize - $drawHeight) / 2)
      $graphics.DrawImage($img, $dx, $dy, $drawWidth, $drawHeight)
      $img.Dispose()
    } catch {
      $graphics.DrawString('unreadable', $font, $brush, $x + 4, $y + 70)
    }
    $label = ('#{0} {1}x{2}' -f $record.index, $record.width, $record.height)
    $graphics.DrawString($label, $font, $brush, $x + 4, $y + $ThumbSize + 2)
  }

  $sheet.Save($sheetPath, [Drawing.Imaging.ImageFormat]::Jpeg)
  $graphics.Dispose()
  $sheet.Dispose()
  $font.Dispose()
}

$manifest = [ordered]@{
  raw_product_json = $rawPath
  image_workspace = $ImageWorkspace
  generated_at = (Get-Date).ToString('s')
  contact_sheet = $sheetPath
  records = @($records.ToArray())
}

$manifestPath = Join-Path $candidateDir 'manifest.json'
Save-Json -Value $manifest -Path $manifestPath

[ordered]@{
  raw_product_json = $rawPath
  image_workspace = $ImageWorkspace
  candidate_count = $records.Count
  manifest_path = $manifestPath
  contact_sheet = $sheetPath
} | ConvertTo-Json -Depth 5 -Compress
