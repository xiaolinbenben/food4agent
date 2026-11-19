[CmdletBinding(PositionalBinding = $false)]
param(
  [Parameter(Mandatory = $true)]
  [string] $GeneratedDir,

  [string] $ManifestPath = '',

  [string] $OutputPath = '',

  [int] $MaxBytes = 3145728
)

$ErrorActionPreference = 'Stop'

function Resolve-RequiredFile {
  param([Parameter(Mandatory = $true)][string] $Path)
  $resolved = Resolve-Path -LiteralPath $Path -ErrorAction Stop
  return $resolved.ProviderPath
}

function Ensure-Path {
  param([Parameter(Mandatory = $true)][string] $Path)
  if (-not (Test-Path -LiteralPath $Path)) {
    throw "Path does not exist: $Path"
  }
  return (Resolve-Path -LiteralPath $Path).ProviderPath
}

function Write-JsonFile {
  param(
    [Parameter(Mandatory = $true)] $Value,
    [Parameter(Mandatory = $true)][string] $Path,
    [int] $Depth = 30
  )
  $jsonLines = ConvertTo-Json -InputObject $Value -Depth $Depth
  $jsonText = @($jsonLines) -join [Environment]::NewLine
  Set-Content -LiteralPath $Path -Value $jsonText -Encoding UTF8
}

function Get-ObjectValue {
  param(
    [Parameter(Mandatory = $true)] $Object,
    [Parameter(Mandatory = $true)][string] $Name
  )
  if ($Object -is [System.Collections.IDictionary] -and $Object.Contains($Name)) {
    return $Object[$Name]
  }
  $property = $Object.PSObject.Properties[$Name]
  if (-not $property) { return $null }
  return $property.Value
}

function Test-AspectRatio {
  param(
    [Parameter(Mandatory = $true)][int] $Width,
    [Parameter(Mandatory = $true)][int] $Height,
    [Parameter(Mandatory = $true)][string[]] $AllowedRatios,
    [double] $Tolerance = 0.02
  )
  if ($Width -le 0 -or $Height -le 0) { return $false }
  $actual = [double] $Width / [double] $Height
  foreach ($ratio in $AllowedRatios) {
    $parts = $ratio -split ':'
    if ($parts.Count -ne 2) { continue }
    $expected = [double] $parts[0] / [double] $parts[1]
    if ([Math]::Abs($actual - $expected) -le $Tolerance) {
      return $true
    }
  }
  return $false
}

function Get-ImageGeometryIssue {
  param(
    [Parameter(Mandatory = $true)][string] $Type,
    [Parameter(Mandatory = $true)][int] $Width,
    [Parameter(Mandatory = $true)][int] $Height
  )

  if ($Width -le 0 -or $Height -le 0) {
    return 'unreadable_dimensions'
  }

  $normalizedType = $Type.ToLowerInvariant()
  switch ($normalizedType) {
    'detail' {
      if ($Width -lt 900 -or $Height -lt 900 -or $Width -gt 2200 -or $Height -gt 2200) {
        return 'detail_dimensions_out_of_range'
      }
      if (-not (Test-AspectRatio -Width $Width -Height $Height -AllowedRatios @('1:1', '3:4', '4:5', '13:16'))) {
        return 'detail_invalid_aspect_ratio'
      }
    }
    'square' {
      if ($Width -lt 900 -or $Height -lt 900 -or $Width -gt 2200 -or $Height -gt 2200) {
        return 'square_dimensions_out_of_range'
      }
      if (-not (Test-AspectRatio -Width $Width -Height $Height -AllowedRatios @('1:1'))) {
        return 'square_invalid_aspect_ratio'
      }
    }
    'sku' {
      if ($Width -lt 900 -or $Height -lt 900 -or $Width -gt 2200 -or $Height -gt 2200) {
        return 'sku_dimensions_out_of_range'
      }
      if (-not (Test-AspectRatio -Width $Width -Height $Height -AllowedRatios @('1:1'))) {
        return 'sku_invalid_aspect_ratio'
      }
    }
    'description' {
      if ($Width -lt 900 -or $Height -lt 900) {
        return 'description_dimensions_too_small'
      }
      if (-not (Test-AspectRatio -Width $Width -Height $Height -AllowedRatios @('3:4'))) {
        return 'description_invalid_aspect_ratio'
      }
    }
  }

  return $null
}

