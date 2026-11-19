[CmdletBinding(PositionalBinding = $false)]
param(
  [string] $Prompt,

  [string] $TaskId = '',

  [switch] $SubmitOnly,

  [switch] $PollOnce,

  [ValidateSet('auto', '1:1', '3:2', '2:3', '4:3', '3:4', '5:4', '4:5', '16:9', '9:16', '2:1', '1:2', '21:9', '9:21')]
  [string] $Size = '1:1',

  [ValidateSet('1k', '2k', '4k')]
  [string] $Resolution = '2k',

  [Alias('ImageUrls', 'image_urls', 'image-url')]
  [string[]] $ImageUrl = @(),

  [int] $PollIntervalSeconds = 5,

  [int] $MaxWaitSeconds = 900
)

$ErrorActionPreference = 'Stop'

$BaseUrl = 'https://dragoncode.codes/gpt-image/v1'
$ApiKeyEnv = 'TERLN_API_KEY'
$Model = 'gpt-image-2'
$Supported4kSizes = @('16:9', '9:16', '2:1', '1:2', '21:9', '9:21')
$ProxyEnvKeys = @('HTTPS_PROXY', 'https_proxy', 'HTTP_PROXY', 'http_proxy', 'ALL_PROXY', 'all_proxy')
$CommonProxyPorts = @(7879, 7897, 7890, 7899, 10809, 8080, 1080)
$script:ProxyUrl = $null

