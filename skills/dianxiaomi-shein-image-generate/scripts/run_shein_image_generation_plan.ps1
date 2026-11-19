[CmdletBinding(PositionalBinding = $false)]
param(
  [Parameter(Mandatory = $true)]
  [string] $PlanPath,

  [string] $WorkspaceRoot = (Get-Location).Path,

  [string] $ManifestPath = '',

  [int] $MaxBytes = 3145728
)

$ErrorActionPreference = 'Stop'

function Read-Plan {
  param([Parameter(Mandatory = $true)][string] $Path)
  $text = Get-Content -LiteralPath $Path -Raw -Encoding UTF8
  $text = $text.TrimStart([char]0xFEFF)
  return $text | ConvertFrom-Json
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

function Get-TasksContainer {
  param($Plan)
  if ($Plan -is [array]) {
    return [ordered]@{ tasks = $Plan; is_array = $true }
  }
  return [ordered]@{ tasks = @($Plan.tasks); is_array = $false }
}

function Get-JsonObjectFromOutput {
  param([string[]] $Lines)
  for ($i = $Lines.Count - 1; $i -ge 0; $i--) {
    $line = $Lines[$i].Trim()
    if ($line.StartsWith('{') -and $line.EndsWith('}')) {
      return $line | ConvertFrom-Json
    }
  }
  throw 'Terln command did not print a JSON result'
}

function Ensure-Property {
  param(
    [Parameter(Mandatory = $true)] $Object,
    [Parameter(Mandatory = $true)][string] $Name,
    $Value = $null
  )
  if (-not ($Object.PSObject.Properties.Name -contains $Name)) {
    $Object | Add-Member -NotePropertyName $Name -NotePropertyValue $Value
  }
}

function Save-State {
  param(
    [Parameter(Mandatory = $true)] $Plan,
    [Parameter(Mandatory = $true)] $Tasks,
    [Parameter(Mandatory = $true)] $Container,
    [Parameter(Mandatory = $true)][string] $PlanFile,
    [Parameter(Mandatory = $true)][string] $ManifestFile
  )

  if ($Container.is_array) {
    Write-JsonFile -Value @($Tasks) -Path $PlanFile -Depth 30
  } else {
    $Plan.tasks = @($Tasks)
    Write-JsonFile -Value $Plan -Path $PlanFile -Depth 30
  }

  $manifest = [ordered]@{
    generated_at = (Get-Date).ToString('s')
    plan_path = $PlanFile
    records = @($Tasks)
  }
  Write-JsonFile -Value $manifest -Path $ManifestFile -Depth 30
}

function Get-TaskLocalPath {
  param(
    [Parameter(Mandatory = $true)] $Task,
    [Parameter(Mandatory = $true)][string] $PlanFile
  )

  $localPath = [string] $Task.local_file_path
  if ([string]::IsNullOrWhiteSpace($localPath)) {
    $planDir = Split-Path -Parent $PlanFile
    $type = if ([string]::IsNullOrWhiteSpace([string] $Task.type)) { 'misc' } else { [string] $Task.type }
    $fileName = if ([string]::IsNullOrWhiteSpace([string] $Task.file_name)) { "$($Task.slot_key).png" } else { [string] $Task.file_name }
    $localPath = Join-Path (Join-Path $planDir $type) $fileName
    Ensure-Property -Object $Task -Name 'local_file_path' -Value $localPath
    $Task.local_file_path = $localPath
  }

  return $localPath
}

function Receive-GeneratedFile {
  param(
    [Parameter(Mandatory = $true)] $Task,
    [Parameter(Mandatory = $true)][string] $LocalPath,
    [Parameter(Mandatory = $true)] $Result,
    [Parameter(Mandatory = $true)][int] $MaxFileBytes
  )

  if (-not (Test-Path -LiteralPath $LocalPath)) {
    throw "Terln command completed but did not create file: $LocalPath"
  }

  $item = Get-Item -LiteralPath $LocalPath
  $img = $null
  $width = $null
  $height = $null
  try {
    $img = [Drawing.Image]::FromFile($LocalPath)
    $width = $img.Width
    $height = $img.Height
  } finally {
    if ($img) { $img.Dispose() }
  }

  Ensure-Property -Object $Task -Name 'generated_url'
  Ensure-Property -Object $Task -Name 'file_size_bytes'
  Ensure-Property -Object $Task -Name 'width'
  Ensure-Property -Object $Task -Name 'height'
  Ensure-Property -Object $Task -Name 'usable'
  Ensure-Property -Object $Task -Name 'completed_at'
  Ensure-Property -Object $Task -Name 'api_model'
  Ensure-Property -Object $Task -Name 'api_size'
  Ensure-Property -Object $Task -Name 'b64_json_count'

  $Task.generated_url = [string] @($Result.image_urls)[0]
  $Task.file_size_bytes = [int64] $item.Length
  $Task.width = [int] $width
  $Task.height = [int] $height
  $Task.completed_at = (Get-Date).ToString('s')
  $Task.api_model = [string] $Result.model
  $Task.api_size = [string] $Result.size
  $Task.b64_json_count = [int] $Result.b64_json_count

  if ($item.Length -gt $MaxFileBytes) {
    $Task.status = 'unusable'
    $Task.usable = $false
    $Task.error = "Generated image exceeds $MaxFileBytes bytes"
  } else {
    $Task.status = 'completed'
    $Task.usable = $true
    $Task.error = $null
  }
}

$resolvedPlan = Resolve-Path -LiteralPath $PlanPath -ErrorAction Stop
$plan = Read-Plan -Path $resolvedPlan.ProviderPath
$container = Get-TasksContainer -Plan $plan
$tasks = @($container.tasks)
$terlnScript = Join-Path $WorkspaceRoot '.codex\skills\terln-gpt-image\scripts\generate_image.ps1'
if (-not (Test-Path -LiteralPath $terlnScript)) {
  throw "Missing Terln image command: $terlnScript"
}

if ([string]::IsNullOrWhiteSpace($ManifestPath)) {
  $ManifestPath = Join-Path (Split-Path -Parent $resolvedPlan.ProviderPath) 'manifest.json'
}

Add-Type -AssemblyName System.Drawing

foreach ($task in $tasks) {
  Ensure-Property -Object $task -Name 'status' -Value 'pending'
  Ensure-Property -Object $task -Name 'error'
  Ensure-Property -Object $task -Name 'generated_at'

  $localPath = Get-TaskLocalPath -Task $task -PlanFile $resolvedPlan.ProviderPath

  if ($task.status -eq 'completed' -and (Test-Path -LiteralPath $localPath)) {
    continue
  }
  if ($task.status -eq 'completed') {
    $task.status = 'pending'
    $task.error = 'Completed status had no local file; regenerating'
  }
  if ($task.status -eq 'unusable') {
    continue
  }
  if ([string]::IsNullOrWhiteSpace([string] $task.prompt)) {
    throw "Task missing prompt: $($task.slot_key)"
  }
  if ([string]::IsNullOrWhiteSpace([string] $task.size)) {
    throw "Task missing API size: $($task.slot_key)"
  }

  New-Item -ItemType Directory -Force -Path (Split-Path -Parent $localPath) | Out-Null
  $refs = @($task.image_urls | Where-Object { -not [string]::IsNullOrWhiteSpace([string] $_) })

  $global:LASTEXITCODE = 0
  if ($refs.Count -gt 0) {
    $output = & $terlnScript `
      -Prompt ([string] $task.prompt) `
      -Size ([string] $task.size) `
      -OutputPath $localPath `
      -ImageUrl $refs 2>&1
  } else {
    $output = & $terlnScript `
      -Prompt ([string] $task.prompt) `
      -Size ([string] $task.size) `
      -OutputPath $localPath 2>&1
  }
  $exitCode = $LASTEXITCODE

  if ($exitCode -ne 0) {
    $task.status = 'generate_failed'
    $task.error = ($output -join "`n")
    Save-State -Plan $plan -Tasks $tasks -Container $container -PlanFile $resolvedPlan.ProviderPath -ManifestFile $ManifestPath
    continue
  }

  try {
    $result = Get-JsonObjectFromOutput -Lines @($output)
    Receive-GeneratedFile -Task $task -LocalPath $localPath -Result $result -MaxFileBytes $MaxBytes
  } catch {
    $task.status = 'generate_failed'
    $task.error = $_.Exception.Message
  }

  $task.generated_at = (Get-Date).ToString('s')
  Save-State -Plan $plan -Tasks $tasks -Container $container -PlanFile $resolvedPlan.ProviderPath -ManifestFile $ManifestPath
}

Save-State -Plan $plan -Tasks $tasks -Container $container -PlanFile $resolvedPlan.ProviderPath -ManifestFile $ManifestPath

[ordered]@{
  plan_path = $resolvedPlan.ProviderPath
  manifest_path = $ManifestPath
  completed = @($tasks | Where-Object { $_.status -eq 'completed' }).Count
  unusable = @($tasks | Where-Object { $_.status -eq 'unusable' }).Count
  failed = @($tasks | Where-Object { $_.status -eq 'generate_failed' }).Count
  total = $tasks.Count
} | ConvertTo-Json -Depth 5 -Compress
