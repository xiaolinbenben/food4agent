[CmdletBinding(PositionalBinding = $false)]
param(
  [Parameter(Mandatory = $true)]
  [string] $HexColor,

  [Parameter(Mandatory = $true)]
  [string] $OutputPath,

  [int] $Size = 80
)

$ErrorActionPreference = 'Stop'

$hex = $HexColor.Trim().TrimStart('#')
if ($hex -notmatch '^[0-9a-fA-F]{6}$') {
  throw "HexColor must be exactly 6 hex digits, for example 777777 or #777777."
}
if ($Size -le 0) {
  throw 'Size must be greater than 0.'
}

$resolvedOutput = $ExecutionContext.SessionState.Path.GetUnresolvedProviderPathFromPSPath($OutputPath)
$parent = Split-Path -Parent $resolvedOutput
if (-not [string]::IsNullOrWhiteSpace($parent)) {
  New-Item -ItemType Directory -Force -Path $parent | Out-Null
}

$r = [Convert]::ToInt32($hex.Substring(0, 2), 16)
$g = [Convert]::ToInt32($hex.Substring(2, 2), 16)
$b = [Convert]::ToInt32($hex.Substring(4, 2), 16)

Add-Type -AssemblyName System.Drawing
$bitmap = New-Object Drawing.Bitmap $Size, $Size
$graphics = $null
try {
  $graphics = [Drawing.Graphics]::FromImage($bitmap)
  $graphics.Clear([Drawing.Color]::FromArgb($r, $g, $b))
  $bitmap.Save($resolvedOutput, [Drawing.Imaging.ImageFormat]::Png)
} finally {
  if ($graphics) { $graphics.Dispose() }
  if ($bitmap) { $bitmap.Dispose() }
}

[ordered]@{
  output_path = $resolvedOutput
  hex_color = $hex.ToUpperInvariant()
  width = $Size
  height = $Size
} | ConvertTo-Json -Compress
