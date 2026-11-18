[CmdletBinding(PositionalBinding = $false)]
param(
  [Parameter(Mandatory = $true)]
  [string] $Prompt,

  [ValidatePattern('^(auto|[0-9]{2,5}x[0-9]{2,5})$')]
  [string] $Size = '1024x1024',

  [ValidateSet('auto', 'low', 'medium', 'high')]
  [string] $Quality = 'auto',

  [Alias('ReferenceImages', 'Image', 'Images')]
  [string[]] $ReferenceImage = @(),

  [string] $OutputPath = '',

  [ValidateRange(1, 1800)]
  [int] $TimeoutSeconds = 300
)

$ErrorActionPreference = 'Stop'
$Model = 'gpt-image-2'
$SupportedReferenceExtensions = @('.png', '.jpg', '.jpeg', '.webp')
$ProxyEnvKeys = @('HTTPS_PROXY', 'https_proxy', 'HTTP_PROXY', 'http_proxy', 'ALL_PROXY', 'all_proxy')

[Net.ServicePointManager]::SecurityProtocol = [Net.ServicePointManager]::SecurityProtocol -bor [Net.SecurityProtocolType]::Tls12
Add-Type -AssemblyName System.Net.Http

function ConvertFrom-QuotedValue {
  param([Parameter(Mandatory = $true)][string] $Value)

  $trimmed = $Value.Trim()
  if ($trimmed.StartsWith('"') -and $trimmed.EndsWith('"')) {
    return ($trimmed | ConvertFrom-Json)
  }
  if ($trimmed.StartsWith("'") -and $trimmed.EndsWith("'")) {
    return $trimmed.Substring(1, $trimmed.Length - 2)
  }
  return $trimmed
}

function Get-UserProfileDirectory {
  $profileDirectory = [Environment]::GetEnvironmentVariable('USERPROFILE')
  if ([string]::IsNullOrWhiteSpace($profileDirectory)) {
    $profileDirectory = [Environment]::GetFolderPath('UserProfile')
  }
  if ([string]::IsNullOrWhiteSpace($profileDirectory)) {
    throw 'Cannot resolve the current user profile directory'
  }
  return $profileDirectory
}

function Get-CodexImageApiSettings {
  $configPath = Join-Path (Get-UserProfileDirectory) '.codex\config.toml'
  if (-not (Test-Path -LiteralPath $configPath -PathType Leaf)) {
    throw "Missing Codex config: $configPath"
  }

  $currentTable = ''
  $baseUrl = ''
  $apiKey = ''
  foreach ($rawLine in Get-Content -LiteralPath $configPath -Encoding UTF8) {
    $line = $rawLine.Trim()
    $tableMatch = [regex]::Match($line, '^\[([^\]]+)\]\s*(?:#.*)?$')
    if ($tableMatch.Success) {
      $currentTable = $tableMatch.Groups[1].Value
      continue
    }
    if ($currentTable -ne 'model_providers.custom' -or -not $line -or $line.StartsWith('#')) {
      continue
    }

    $valueMatch = [regex]::Match($line, '^(base_url|experimental_bearer_token)\s*=\s*(.+?)\s*$')
    if (-not $valueMatch.Success) {
      continue
    }

    $value = ConvertFrom-QuotedValue -Value $valueMatch.Groups[2].Value
    if ($valueMatch.Groups[1].Value -eq 'base_url') {
      $baseUrl = $value
    } else {
      $apiKey = $value
    }
  }

  if ([string]::IsNullOrWhiteSpace($baseUrl)) {
    throw "Missing base_url in [model_providers.custom] of $configPath"
  }
  if ($baseUrl -notmatch '^https?://') {
    throw "Invalid base_url in [model_providers.custom] of $configPath"
  }
  if ([string]::IsNullOrWhiteSpace($apiKey)) {
    throw "Missing experimental_bearer_token in [model_providers.custom] of $configPath"
  }

  return [pscustomobject]@{
    base_url = $baseUrl.TrimEnd('/')
    api_key = $apiKey
  }
}

