[CmdletBinding(PositionalBinding = $false)]
param(
  [Parameter(Mandatory = $true)]
  [string] $RawProductJson,

  [Parameter(Mandatory = $true)]
  [string[]] $Colors,

  [string[]] $SkuKeys = @(),

  [string] $ProductSummary = '',

  [string] $ImageWorkspace = '',

  [string] $CandidateManifestPath = '',

  [string] $PlanPath = '',

  [string[]] $ColorReferenceIndexes = @(),

  [int] $ReferenceLimit = 16
)

$ErrorActionPreference = 'Stop'

function Resolve-RequiredFile {
  param([Parameter(Mandatory = $true)][string] $Path)
  $resolved = Resolve-Path -LiteralPath $Path -ErrorAction Stop
  return $resolved.ProviderPath
}

function Get-PromptTemplates {
  $templatePath = Join-Path $PSScriptRoot 'shein_image_prompt_templates.json'
  $resolvedTemplatePath = Resolve-RequiredFile -Path $templatePath
  return Get-Content -LiteralPath $resolvedTemplatePath -Raw -Encoding UTF8 | ConvertFrom-Json
}

function Expand-PromptTemplate {
  param(
    [Parameter(Mandatory = $true)][string] $Template,
    [Parameter(Mandatory = $true)][hashtable] $Values
  )
  $result = $Template
  foreach ($key in $Values.Keys) {
    $result = $result.Replace("{$key}", [string] $Values[$key])
  }
  return $result
}

function Save-Json {
  param(
    [Parameter(Mandatory = $true)] $Value,
    [Parameter(Mandatory = $true)][string] $Path
  )
  $jsonLines = ConvertTo-Json -InputObject $Value -Depth 40
  $jsonText = @($jsonLines) -join [Environment]::NewLine
  Set-Content -LiteralPath $Path -Value $jsonText -Encoding UTF8
}

function ConvertTo-Slug {
  param([Parameter(Mandatory = $true)][string] $Text)
  $trimmed = $Text.Trim()
  $sha256 = [System.Security.Cryptography.SHA256]::Create()
  try {
    $hashBytes = $sha256.ComputeHash([System.Text.Encoding]::UTF8.GetBytes($trimmed))
    $hash = ([System.BitConverter]::ToString($hashBytes) -replace '-', '').ToLowerInvariant().Substring(0, 8)
  } finally {
    $sha256.Dispose()
  }
  $slug = $trimmed.ToLowerInvariant() -replace '[^a-z0-9]+', '-'
  $slug = $slug.Trim('-')
  if ([string]::IsNullOrWhiteSpace($slug)) {
    return "value-$hash"
  }
  return "$slug-$hash"
}

function Get-ReferenceIndexSet {
  param([string[]] $Values)
  $set = @{}
  foreach ($value in @($Values)) {
    foreach ($piece in ([string] $value -split ',')) {
      $trimmed = $piece.Trim()
      if ([string]::IsNullOrWhiteSpace($trimmed)) { continue }
      $parsed = 0
      if (-not [int]::TryParse($trimmed, [ref] $parsed)) {
        throw "Reference index is not an integer: $trimmed"
      }
      $set[$parsed] = $true
    }
  }
  return $set
}

function Get-RatioBucket {
  param($Record)
  $width = [double] $Record.width
  $height = [double] $Record.height
  if ($width -le 0 -or $height -le 0) { return 'unknown' }
  $ratio = $width / $height
  if ($ratio -ge 0.9 -and $ratio -le 1.1) { return 'square' }
  if ($ratio -lt 0.65) { return 'tall' }
  if ($ratio -lt 0.9) { return 'portrait' }
  if ($ratio -gt 1.55) { return 'wide' }
  return 'landscape'
}

