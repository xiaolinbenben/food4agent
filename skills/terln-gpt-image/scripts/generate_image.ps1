[CmdletBinding(PositionalBinding = $false)]
param(
  [Parameter(Mandatory = $true)]
  [string] $Prompt,

  [ValidatePattern('^(auto|[0-9]{2,5}x[0-9]{2,5})$')]
  [string] $Size = '1024x1024',

  [Alias('ImageUrls', 'image_urls', 'image-url')]
  [string[]] $ImageUrl = @(),

  [string] $OutputPath = '',

  [int] $TimeoutSeconds = 300
)

$ErrorActionPreference = 'Stop'

$BaseUrl = 'https://api.terln.com'
$ApiKeyEnv = 'TERLN_API_KEY'
$Model = 'gpt-image-2'
$ProxyEnvKeys = @('HTTPS_PROXY', 'https_proxy', 'HTTP_PROXY', 'http_proxy', 'ALL_PROXY', 'all_proxy')
$CommonProxyPorts = @(7879, 7897, 7890, 7899, 10809, 8080, 1080)
$script:ProxyUrl = $null

[Net.ServicePointManager]::SecurityProtocol = [Net.ServicePointManager]::SecurityProtocol -bor [Net.SecurityProtocolType]::Tls12

function Read-DotEnv {
  param([Parameter(Mandatory = $true)][string] $Path)

  if (-not (Test-Path -LiteralPath $Path)) {
    throw "Missing .env file: $Path"
  }

  $values = @{}
  foreach ($rawLine in Get-Content -LiteralPath $Path -Encoding UTF8) {
    $line = $rawLine.Trim()
    if (-not $line -or $line.StartsWith('#') -or -not $line.Contains('=')) {
      continue
    }

    $parts = $line.Split('=', 2)
    $key = $parts[0].Trim()
    $value = $parts[1].Trim()

    if ($value.Length -ge 2) {
      $first = $value.Substring(0, 1)
      $last = $value.Substring($value.Length - 1, 1)
      if (($first -eq '"' -and $last -eq '"') -or ($first -eq "'" -and $last -eq "'")) {
        $value = $value.Substring(1, $value.Length - 2)
      }
    }

    $values[$key] = $value
  }

  return $values
}

function Get-TerlnApiKey {
  $envPath = Join-Path (Get-Location) '.env'
  $values = Read-DotEnv -Path $envPath
  $apiKey = $values[$ApiKeyEnv]
  if ([string]::IsNullOrWhiteSpace($apiKey)) {
    throw "Missing $ApiKeyEnv in $envPath"
  }
  return $apiKey
}

function Normalize-ProxyUrl {
  param([string] $Value)

  if ([string]::IsNullOrWhiteSpace($Value)) {
    return $null
  }

  $proxyUrl = $Value.Trim()
  if ($proxyUrl -notmatch '^[a-zA-Z][a-zA-Z0-9+.-]*://') {
    $proxyUrl = "http://$proxyUrl"
  }

  return $proxyUrl
}

function Get-ProxyEnvValue {
  foreach ($key in $ProxyEnvKeys) {
    $value = [Environment]::GetEnvironmentVariable($key)
    if (-not [string]::IsNullOrWhiteSpace($value)) {
      return $value
    }
  }

  $envPath = Join-Path (Get-Location) '.env'
  if (-not (Test-Path -LiteralPath $envPath)) {
    return $null
  }

  $values = Read-DotEnv -Path $envPath
  foreach ($key in $ProxyEnvKeys) {
    if ($values.ContainsKey($key) -and -not [string]::IsNullOrWhiteSpace([string] $values[$key])) {
      return [string] $values[$key]
    }
  }

  return $null
}

function Get-ProxyConfigPaths {
  $paths = New-Object System.Collections.Generic.List[string]

  if (-not [string]::IsNullOrWhiteSpace($env:APPDATA)) {
    $appData = $env:APPDATA
    [void] $paths.Add((Join-Path $appData 'Terln AI\proxy\config.yaml'))
    [void] $paths.Add((Join-Path $appData 'terln-ai-client\proxy\config.yaml'))
    [void] $paths.Add((Join-Path $appData 'io.github.clash-verge-rev.clash-verge-rev\config.yaml'))
    [void] $paths.Add((Join-Path $appData 'io.github.clash-verge-rev.clash-verge-rev\clash-verge.yaml'))
    [void] $paths.Add((Join-Path $appData 'io.github.clash-verge-rev.clash-verge-rev\verge.yaml'))
    [void] $paths.Add((Join-Path $appData 'Clash for Windows\config.yaml'))
  }

  $userProfileDir = [Environment]::GetFolderPath('UserProfile')
  if (-not [string]::IsNullOrWhiteSpace($userProfileDir)) {
    [void] $paths.Add((Join-Path $userProfileDir '.config\mihomo\config.yaml'))
    [void] $paths.Add((Join-Path $userProfileDir '.config\clash\config.yaml'))
    [void] $paths.Add((Join-Path $userProfileDir '.config\clash-verge-rev\config.yaml'))
    [void] $paths.Add((Join-Path $userProfileDir 'Library\Application Support\io.github.clash-verge-rev.clash-verge-rev\config.yaml'))
    [void] $paths.Add((Join-Path $userProfileDir 'Library\Application Support\Clash\config.yaml'))
  }

  return @($paths.ToArray() | Select-Object -Unique)
}