function Get-ProxyUrl {
  foreach ($key in $ProxyEnvKeys) {
    $value = [Environment]::GetEnvironmentVariable($key)
    if (-not [string]::IsNullOrWhiteSpace($value)) {
      return $value.Trim()
    }
  }

  $envPath = Join-Path (Get-UserProfileDirectory) '.codex\.env'
  if (-not (Test-Path -LiteralPath $envPath -PathType Leaf)) {
    return $null
  }

  $values = @{}
  foreach ($rawLine in Get-Content -LiteralPath $envPath -Encoding UTF8) {
    $match = [regex]::Match($rawLine, '^\s*(?:export\s+)?([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.*?)\s*$')
    if ($match.Success) {
      $values[$match.Groups[1].Value] = ConvertFrom-QuotedValue -Value $match.Groups[2].Value
    }
  }

  foreach ($key in $ProxyEnvKeys) {
    if ($values.ContainsKey($key) -and -not [string]::IsNullOrWhiteSpace([string] $values[$key])) {
      return [string] $values[$key]
    }
  }
  return $null
}

function New-HttpClient {
  param(
    [string] $ApiKey = '',
    [int] $Timeout = 300
  )

  $handler = New-Object System.Net.Http.HttpClientHandler
  $proxyUrl = Get-ProxyUrl
  if (-not [string]::IsNullOrWhiteSpace($proxyUrl)) {
    if ($proxyUrl -notmatch '^[a-zA-Z][a-zA-Z0-9+.-]*://') {
      $proxyUrl = "http://$proxyUrl"
    }
    $handler.Proxy = New-Object System.Net.WebProxy($proxyUrl)
    $handler.UseProxy = $true
  }

  $client = New-Object System.Net.Http.HttpClient($handler, $true)
  $client.Timeout = [TimeSpan]::FromSeconds($Timeout)
  if (-not [string]::IsNullOrWhiteSpace($ApiKey)) {
    $client.DefaultRequestHeaders.Authorization = New-Object System.Net.Http.Headers.AuthenticationHeaderValue('Bearer', $ApiKey)
  }
  return $client
}

function Resolve-ReferenceFiles {
  param([string[]] $Paths)

  $referenceInputs = New-Object System.Collections.Generic.List[string]
  foreach ($pathGroup in $Paths) {
    foreach ($pathValue in $pathGroup.Split(',')) {
      [void] $referenceInputs.Add($pathValue)
    }
  }

  if ($referenceInputs.Count -gt 16) {
    throw 'ReferenceImage supports at most 16 local files'
  }

  $files = New-Object System.Collections.Generic.List[string]
  foreach ($pathValue in $referenceInputs) {
    if ([string]::IsNullOrWhiteSpace($pathValue)) {
      throw 'ReferenceImage contains an empty path'
    }
    if ($pathValue -match '^https?://') {
      throw "ReferenceImage must be a local file path: $pathValue"
    }

    $fullPath = [IO.Path]::GetFullPath($pathValue)
    if (-not (Test-Path -LiteralPath $fullPath -PathType Leaf)) {
      throw "Reference image not found: $fullPath"
    }
    $extension = [IO.Path]::GetExtension($fullPath).ToLowerInvariant()
    if ($SupportedReferenceExtensions -notcontains $extension) {
      throw "Unsupported reference image type '$extension': $fullPath"
    }
    [void] $files.Add($fullPath)
  }
  return @($files.ToArray())
}