function Select-ReferenceRecords {
  param(
    [Parameter(Mandatory = $true)] $Records,
    [Parameter(Mandatory = $true)][int] $Limit,
    [string[]] $Indexes
  )
  $usable = @($Records | Where-Object {
    $_.status -like 'downloaded*' -and
    -not [string]::IsNullOrWhiteSpace([string] $_.image_url)
  })
  if ($usable.Count -eq 0) {
    throw 'No downloaded JSON image references are available.'
  }

  $indexSet = Get-ReferenceIndexSet -Values $Indexes
  if ($indexSet.Count -gt 0) {
    $selected = @($usable | Where-Object { $indexSet.ContainsKey([int] $_.index) })
    if ($selected.Count -eq 0) {
      throw 'ColorReferenceIndexes did not match any downloaded candidates.'
    }
    return @($selected | Select-Object -First $Limit)
  }

  if ($usable.Count -le $Limit) {
    return @($usable)
  }

  $groups = @{}
  foreach ($record in @($usable | Sort-Object @{ Expression = { [int64] $_.width * [int64] $_.height }; Descending = $true })) {
    $bucket = Get-RatioBucket -Record $record
    if (-not $groups.ContainsKey($bucket)) {
      $groups[$bucket] = New-Object System.Collections.Generic.List[object]
    }
    [void] $groups[$bucket].Add($record)
  }

  $order = @('square', 'portrait', 'landscape', 'tall', 'wide', 'unknown')
  $selectedList = New-Object System.Collections.Generic.List[object]
  $cursor = 0
  while ($selectedList.Count -lt $Limit) {
    $added = $false
    foreach ($bucket in $order) {
      if (-not $groups.ContainsKey($bucket)) { continue }
      if ($cursor -lt $groups[$bucket].Count) {
        [void] $selectedList.Add($groups[$bucket][$cursor])
        $added = $true
        if ($selectedList.Count -ge $Limit) { break }
      }
    }
    if (-not $added) { break }
    $cursor++
  }
  return @($selectedList.ToArray())
}

function Get-ColorReferenceIndexMap {
  param([string[]] $Values)
  $map = @{}
  foreach ($value in @($Values)) {
    $text = ([string] $value).Trim()
    if ([string]::IsNullOrWhiteSpace($text)) { continue }
    $parts = $text -split '=', 2
    if ($parts.Count -ne 2 -or [string]::IsNullOrWhiteSpace($parts[0]) -or [string]::IsNullOrWhiteSpace($parts[1])) {
      throw "ColorReferenceIndexes entries must use Color=1,2 format: $text"
    }
    $color = $parts[0].Trim()
    $indexes = @($parts[1] -split ',' | ForEach-Object { $_.Trim() } | Where-Object { -not [string]::IsNullOrWhiteSpace($_) })
    if ($indexes.Count -eq 0) {
      throw "ColorReferenceIndexes has no indexes for color: $color"
    }
    $map[$color] = $indexes
  }
  return $map
}

function Get-ReferenceIndexesFromRecords {
  param($Records)
  $values = New-Object System.Collections.Generic.List[int]
  foreach ($refRecord in @($Records)) {
    $indexProperty = $refRecord.PSObject.Properties['index']
    if ($indexProperty) {
      [void] $values.Add([int] $indexProperty.Value)
    }
  }
  return @($values.ToArray())
}

$rawPath = Resolve-RequiredFile -Path $RawProductJson
$jsonDir = Split-Path -Parent $rawPath
if ([string]::IsNullOrWhiteSpace($ImageWorkspace)) {
  $ImageWorkspace = Join-Path $jsonDir 'image'
}
if ([string]::IsNullOrWhiteSpace($CandidateManifestPath)) {
  $CandidateManifestPath = Join-Path (Join-Path $ImageWorkspace 'candidates') 'manifest.json'
}
if ([string]::IsNullOrWhiteSpace($PlanPath)) {
  $PlanPath = Join-Path (Join-Path $ImageWorkspace 'generated') 'plan.json'
}

$colorsClean = @($Colors | ForEach-Object { ([string] $_).Trim() } | Where-Object { -not [string]::IsNullOrWhiteSpace($_) })
if ($colorsClean.Count -eq 0) {
  throw 'At least one color from the Dianxiaomi image edit page is required.'
}