function Get-ConfiguredProxyPorts {
  $ports = New-Object System.Collections.Generic.List[int]

  foreach ($path in Get-ProxyConfigPaths) {
    if (-not (Test-Path -LiteralPath $path)) {
      continue
    }

    foreach ($rawLine in Get-Content -LiteralPath $path -Encoding UTF8) {
      if ($rawLine -match '^(mixed-port|port)\s*:\s*([0-9]+)\s*(?:#.*)?$') {
        $port = [int] $Matches[2]
        if ($port -gt 0 -and $port -le 65535 -and -not $ports.Contains($port)) {
          [void] $ports.Add($port)
        }
      }
    }
  }

  return @($ports.ToArray())
}

function Test-LocalTcpPort {
  param([Parameter(Mandatory = $true)][int] $Port)

  $client = New-Object Net.Sockets.TcpClient
  $connect = $null
  try {
    $connect = $client.BeginConnect('127.0.0.1', $Port, $null, $null)
    if (-not $connect.AsyncWaitHandle.WaitOne(250)) {
      return $false
    }
    $client.EndConnect($connect)
    return $true
  } catch {
    return $false
  } finally {
    if ($connect -and $connect.AsyncWaitHandle) {
      $connect.AsyncWaitHandle.Dispose()
    }
    $client.Close()
  }
}

function Get-TerlnProxyUrl {
  $proxyUrl = Normalize-ProxyUrl -Value (Get-ProxyEnvValue)
  if (-not [string]::IsNullOrWhiteSpace($proxyUrl)) {
    return $proxyUrl
  }

  $ports = New-Object System.Collections.Generic.List[int]
  foreach ($port in Get-ConfiguredProxyPorts) {
    if (-not $ports.Contains($port)) {
      [void] $ports.Add($port)
    }
  }
  foreach ($port in $CommonProxyPorts) {
    if (-not $ports.Contains($port)) {
      [void] $ports.Add($port)
    }
  }

  foreach ($port in $ports) {
    if (Test-LocalTcpPort -Port $port) {
      return "http://127.0.0.1:$port"
    }
  }

  return $null
}

function Invoke-TerlnJson {
  param(
    [Parameter(Mandatory = $true)][string] $Url,
    [Parameter(Mandatory = $true)][hashtable] $Headers,
    [Parameter(Mandatory = $true)] $Payload
  )

  try {
    $requestParams = @{
      Method = 'POST'
      Uri = $Url
      Headers = $Headers
      TimeoutSec = $TimeoutSeconds
      ContentType = 'application/json'
      Body = ($Payload | ConvertTo-Json -Depth 20 -Compress)
    }
    if (-not [string]::IsNullOrWhiteSpace($script:ProxyUrl)) {
      $requestParams.Proxy = $script:ProxyUrl
    }

    return Invoke-RestMethod @requestParams
  } catch {
    $response = $_.Exception.Response
    if ($response) {
      $statusCode = [int] $response.StatusCode
      $stream = $response.GetResponseStream()
      if ($stream) {
        $reader = New-Object System.IO.StreamReader($stream)
        $body = $reader.ReadToEnd()
        $reader.Dispose()
        throw "HTTP $statusCode`: $body"
      }
      throw "HTTP $statusCode`: $($_.Exception.Message)"
    }
    throw "Request failed: $($_.Exception.Message)"
  }
}

function Get-ErrorText {
  param($Body)

  if ($Body -and $Body.PSObject.Properties['error']) {
    $errorValue = $Body.error
    if ($errorValue -and $errorValue.PSObject.Properties['message'] -and -not [string]::IsNullOrWhiteSpace([string] $errorValue.message)) {
      return [string] $errorValue.message
    }
    return ($errorValue | ConvertTo-Json -Depth 20 -Compress)
  }

  return $null
}