function Resolve-OutputTarget {
  param([string] $RequestedPath)

  if ([string]::IsNullOrWhiteSpace($RequestedPath)) {
    $outputDirectory = Join-Path (Get-Location) '.codex\generated-images'
    $fileName = '{0}-{1}.png' -f (Get-Date -Format 'yyyyMMdd-HHmmss'), ([Guid]::NewGuid().ToString('N').Substring(0, 8))
    $fullPath = Join-Path $outputDirectory $fileName
  } else {
    $fullPath = [IO.Path]::GetFullPath($RequestedPath)
    $outputDirectory = Split-Path -Parent $fullPath
  }

  $extension = [IO.Path]::GetExtension($fullPath).ToLowerInvariant()
  $format = switch ($extension) {
    '.png' { 'png' }
    '.jpg' { 'jpeg' }
    '.jpeg' { 'jpeg' }
    '.webp' { 'webp' }
    default { throw "OutputPath must end in .png, .jpg, .jpeg, or .webp: $fullPath" }
  }

  if (Test-Path -LiteralPath $fullPath) {
    throw "OutputPath already exists: $fullPath"
  }
  if (-not [string]::IsNullOrWhiteSpace($outputDirectory)) {
    New-Item -ItemType Directory -Force -Path $outputDirectory | Out-Null
  }

  return [pscustomobject]@{
    path = $fullPath
    format = $format
  }
}

function Get-ImageContentType {
  param([Parameter(Mandatory = $true)][string] $Path)

  $contentType = switch ([IO.Path]::GetExtension($Path).ToLowerInvariant()) {
    '.png' { 'image/png' }
    '.jpg' { 'image/jpeg' }
    '.jpeg' { 'image/jpeg' }
    '.webp' { 'image/webp' }
  }
  return $contentType
}

function Get-ApiErrorMessage {
  param(
    [Parameter(Mandatory = $true)][string] $Body,
    [Parameter(Mandatory = $true)][int] $StatusCode
  )

  try {
    $parsed = $Body | ConvertFrom-Json
    if ($parsed.error -and -not [string]::IsNullOrWhiteSpace([string] $parsed.error.message)) {
      return "Image API request failed ($StatusCode): $($parsed.error.message)"
    }
  } catch {
  }
  return "Image API request failed ($StatusCode): $($Body.Substring(0, [Math]::Min(500, $Body.Length)))"
}

function Send-ImageRequest {
  param(
    [Parameter(Mandatory = $true)][System.Net.Http.HttpClient] $Client,
    [Parameter(Mandatory = $true)][string] $Url,
    [Parameter(Mandatory = $true)][System.Net.Http.HttpContent] $Content
  )

  $response = $null
  try {
    $response = $Client.PostAsync($Url, $Content).GetAwaiter().GetResult()
    $body = $response.Content.ReadAsStringAsync().GetAwaiter().GetResult()
    if (-not $response.IsSuccessStatusCode) {
      throw (Get-ApiErrorMessage -Body $body -StatusCode ([int] $response.StatusCode))
    }
    return ($body | ConvertFrom-Json)
  } finally {
    if ($null -ne $response) {
      $response.Dispose()
    }
  }
}

function Invoke-Generation {
  param(
    [Parameter(Mandatory = $true)][System.Net.Http.HttpClient] $Client,
    [Parameter(Mandatory = $true)][string] $Url,
    [Parameter(Mandatory = $true)][string] $OutputFormat
  )

  $payload = [ordered]@{
    model = $Model
    prompt = $Prompt
    size = $Size
    quality = $Quality
    output_format = $OutputFormat
    n = 1
  }
  $json = $payload | ConvertTo-Json -Depth 8 -Compress
  $content = New-Object System.Net.Http.StringContent($json, [Text.Encoding]::UTF8, 'application/json')
  try {
    return Send-ImageRequest -Client $Client -Url $Url -Content $content
  } finally {
    $content.Dispose()
  }
}