$manifestPath = Resolve-RequiredFile -Path $CandidateManifestPath
$manifest = Get-Content -LiteralPath $manifestPath -Raw -Encoding UTF8 | ConvertFrom-Json
$colorReferenceIndexMap = Get-ColorReferenceIndexMap -Values $ColorReferenceIndexes
$promptTemplates = Get-PromptTemplates

$generatedDir = Split-Path -Parent $PlanPath
New-Item -ItemType Directory -Force -Path $generatedDir | Out-Null
foreach ($type in @('detail', 'description', 'square', 'unusable')) {
  New-Item -ItemType Directory -Force -Path (Join-Path $generatedDir $type) | Out-Null
}

$product = $ProductSummary.Trim()
if ([string]::IsNullOrWhiteSpace($product)) {
  $product = 'the exact product shown in the reference images'
}

$tasks = New-Object System.Collections.Generic.List[object]
$reuseMappings = New-Object System.Collections.Generic.List[object]
$referenceGroups = New-Object System.Collections.Generic.List[object]

function Add-GenerationTask {
  param(
    [Parameter(Mandatory = $true)][string] $Color,
    [Parameter(Mandatory = $true)][string] $Type,
    [Parameter(Mandatory = $true)][string] $Slot,
    [Parameter(Mandatory = $true)][string] $FileName,
    [Parameter(Mandatory = $true)][string] $Size,
    [Parameter(Mandatory = $true)][string] $Ratio,
    [Parameter(Mandatory = $true)][string] $Prompt,
    [Parameter(Mandatory = $true)][string[]] $ImageUrls
  )
  $localPath = Join-Path (Join-Path $generatedDir $Type) $FileName
  $ratioInstruction = Expand-PromptTemplate -Template $promptTemplates.common.ratio_instruction -Values @{ ratio = $Ratio }
  $textInstruction = $promptTemplates.common.text_instruction
  $finalPrompt = "$Prompt $ratioInstruction $textInstruction"
  [void] $tasks.Add([ordered]@{
    slot_key = $Slot
    type = $Type
    color = $Color
    file_name = $FileName
    local_file_path = $localPath
    prompt = $finalPrompt
    size = $Size
    ratio = $Ratio
    image_urls = @($ImageUrls)
    status = 'pending'
  })
}