function Get-ImageResults {
  param([Parameter(Mandatory = $true)] $Body)

  $errorText = Get-ErrorText -Body $Body
  if (-not [string]::IsNullOrWhiteSpace($errorText)) {
    throw "API error: $errorText"
  }

  if ($Body.PSObject.Properties['code'] -and $Body.code -ne 200) {
    $text = $Body | ConvertTo-Json -Depth 20 -Compress
    throw "API request failed: $text"
  }

  if (-not $Body.PSObject.Properties['data']) {
    $text = $Body | ConvertTo-Json -Depth 20 -Compress
    throw "API response missing data: $text"
  }

  $urls = New-Object System.Collections.Generic.List[string]
  $base64Values = New-Object System.Collections.Generic.List[string]

  foreach ($item in @($Body.data)) {
    if ($item.PSObject.Properties['url'] -and -not [string]::IsNullOrWhiteSpace([string] $item.url)) {
      [void] $urls.Add([string] $item.url)
    }
    if ($item.PSObject.Properties['b64_json'] -and -not [string]::IsNullOrWhiteSpace([string] $item.b64_json)) {
      [void] $base64Values.Add([string] $item.b64_json)
    }
  }

  if ($urls.Count -eq 0 -and $base64Values.Count -eq 0) {
    $text = $Body | ConvertTo-Json -Depth 20 -Compress
    throw "API response contains no image URL or base64 image data: $text"
  }

  return [pscustomobject]@{
    urls = @($urls.ToArray())
    b64_json = @($base64Values.ToArray())
  }
}

function Save-ImageFromUrl {
  param(
    [Parameter(Mandatory = $true)][string] $Url,
    [Parameter(Mandatory = $true)][string] $Path
  )

  $requestParams = @{
    Uri = $Url
    OutFile = $Path
    TimeoutSec = 120
  }
  if (-not [string]::IsNullOrWhiteSpace($script:ProxyUrl)) {
    $requestParams.Proxy = $script:ProxyUrl
  }
  Invoke-WebRequest @requestParams
}

function Save-ImageFromBase64 {
  param(
    [Parameter(Mandatory = $true)][string] $Value,
    [Parameter(Mandatory = $true)][string] $Path
  )

  $base64 = $Value.Trim()
  if ($base64 -match '^data:[^;]+;base64,(.+)$') {
    $base64 = $Matches[1]
  }
  [IO.File]::WriteAllBytes($Path, [Convert]::FromBase64String($base64))
}

try {
  if ([string]::IsNullOrWhiteSpace($Prompt)) {
    throw 'Prompt must not be empty'
  }
  if ($ImageUrl.Count -gt 16) {
    throw 'ImageUrl supports at most 16 reference images'
  }

  $apiKey = Get-TerlnApiKey
  $script:ProxyUrl = Get-TerlnProxyUrl
  $headers = @{
    Authorization = "Bearer $apiKey"
  }

  $payload = [ordered]@{
    model = $Model
    prompt = $Prompt
    size = $Size
    n = 1
  }

  if ($ImageUrl.Count -gt 0) {
    $payload.image_urls = @($ImageUrl)
  }

  $body = Invoke-TerlnJson -Url "$BaseUrl/v1/images/generations" -Headers $headers -Payload $payload
  $results = Get-ImageResults -Body $body
  $savedFiles = New-Object System.Collections.Generic.List[string]

  if (-not [string]::IsNullOrWhiteSpace($OutputPath)) {
    $parent = Split-Path -Parent $OutputPath
    if (-not [string]::IsNullOrWhiteSpace($parent)) {
      New-Item -ItemType Directory -Force -Path $parent | Out-Null
    }

    if (@($results.urls).Count -gt 0) {
      Save-ImageFromUrl -Url ([string] @($results.urls)[0]) -Path $OutputPath
    } else {
      Save-ImageFromBase64 -Value ([string] @($results.b64_json)[0]) -Path $OutputPath
    }

    [void] $savedFiles.Add((Resolve-Path -LiteralPath $OutputPath).ProviderPath)
  }

  $response = [ordered]@{
    status = 'completed'
    model = $Model
    size = $Size
    image_urls = @($results.urls)
    b64_json_count = @($results.b64_json).Count
    saved_files = @($savedFiles.ToArray())
  }

  if ([string]::IsNullOrWhiteSpace($OutputPath) -and @($results.urls).Count -eq 0 -and @($results.b64_json).Count -gt 0) {
    $response.b64_json = @($results.b64_json)
  }

  $response | ConvertTo-Json -Depth 8 -Compress
  exit 0
} catch {
  [Console]::Error.WriteLine("Error: $($_.Exception.Message)")
  exit 1
}