function Invoke-Edit {
  param(
    [Parameter(Mandatory = $true)][System.Net.Http.HttpClient] $Client,
    [Parameter(Mandatory = $true)][string] $Url,
    [Parameter(Mandatory = $true)][string[]] $ReferenceFiles,
    [Parameter(Mandatory = $true)][string] $OutputFormat
  )

  $content = New-Object System.Net.Http.MultipartFormDataContent
  try {
    $content.Add((New-Object System.Net.Http.StringContent($Model)), 'model')
    $content.Add((New-Object System.Net.Http.StringContent($Prompt)), 'prompt')
    $content.Add((New-Object System.Net.Http.StringContent($Size)), 'size')
    $content.Add((New-Object System.Net.Http.StringContent($Quality)), 'quality')
    $content.Add((New-Object System.Net.Http.StringContent($OutputFormat)), 'output_format')
    $content.Add((New-Object System.Net.Http.StringContent('1')), 'n')

    foreach ($referencePath in $ReferenceFiles) {
      $stream = [IO.File]::OpenRead($referencePath)
      $imageContent = New-Object System.Net.Http.StreamContent($stream)
      $imageContent.Headers.ContentType = New-Object System.Net.Http.Headers.MediaTypeHeaderValue((Get-ImageContentType -Path $referencePath))
      $content.Add($imageContent, 'image[]', [IO.Path]::GetFileName($referencePath))
    }

    return Send-ImageRequest -Client $Client -Url $Url -Content $content
  } finally {
    $content.Dispose()
  }
}

function Save-ImageResult {
  param(
    [Parameter(Mandatory = $true)] $Body,
    [Parameter(Mandatory = $true)][string] $Path,
    [Parameter(Mandatory = $true)][int] $Timeout
  )

  $items = @($Body.data)
  if ($items.Count -eq 0) {
    throw 'Image API response contains no data items'
  }

  $item = $items[0]
  if ($item.PSObject.Properties['b64_json'] -and -not [string]::IsNullOrWhiteSpace([string] $item.b64_json)) {
    $base64 = ([string] $item.b64_json).Trim()
    if ($base64 -match '^data:[^;]+;base64,(.+)$') {
      $base64 = $Matches[1]
    }
    [IO.File]::WriteAllBytes($Path, [Convert]::FromBase64String($base64))
    return
  }

  if ($item.PSObject.Properties['url'] -and -not [string]::IsNullOrWhiteSpace([string] $item.url)) {
    $downloadClient = New-HttpClient -Timeout $Timeout
    try {
      $bytes = $downloadClient.GetByteArrayAsync([string] $item.url).GetAwaiter().GetResult()
      [IO.File]::WriteAllBytes($Path, $bytes)
      return
    } finally {
      $downloadClient.Dispose()
    }
  }

  $keys = @($item.PSObject.Properties.Name) -join ', '
  throw "Image API response contains neither b64_json nor url; first data keys: $keys"
}

try {
  if ([string]::IsNullOrWhiteSpace($Prompt)) {
    throw 'Prompt must not be empty'
  }

  $referenceFiles = @(Resolve-ReferenceFiles -Paths $ReferenceImage)
  $target = Resolve-OutputTarget -RequestedPath $OutputPath
  $settings = Get-CodexImageApiSettings
  $client = New-HttpClient -ApiKey $settings.api_key -Timeout $TimeoutSeconds
  try {
    if ($referenceFiles.Count -eq 0) {
      $operation = 'generation'
      $body = Invoke-Generation -Client $client -Url "$($settings.base_url)/images/generations" -OutputFormat $target.format
    } else {
      $operation = 'edit'
      $body = Invoke-Edit -Client $client -Url "$($settings.base_url)/images/edits" -ReferenceFiles $referenceFiles -OutputFormat $target.format
    }
  } finally {
    $client.Dispose()
  }

  Save-ImageResult -Body $body -Path $target.path -Timeout $TimeoutSeconds
  $displayPath = $target.path.Replace('\', '/')
  $markdown = "![Generated image](<$displayPath>)"
  [ordered]@{
    status = 'completed'
    operation = $operation
    model = $Model
    size = $Size
    saved_files = @($target.path)
    display_markdown = @($markdown)
  } | ConvertTo-Json -Depth 8 -Compress
  exit 0
} catch {
  [Console]::Error.WriteLine("Error: $($_.Exception.Message)")
  exit 1
}
