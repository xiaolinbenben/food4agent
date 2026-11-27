# Read experimental_bearer_token from Codex config.toml.
# macOS: $HOME/.codex/config.toml
# Windows: %USERPROFILE%\.codex\config.toml
# Both: $CODEX_HOME/config.toml when CODEX_HOME is set.

function Test-CodexWindowsPlatform {
  if (Test-Path -Path 'variable:IsWindows') {
    return [bool]$IsWindows
  }
  return $env:OS -eq 'Windows_NT'
}

function Get-CodexConfigPathForPlatform {
  param(
    [Parameter(Mandatory = $true)]
    [string] $Platform,

    [AllowEmptyString()]
    [string] $CodexHome = '',

    [AllowEmptyString()]
    [string] $UserProfile = '',

    [AllowEmptyString()]
    [string] $HomeDir = ''
  )

  if (-not [string]::IsNullOrWhiteSpace($CodexHome)) {
    $root = $CodexHome.Trim().TrimEnd('\', '/')
    return [IO.Path]::Combine($root, 'config.toml')
  }

  $useWindowsProfile = $Platform -match '^(Windows|Win|MINGW|MSYS|CYGWIN)'
  if ($useWindowsProfile) {
    if ([string]::IsNullOrWhiteSpace($UserProfile)) {
      throw 'USERPROFILE is not set. On Windows the Codex config is %USERPROFILE%\.codex\config.toml. Set CODEX_HOME if Codex uses another directory. Do not ask the user for an API key.'
    }
    $profileDir = $UserProfile.Trim().TrimEnd('\', '/')
    return [IO.Path]::Combine($profileDir, '.codex', 'config.toml')
  }

  if ([string]::IsNullOrWhiteSpace($HomeDir)) {
    throw 'HOME is not set. On macOS the Codex config is ~/.codex/config.toml. Set CODEX_HOME if Codex uses another directory. Do not ask the user for an API key.'
  }
  $homeDirectory = $HomeDir.Trim().TrimEnd('\', '/')
  return [IO.Path]::Combine($homeDirectory, '.codex', 'config.toml')
}

function Get-CodexConfigPath {
  $platform = 'Darwin'
  if (Test-CodexWindowsPlatform) {
    $platform = 'Windows'
  }
  return Get-CodexConfigPathForPlatform -Platform $platform -CodexHome $env:CODEX_HOME -UserProfile $env:USERPROFILE -HomeDir $env:HOME
}

function New-TomlParse {
  param(
    [string] $Status,
    [string] $Value = ''
  )
  return @{ Status = $Status; Value = $Value }
}

function Test-TomlSame {
  param([string] $Left, [string] $Right)
  return [string]::Equals($Left, $Right, [StringComparison]::Ordinal)
}

function ConvertTo-NormalizedTomlKey {
  param([string] $Key)
  $normalized = $Key.Trim()
  if ($normalized.Length -ge 2) {
    $first = $normalized.Substring(0, 1)
    $last = $normalized.Substring($normalized.Length - 1, 1)
    $doubleQuote = [string]::Equals($first, '"', [StringComparison]::Ordinal) -and [string]::Equals($last, '"', [StringComparison]::Ordinal)
    $singleQuote = [string]::Equals($first, "'", [StringComparison]::Ordinal) -and [string]::Equals($last, "'", [StringComparison]::Ordinal)
    if ($doubleQuote -or $singleQuote) {
      $normalized = $normalized.Substring(1, $normalized.Length - 2)
    }
  }
  return ($normalized -replace '\s', '')
}

function Test-TomlTrailing {
  param([string] $Rest)
  if ($null -eq $Rest) {
    return $true
  }
  $trimmed = $Rest.TrimStart()
  return [string]::IsNullOrEmpty($trimmed) -or $trimmed.StartsWith('#')
}

function Get-TomlChar {
  param([string] $Text, [int] $Index)
  return $Text.Substring($Index, 1)
}

function Test-TomlSlice {
  param([string] $Text, [int] $Index, [string] $Token)
  if ($Index + $Token.Length -gt $Text.Length) {
    return $false
  }
  return [string]::Equals($Text.Substring($Index, $Token.Length), $Token, [StringComparison]::Ordinal)
}

function Add-TomlEscape {
  param([string] $Next)
  if ([string]::Equals($Next, '"', [StringComparison]::Ordinal)) { return '"' }
  if ([string]::Equals($Next, '\', [StringComparison]::Ordinal)) { return '\' }
  if ([string]::Equals($Next, 'n', [StringComparison]::Ordinal)) { return "`n" }
  if ([string]::Equals($Next, 't', [StringComparison]::Ordinal)) { return "`t" }
  if ([string]::Equals($Next, 'r', [StringComparison]::Ordinal)) { return "`r" }
  if ([string]::Equals($Next, 'b', [StringComparison]::Ordinal)) { return "`b" }
  if ([string]::Equals($Next, 'f', [StringComparison]::Ordinal)) { return "`f" }
  return $null
}

function Get-TomlCodePoint {
  param([string] $Hex)
  $code = 0
  if (-not [int]::TryParse($Hex, [Globalization.NumberStyles]::AllowHexSpecifier, [Globalization.CultureInfo]::InvariantCulture, [ref] $code)) {
    return $null
  }
  if ($code -lt 0 -or $code -gt 0x10FFFF -or ($code -ge 0xD800 -and $code -le 0xDFFF)) {
    return $null
  }
  return [char]::ConvertFromUtf32($code)
}

function Get-TomlValueStart {
  param([string] $Text)
  $value = $Text
  while ($true) {
    $value = $value.TrimStart()
    if ($value.StartsWith('#')) {
      $newline = $value.IndexOf("`n")
      if ($newline -lt 0) {
        return ''
      }
      $value = $value.Substring($newline + 1)
      continue
    }
    return $value
  }
}

function ConvertFrom-TomlBasicString {
  param([string] $Text)
  $builder = New-Object System.Text.StringBuilder
  $index = 1
  while ($index -lt $Text.Length) {
    $char = Get-TomlChar -Text $Text -Index $index
    if ([string]::Equals($char, '\', [StringComparison]::Ordinal)) {
      if ($index + 1 -ge $Text.Length) {
        return New-TomlParse -Status 'incomplete'
      }
      $next = Get-TomlChar -Text $Text -Index ($index + 1)
      if ([string]::Equals($next, 'u', [StringComparison]::Ordinal) -or [string]::Equals($next, 'U', [StringComparison]::Ordinal)) {
        $digits = 4
        if ([string]::Equals($next, 'U', [StringComparison]::Ordinal)) { $digits = 8 }
        if ($index + 2 + $digits -gt $Text.Length) {
          return New-TomlParse -Status 'incomplete'
        }
        $hex = $Text.Substring($index + 2, $digits)
        if ($hex -notmatch '^[0-9A-Fa-f]+$' -or $hex.Length -ne $digits) {
          return New-TomlParse -Status 'invalid'
        }
        $decoded = Get-TomlCodePoint -Hex $hex
        if ($null -eq $decoded) {
          return New-TomlParse -Status 'invalid'
        }
        [void] $builder.Append($decoded)
        $index += 2 + $digits
        continue
      }
      $escaped = Add-TomlEscape -Next $next
      if ($null -eq $escaped) {
        return New-TomlParse -Status 'invalid'
      }
      [void] $builder.Append($escaped)
      $index += 2
      continue
    }
    if ([string]::Equals($char, "`n", [StringComparison]::Ordinal) -or [string]::Equals($char, "`r", [StringComparison]::Ordinal)) {
      return New-TomlParse -Status 'invalid'
    }
    if ([string]::Equals($char, '"', [StringComparison]::Ordinal)) {
      if (-not (Test-TomlTrailing -Rest $Text.Substring($index + 1))) {
        return New-TomlParse -Status 'invalid'
      }
      return New-TomlParse -Status 'ok' -Value $builder.ToString()
    }
    [void] $builder.Append($char)
    $index += 1
  }
  return New-TomlParse -Status 'incomplete'
}

function ConvertFrom-TomlLiteralString {
  param([string] $Text)
  $builder = New-Object System.Text.StringBuilder
  $index = 1
  while ($index -lt $Text.Length) {
    $char = Get-TomlChar -Text $Text -Index $index
    if ([string]::Equals($char, "`n", [StringComparison]::Ordinal) -or [string]::Equals($char, "`r", [StringComparison]::Ordinal)) {
      return New-TomlParse -Status 'invalid'
    }
    if ([string]::Equals($char, "'", [StringComparison]::Ordinal)) {
      if (-not (Test-TomlTrailing -Rest $Text.Substring($index + 1))) {
        return New-TomlParse -Status 'invalid'
      }
      return New-TomlParse -Status 'ok' -Value $builder.ToString()
    }
    [void] $builder.Append($char)
    $index += 1
  }
  return New-TomlParse -Status 'incomplete'
}

function ConvertFrom-TomlMultilineBasic {
  param([string] $Text)
  $builder = New-Object System.Text.StringBuilder
  $index = 3
  if ($Text.Length -ge 4 -and [string]::Equals((Get-TomlChar -Text $Text -Index 3), "`n", [StringComparison]::Ordinal)) {
    $index = 4
  }
  while ($index -lt $Text.Length) {
    if (Test-TomlSlice -Text $Text -Index $index -Token '"""') {
      if (-not (Test-TomlTrailing -Rest $Text.Substring($index + 3))) {
        return New-TomlParse -Status 'invalid'
      }
      return New-TomlParse -Status 'ok' -Value $builder.ToString()
    }
    $char = Get-TomlChar -Text $Text -Index $index
    if ([string]::Equals($char, '\', [StringComparison]::Ordinal)) {
      if ($index + 1 -ge $Text.Length) {
        return New-TomlParse -Status 'incomplete'
      }
      $next = Get-TomlChar -Text $Text -Index ($index + 1)
      if ([string]::Equals($next, "`n", [StringComparison]::Ordinal)) {
        $index += 2
        while ($index -lt $Text.Length) {
          $space = Get-TomlChar -Text $Text -Index $index
          if (-not [string]::Equals($space, ' ', [StringComparison]::Ordinal) -and -not [string]::Equals($space, "`t", [StringComparison]::Ordinal) -and -not [string]::Equals($space, "`r", [StringComparison]::Ordinal)) {
            break
          }
          $index += 1
        }
        continue
      }
      if ([string]::Equals($next, 'u', [StringComparison]::Ordinal) -or [string]::Equals($next, 'U', [StringComparison]::Ordinal)) {
        $digits = 4
        if ([string]::Equals($next, 'U', [StringComparison]::Ordinal)) { $digits = 8 }
        if ($index + 2 + $digits -gt $Text.Length) {
          return New-TomlParse -Status 'incomplete'
        }
        $hex = $Text.Substring($index + 2, $digits)
        if ($hex -notmatch '^[0-9A-Fa-f]+$' -or $hex.Length -ne $digits) {
          return New-TomlParse -Status 'invalid'
        }
        $decoded = Get-TomlCodePoint -Hex $hex
        if ($null -eq $decoded) {
          return New-TomlParse -Status 'invalid'
        }
        [void] $builder.Append($decoded)
        $index += 2 + $digits
        continue
      }
      $escaped = Add-TomlEscape -Next $next
      if ($null -eq $escaped) {
        return New-TomlParse -Status 'invalid'
      }
      [void] $builder.Append($escaped)
      $index += 2
      continue
    }
    [void] $builder.Append($char)
    $index += 1
  }
  return New-TomlParse -Status 'incomplete'
}

function ConvertFrom-TomlMultilineLiteral {
  param([string] $Text)
  $builder = New-Object System.Text.StringBuilder
  $index = 3
  if ($Text.Length -ge 4 -and [string]::Equals((Get-TomlChar -Text $Text -Index 3), "`n", [StringComparison]::Ordinal)) {
    $index = 4
  }
  while ($index -lt $Text.Length) {
    if (Test-TomlSlice -Text $Text -Index $index -Token "'''") {
      if (-not (Test-TomlTrailing -Rest $Text.Substring($index + 3))) {
        return New-TomlParse -Status 'invalid'
      }
      return New-TomlParse -Status 'ok' -Value $builder.ToString()
    }
    [void] $builder.Append((Get-TomlChar -Text $Text -Index $index))
    $index += 1
  }
  return New-TomlParse -Status 'incomplete'
}

function ConvertFrom-TomlBare {
  param([string] $Text)
  $bare = $Text
  $newline = $bare.IndexOf("`n")
  if ($newline -ge 0) {
    $bare = $bare.Substring(0, $newline)
  }
  $comment = [regex]::Match($bare, '^(.*)[ \t]#')
  if ($comment.Success) {
    $bare = $comment.Groups[1].Value
  } elseif ($bare.TrimStart().StartsWith('#')) {
    return New-TomlParse -Status 'invalid'
  }
  $bare = $bare.Trim()
  if ([string]::IsNullOrEmpty($bare)) {
    return New-TomlParse -Status 'invalid'
  }
  return New-TomlParse -Status 'ok' -Value $bare
}

function ConvertFrom-TomlScalar {
  param([string] $Text)
  if ($Text.StartsWith('"""')) {
    return ConvertFrom-TomlMultilineBasic -Text $Text
  }
  if ($Text.StartsWith("'''")) {
    return ConvertFrom-TomlMultilineLiteral -Text $Text
  }
  if ($Text.StartsWith('"')) {
    return ConvertFrom-TomlBasicString -Text $Text
  }
  if ($Text.StartsWith("'")) {
    return ConvertFrom-TomlLiteralString -Text $Text
  }
  return ConvertFrom-TomlBare -Text $Text
}

function Read-CodexBearerToken {
  param([Parameter(Mandatory = $true)][string] $Path)

  if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) {
    throw "Codex config not found: $Path. Do not ask the user for an API key."
  }

  $raw = [IO.File]::ReadAllText($Path)
  if ($raw.Length -gt 0 -and [int][char]$raw[0] -eq 0xFEFF) {
    $raw = $raw.Substring(1)
  }
  $lines = @($raw -split '\r\n|\n|\r')
  $table = ''
  $tokTables = New-Object System.Collections.Generic.List[string]
  $tokValues = New-Object System.Collections.Generic.List[string]
  $urlTables = New-Object System.Collections.Generic.List[string]
  $urlValues = New-Object System.Collections.Generic.List[string]
  $index = 0

  while ($index -lt $lines.Count) {
    $line = [string]$lines[$index]
    if ($index -eq 0) {
      $line = $line.TrimStart([char]0xFEFF)
    }
    $line = $line.TrimStart()
    if ([string]::IsNullOrEmpty($line) -or $line.StartsWith('#')) {
      $index += 1
      continue
    }
    if ($line -match '^\[\[([^]]+)\]\]\s*(#.*)?$') {
      $table = ConvertTo-NormalizedTomlKey -Key $Matches[1]
      $index += 1
      continue
    }
    if ($line -match '^\[([^]]+)\]\s*(#.*)?$') {
      $table = ConvertTo-NormalizedTomlKey -Key $Matches[1]
      $index += 1
      continue
    }
    $equals = $line.IndexOf('=')
    if ($equals -lt 0) {
      $index += 1
      continue
    }

    $lhs = $line.Substring(0, $equals).Trim()
    $rhs = $line.Substring($equals + 1).TrimStart()
    $key = ConvertTo-NormalizedTomlKey -Key $lhs
    if ([string]::IsNullOrEmpty($key)) {
      $index += 1
      continue
    }
    if ([string]::IsNullOrEmpty($table)) {
      $fullKey = $key
    } else {
      $fullKey = "$table.$key"
    }
    if ($fullKey.Contains('.')) {
      $parent = $fullKey.Substring(0, $fullKey.LastIndexOf('.'))
    } else {
      $parent = ''
    }
    $leaf = $fullKey.Substring($fullKey.LastIndexOf('.') + 1)
    $interesting = (Test-TomlSame -Left $leaf -Right 'experimental_bearer_token') -or (Test-TomlSame -Left $leaf -Right 'base_url')

    $text = $rhs
    $end = $index
    $parsed = $null
    while ($true) {
      $trimmed = Get-TomlValueStart -Text $text
      if ([string]::IsNullOrEmpty($trimmed)) {
        $parsed = New-TomlParse -Status 'incomplete'
      } else {
        $parsed = ConvertFrom-TomlScalar -Text $trimmed
      }
      if (Test-TomlSame -Left $parsed.Status -Right 'ok') {
        break
      }
      $continueValue = $false
      if ([string]::IsNullOrEmpty($trimmed)) {
        $continueValue = $true
      } elseif ((Test-TomlSame -Left $parsed.Status -Right 'incomplete') -and ($trimmed.StartsWith('"""') -or $trimmed.StartsWith("'''"))) {
        $continueValue = $true
      }
      if ($continueValue) {
        $end += 1
        if ($end -ge $lines.Count) {
          if ($interesting) {
            throw "Unterminated value while reading Codex config: $Path. Do not ask the user for an API key."
          }
          break
        }
        $text = $text + "`n" + [string]$lines[$end]
        continue
      }
      if ($interesting) {
        throw "Invalid experimental_bearer_token or base_url in $Path. Do not ask the user for an API key."
      }
      $end = $index
      break
    }

    if ($null -ne $parsed -and (Test-TomlSame -Left $parsed.Status -Right 'ok') -and $interesting) {
      $value = [string]$parsed.Value
      if (Test-TomlSame -Left $leaf -Right 'experimental_bearer_token') {
        if ([string]::IsNullOrWhiteSpace($value)) {
          throw "experimental_bearer_token is empty in $Path. Do not ask the user for an API key."
        }
        if ($value.Contains("`n") -or $value.Contains("`r")) {
          throw "experimental_bearer_token must be a single-line string in $Path. Do not ask the user for an API key."
        }
        [void] $tokTables.Add($parent)
        [void] $tokValues.Add($value)
      } else {
        [void] $urlTables.Add($parent)
        [void] $urlValues.Add($value)
      }
    }
    $index = $end + 1
  }

  if ($tokValues.Count -eq 0) {
    throw "experimental_bearer_token was not found in $Path. Do not ask the user for an API key."
  }

  $tokenMatches = New-Object System.Collections.Generic.List[int]
  for ($i = 0; $i -lt $tokValues.Count; $i++) {
    $url = ''
    for ($j = 0; $j -lt $urlValues.Count; $j++) {
      if (Test-TomlSame -Left $urlTables[$j] -Right $tokTables[$i]) {
        $url = $urlValues[$j]
      }
    }
    if ($url.ToLowerInvariant().Contains('terln.com')) {
      [void] $tokenMatches.Add($i)
    }
  }

  if ($tokenMatches.Count -gt 0) {
    $chosen = $tokValues[$tokenMatches[0]]
    for ($i = 1; $i -lt $tokenMatches.Count; $i++) {
      if (-not (Test-TomlSame -Left $tokValues[$tokenMatches[$i]] -Right $chosen)) {
        throw "Multiple different experimental_bearer_token values match a Terln base_url in $Path. Do not ask the user for an API key."
      }
    }
    return $chosen
  }

  $chosen = $tokValues[0]
  $allSame = $true
  for ($i = 1; $i -lt $tokValues.Count; $i++) {
    if (-not (Test-TomlSame -Left $tokValues[$i] -Right $chosen)) {
      $allSame = $false
      break
    }
  }
  if ($allSame) {
    return $chosen
  }

  for ($i = 0; $i -lt $tokValues.Count; $i++) {
    if (Test-TomlSame -Left $tokTables[$i] -Right 'model_providers.custom') {
      return $tokValues[$i]
    }
  }

  throw "Multiple experimental_bearer_token values in $Path and none is tied to a Terln base_url. Do not ask the user for an API key."
}

function Get-CodexBearerToken {
  $configPath = Get-CodexConfigPath
  return Read-CodexBearerToken -Path $configPath
}