foreach ($color in $colorsClean) {
  if (-not $colorReferenceIndexMap.ContainsKey($color)) {
    throw "Missing ColorReferenceIndexes entry for color: $color"
  }
  $selectedRefs = Select-ReferenceRecords -Records @($manifest.records) -Limit ([Math]::Max(1, [Math]::Min(16, $ReferenceLimit))) -Indexes @($colorReferenceIndexMap[$color])
  $referenceUrls = @($selectedRefs | ForEach-Object { [string] $_.image_url })
  if ($referenceUrls.Count -eq 0) {
    throw "No reference images selected for color: $color"
  }
  [void] $referenceGroups.Add([ordered]@{
    color = $color
    reference_count = $referenceUrls.Count
    reference_indexes = @(Get-ReferenceIndexesFromRecords -Records $selectedRefs)
    reference_image_urls = @($referenceUrls)
  })

  $colorSlug = ConvertTo-Slug -Text $color
  $templateValues = @{
    color = $color
    product = $product
  }
  $basePrompt = Expand-PromptTemplate -Template $promptTemplates.common.base_prompt -Values $templateValues
  $taskTemplateValues = @{
    color = $color
    product = $product
    basePrompt = $basePrompt
  }

  Add-GenerationTask -Color $color -Type 'detail' -Slot "$colorSlug-detail-angle" -FileName "$colorSlug-detail-angle.png" -Size '960x1280' -Ratio '3:4' -Prompt (Expand-PromptTemplate -Template $promptTemplates.tasks.detail_angle -Values $taskTemplateValues) -ImageUrls $referenceUrls
  Add-GenerationTask -Color $color -Type 'detail' -Slot "$colorSlug-detail-closeup" -FileName "$colorSlug-detail-closeup.png" -Size '1024x1280' -Ratio '4:5' -Prompt (Expand-PromptTemplate -Template $promptTemplates.tasks.detail_closeup -Values $taskTemplateValues) -ImageUrls $referenceUrls

  Add-GenerationTask -Color $color -Type 'description' -Slot "$colorSlug-description-1" -FileName "$colorSlug-description-1.png" -Size '960x1280' -Ratio '3:4' -Prompt (Expand-PromptTemplate -Template $promptTemplates.tasks.description_1 -Values $taskTemplateValues) -ImageUrls $referenceUrls
  Add-GenerationTask -Color $color -Type 'description' -Slot "$colorSlug-description-2" -FileName "$colorSlug-description-2.png" -Size '960x1280' -Ratio '3:4' -Prompt (Expand-PromptTemplate -Template $promptTemplates.tasks.description_2 -Values $taskTemplateValues) -ImageUrls $referenceUrls
  Add-GenerationTask -Color $color -Type 'description' -Slot "$colorSlug-description-3" -FileName "$colorSlug-description-3.png" -Size '960x1280' -Ratio '3:4' -Prompt (Expand-PromptTemplate -Template $promptTemplates.tasks.description_3 -Values $taskTemplateValues) -ImageUrls $referenceUrls

  $squareSlot = "$colorSlug-square"
  $squareFileName = "$colorSlug-square.png"
  $squarePath = Join-Path (Join-Path $generatedDir 'square') $squareFileName
  Add-GenerationTask -Color $color -Type 'square' -Slot $squareSlot -FileName $squareFileName -Size '1024x1024' -Ratio '1:1' -Prompt (Expand-PromptTemplate -Template $promptTemplates.tasks.square -Values $taskTemplateValues) -ImageUrls $referenceUrls

  $skuLabels = @($SkuKeys | ForEach-Object { ([string] $_).Trim() } | Where-Object { -not [string]::IsNullOrWhiteSpace($_) -and $_ -like "*$color*" })
  if ($skuLabels.Count -eq 0) {
    $skuLabels = @($color)
  }
  [void] $reuseMappings.Add([ordered]@{
    source_type = 'square'
    source_slot_key = $squareSlot
    source_file_path = $squarePath
    target_type = 'detail'
    target_slot_key = "$colorSlug-detail-main"
    target_role = 'detail-main'
    color = $color
  })
  foreach ($skuLabel in $skuLabels) {
    $skuSlug = ConvertTo-Slug -Text $skuLabel
    [void] $reuseMappings.Add([ordered]@{
      source_type = 'square'
      source_slot_key = $squareSlot
      source_file_path = $squarePath
      target_type = 'sku'
      target_slot_key = "$skuSlug-sku"
      target_role = 'sku'
      color = $color
      sku_label = $skuLabel
    })
  }
}

$taskValues = @($tasks.ToArray())
$reuseMappingValues = @($reuseMappings.ToArray())
$referenceGroupValues = @($referenceGroups.ToArray())

$plan = [ordered]@{
  raw_product_json = $rawPath
  image_workspace = $ImageWorkspace
  candidate_manifest = $manifestPath
  reference_groups = @($referenceGroupValues)
  created_at = (Get-Date).ToString('s')
  reuse_rules = [ordered]@{
    square_replaces = @('detail-main', 'sku')
  }
  reuse_mappings = @($reuseMappingValues)
  tasks = @($taskValues)
}

Save-Json -Value $plan -Path $PlanPath

[ordered]@{
  plan_path = $PlanPath
  task_count = $tasks.Count
  reference_groups = @($plan.reference_groups | ForEach-Object {
    [ordered]@{
      color = $_.color
      reference_count = $_.reference_count
      reference_indexes = @($_.reference_indexes)
    }
  })
} | ConvertTo-Json -Depth 10 -Compress