if ([Net.ServicePointManager]::SecurityProtocol -band [Net.SecurityProtocolType]::Tls12) {
  [Net.ServicePointManager]::SecurityProtocol = [Net.ServicePointManager]::SecurityProtocol -bor [Net.SecurityProtocolType]::Tls12
} else {
  [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
}

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

function Get-DragonCodeApiKey {
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

function Get-DragonCodeProxyUrl {
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

function Invoke-DragonCodeJson {
  param(
    [Parameter(Mandatory = $true)][ValidateSet('GET', 'POST')][string] $Method,
    [Parameter(Mandatory = $true)][string] $Url,
    [Parameter(Mandatory = $true)][hashtable] $Headers,
    [object] $Payload = $null
  )

  try {
    $requestParams = @{
      Method = $Method
      Uri = $Url
      Headers = $Headers
      TimeoutSec = 60
    }
    if (-not [string]::IsNullOrWhiteSpace($script:ProxyUrl)) {
      $requestParams.Proxy = $script:ProxyUrl
    }

    if ($null -ne $Payload) {
      $json = $Payload | ConvertTo-Json -Depth 20 -Compress
      $requestParams.Body = $json
      $requestParams.ContentType = 'application/json; charset=utf-8'
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

function Assert-ApiOk {
  param(
    [Parameter(Mandatory = $true)] $Body,
    [Parameter(Mandatory = $true)][string] $Operation
  )

  if ($Body.code -ne 200) {
    $text = $Body | ConvertTo-Json -Depth 20 -Compress
    throw "$Operation failed: $text"
  }
}

function Submit-DragonCodeTask {
  param(
    [Parameter(Mandatory = $true)][string] $ApiKey
  )

  $headers = @{
    Authorization = "Bearer $ApiKey"
  }

  $payload = [ordered]@{
    model = $Model
    prompt = $Prompt
    n = 1
    size = $Size
    resolution = $Resolution
  }

  if ($ImageUrl.Count -gt 0) {
    $payload.image_urls = @($ImageUrl)
  }

  $body = Invoke-DragonCodeJson -Method POST -Url "$BaseUrl/images/generations" -Headers $headers -Payload $payload
  Assert-ApiOk -Body $body -Operation 'Submit task'

  $taskId = $null
  if ($body.data -and $body.data.Count -gt 0) {
    $taskId = $body.data[0].task_id
  }
  if ([string]::IsNullOrWhiteSpace([string] $taskId)) {
    $text = $body | ConvertTo-Json -Depth 20 -Compress
    throw "Submit response missing task_id: $text"
  }

  return [string] $taskId
}

function Wait-DragonCodeTask {
  param(
    [Parameter(Mandatory = $true)][string] $TaskId,
    [Parameter(Mandatory = $true)][string] $ApiKey
  )

  $headers = @{
    Authorization = "Bearer $ApiKey"
  }
  $encodedTaskId = [uri]::EscapeDataString($TaskId)
  $deadline = (Get-Date).AddSeconds($MaxWaitSeconds)

  while ((Get-Date) -lt $deadline) {
    $body = Invoke-DragonCodeJson -Method GET -Url "$BaseUrl/tasks/$encodedTaskId" -Headers $headers
    Assert-ApiOk -Body $body -Operation 'Poll task'

    $data = $body.data
    $status = $data.status

    if ($status -eq 'completed') {
      $urls = New-Object System.Collections.Generic.List[string]
      $images = $data.result.images
      foreach ($image in @($images)) {
        $imageUrls = $image.url
        foreach ($url in @($imageUrls)) {
          if (-not [string]::IsNullOrWhiteSpace([string] $url)) {
            [void] $urls.Add([string] $url)
          }
        }
      }

      if ($urls.Count -eq 0) {
        $text = $body | ConvertTo-Json -Depth 20 -Compress
        throw "Completed task has no image URLs: $text"
      }

      return @($urls.ToArray())
    }

    if ($status -eq 'failed') {
      $message = $data.error.message
      if ([string]::IsNullOrWhiteSpace([string] $message)) {
        $message = $body | ConvertTo-Json -Depth 20 -Compress
      }
      throw "Task failed: $message"
    }

    $progress = if ($null -ne $data.progress) { $data.progress } else { 0 }
    $statusText = if ([string]::IsNullOrWhiteSpace([string] $status)) { 'pending' } else { [string] $status }
    [Console]::Error.WriteLine("Task $TaskId $statusText`: $progress%")
    Start-Sleep -Seconds $PollIntervalSeconds
  }

  throw "Timed out waiting for task $TaskId"
}

function Get-DragonCodeTaskStatus {
  param(
    [Parameter(Mandatory = $true)][string] $TaskId,
    [Parameter(Mandatory = $true)][string] $ApiKey
  )

  $headers = @{
    Authorization = "Bearer $ApiKey"
  }
  $encodedTaskId = [uri]::EscapeDataString($TaskId)
  $body = Invoke-DragonCodeJson -Method GET -Url "$BaseUrl/tasks/$encodedTaskId" -Headers $headers
  Assert-ApiOk -Body $body -Operation 'Poll task'

  $data = $body.data
  $status = if ([string]::IsNullOrWhiteSpace([string] $data.status)) { 'pending' } else { [string] $data.status }
  $progress = if ($null -ne $data.progress) { $data.progress } else { 0 }
  $urls = New-Object System.Collections.Generic.List[string]

  if ($status -eq 'completed') {
    $images = $data.result.images
    foreach ($image in @($images)) {
      $imageUrls = $image.url
      foreach ($url in @($imageUrls)) {
        if (-not [string]::IsNullOrWhiteSpace([string] $url)) {
          [void] $urls.Add([string] $url)
        }
      }
    }
  }

  $message = $null
  if ($status -eq 'failed') {
    $message = $data.error.message
    if ([string]::IsNullOrWhiteSpace([string] $message)) {
      $message = $body | ConvertTo-Json -Depth 20 -Compress
    }
  }

  return [ordered]@{
    task_id = $TaskId
    status = $status
    progress = $progress
    image_urls = @($urls.ToArray())
    error = $message
  }
}

try {
  if ([string]::IsNullOrWhiteSpace($TaskId) -and [string]::IsNullOrWhiteSpace($Prompt)) {
    throw 'Prompt must not be empty'
  }
  if ($Resolution -eq '4k' -and $Supported4kSizes -notcontains $Size) {
    throw "4k resolution does not support size $Size"
  }
  if ($ImageUrl.Count -gt 16) {
    throw 'ImageUrl supports at most 16 reference images'
  }

  $apiKey = Get-DragonCodeApiKey
  $script:ProxyUrl = Get-DragonCodeProxyUrl
  if (-not [string]::IsNullOrWhiteSpace($TaskId)) {
    if ($PollOnce) {
      Get-DragonCodeTaskStatus -TaskId $TaskId -ApiKey $apiKey | ConvertTo-Json -Depth 8 -Compress
      exit 0
    }

    $imageUrls = Wait-DragonCodeTask -TaskId $TaskId -ApiKey $apiKey

    [ordered]@{
      task_id = $TaskId
      status = 'completed'
      image_urls = @($imageUrls)
    } | ConvertTo-Json -Depth 5 -Compress
    exit 0
  }

  $taskId = Submit-DragonCodeTask -ApiKey $apiKey
  [Console]::Error.WriteLine("Submitted task $taskId")

  if ($SubmitOnly) {
    [ordered]@{
      task_id = $taskId
      status = 'submitted'
      image_urls = @()
    } | ConvertTo-Json -Depth 5 -Compress
    exit 0
  }

  $imageUrls = Wait-DragonCodeTask -TaskId $taskId -ApiKey $apiKey

  [ordered]@{
    task_id = $taskId
    status = 'completed'
    image_urls = @($imageUrls)
  } | ConvertTo-Json -Depth 5 -Compress
  exit 0
} catch {
  [Console]::Error.WriteLine("Error: $($_.Exception.Message)")
  exit 1
}