function Add-UploadFile {
  param(
    [Parameter(Mandatory = $true)] $Record,
    [Parameter(Mandatory = $true)] $Files,
    [Parameter(Mandatory = $true)][int] $MaxBytes
  )

  $type = [string] (Get-ObjectValue -Object $Record -Name 'type')
  $path = [string] (Get-ObjectValue -Object $Record -Name 'local_file_path')
  $exists = -not [string]::IsNullOrWhiteSpace($path) -and (Test-Path -LiteralPath $path)
  $width = $null
  $height = $null
  $bytes = $null
  $ready = $false
  $issue = $null

  if (-not $exists) {
    $issue = 'missing_local_file'
  } else {
    $item = Get-Item -LiteralPath $path
    $bytes = [int64] $item.Length
    $image = $null
    try {
      $image = [Drawing.Image]::FromFile($path)
      $width = [int] $image.Width
      $height = [int] $image.Height
    } finally {
      if ($image) { $image.Dispose() }
    }

    $geometryIssue = Get-ImageGeometryIssue -Type $type -Width $width -Height $height

    if ($bytes -gt $MaxBytes) {
      $issue = 'over_3mb'
    } elseif ([string] (Get-ObjectValue -Object $Record -Name 'status') -ne 'completed') {
      $issue = "status_$((Get-ObjectValue -Object $Record -Name 'status'))"
    } elseif ((Get-ObjectValue -Object $Record -Name 'usable') -eq $false) {
      $issue = 'marked_unusable'
    } elseif ($geometryIssue) {
      $issue = $geometryIssue
    } else {
      $ready = $true
    }
  }

  $entry = [ordered]@{
    type = $type
    color = [string] (Get-ObjectValue -Object $Record -Name 'color')
    slot_key = [string] (Get-ObjectValue -Object $Record -Name 'slot_key')
    local_file_path = $path
    generated_url = [string] (Get-ObjectValue -Object $Record -Name 'generated_url')
    width = $width
    height = $height
    file_size_bytes = $bytes
    upload_ready = $ready
    issue = $issue
  }

  foreach ($name in @('reuse_source_type', 'reuse_source_slot_key', 'reuse_role', 'sku_label')) {
    $value = [string] (Get-ObjectValue -Object $Record -Name $name)
    if (-not [string]::IsNullOrWhiteSpace($value)) {
      $entry[$name] = $value
    }
  }

  [void] $Files.Add($entry)
}

$resolvedGeneratedDir = Ensure-Path -Path $GeneratedDir
if ([string]::IsNullOrWhiteSpace($ManifestPath)) {
  $ManifestPath = Join-Path $resolvedGeneratedDir 'manifest.json'
}
if ([string]::IsNullOrWhiteSpace($OutputPath)) {
  $OutputPath = Join-Path $resolvedGeneratedDir 'upload-files.json'
}

$manifestFile = Resolve-RequiredFile -Path $ManifestPath
$manifest = Get-Content -LiteralPath $manifestFile -Raw -Encoding UTF8 | ConvertFrom-Json
$records = @($manifest.records)

$planPath = [string] (Get-ObjectValue -Object $manifest -Name 'plan_path')
if ([string]::IsNullOrWhiteSpace($planPath)) {
  $planPath = Join-Path $resolvedGeneratedDir 'plan.json'
}
$planFile = Resolve-RequiredFile -Path $planPath
$plan = Get-Content -LiteralPath $planFile -Raw -Encoding UTF8 | ConvertFrom-Json
$reuseMappings = @($plan.reuse_mappings)
if ($reuseMappings.Count -eq 0) {
  throw 'Plan is missing reuse_mappings; rebuild the generation plan with the updated dianxiaomi-shein-image-generate skill.'
}

Add-Type -AssemblyName System.Drawing
$files = New-Object System.Collections.Generic.List[object]
$recordsBySlot = @{}
foreach ($record in $records) {
  $slotKey = [string] (Get-ObjectValue -Object $record -Name 'slot_key')
  if (-not [string]::IsNullOrWhiteSpace($slotKey)) {
    $recordsBySlot[$slotKey] = $record
  }
  Add-UploadFile -Record $record -Files $files -MaxBytes $MaxBytes
}

foreach ($mapping in $reuseMappings) {
  $sourceSlot = [string] (Get-ObjectValue -Object $mapping -Name 'source_slot_key')
  if ([string]::IsNullOrWhiteSpace($sourceSlot) -or -not $recordsBySlot.ContainsKey($sourceSlot)) {
    throw "Reuse mapping source task is missing from manifest: $sourceSlot"
  }
  $source = $recordsBySlot[$sourceSlot]
  $aliasRecord = [ordered]@{
    type = [string] (Get-ObjectValue -Object $mapping -Name 'target_type')
    color = [string] (Get-ObjectValue -Object $mapping -Name 'color')
    slot_key = [string] (Get-ObjectValue -Object $mapping -Name 'target_slot_key')
    local_file_path = [string] (Get-ObjectValue -Object $source -Name 'local_file_path')
    generated_url = [string] (Get-ObjectValue -Object $source -Name 'generated_url')
    status = [string] (Get-ObjectValue -Object $source -Name 'status')
    usable = Get-ObjectValue -Object $source -Name 'usable'
    reuse_source_type = [string] (Get-ObjectValue -Object $mapping -Name 'source_type')
    reuse_source_slot_key = $sourceSlot
    reuse_role = [string] (Get-ObjectValue -Object $mapping -Name 'target_role')
    sku_label = [string] (Get-ObjectValue -Object $mapping -Name 'sku_label')
  }
  Add-UploadFile -Record $aliasRecord -Files $files -MaxBytes $MaxBytes
}

$fileValues = @($files.ToArray())
$result = [ordered]@{
  generated_dir = $resolvedGeneratedDir
  manifest_path = $manifestFile
  created_at = (Get-Date).ToString('s')
  files = @($fileValues)
}

Write-JsonFile -Value $result -Path $OutputPath -Depth 30

[ordered]@{
  output_path = $OutputPath
  total = $files.Count
  upload_ready = @($files | Where-Object { $_.upload_ready }).Count
  blocked = @($files | Where-Object { -not $_.upload_ready }).Count
} | ConvertTo-Json -Depth 5 -Compress
