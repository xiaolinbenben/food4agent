#!/bin/bash

# Read experimental_bearer_token from Codex config.toml.
# macOS/Linux: $HOME/.codex/config.toml
# Windows: %USERPROFILE%\.codex\config.toml
# Both: $CODEX_HOME/config.toml when CODEX_HOME is set.

TOML_SCALAR_STATE=""
TOML_SCALAR_VALUE=""
TOML_TRIMMED=""

trim_left_ws() {
  local s="$1"
  s="${s#"${s%%[![:space:]]*}"}"
  printf '%s' "$s"
}

normalize_toml_key() {
  local k="$1"
  k="${k#"${k%%[![:space:]]*}"}"
  k="${k%"${k##*[![:space:]]}"}"
  if [[ ${#k} -ge 2 ]]; then
    local first=${k:0:1}
    local last=${k#${k%?}}
    if [[ ( "$first" == '"' && "$last" == '"' ) || ( "$first" == "'" && "$last" == "'" ) ]]; then
      k=${k:1:${#k}-2}
    fi
  fi
  k="${k//[[:space:]]/}"
  printf '%s' "$k"
}

trailing_ok() {
  local rest="$1"
  rest="${rest#"${rest%%[![:space:]]*}"}"
  if [[ -z "$rest" || "$rest" == \#* ]]; then
    return 0
  fi
  return 1
}

decode_codepoint() {
  local hex="$1"
  local code oct
  code=$((16#$hex))
  if (( code < 0 || code > 1114111 || (code >= 55296 && code <= 57343) )); then
    return 1
  fi
  if (( code <= 255 )); then
    oct=$(printf '%03o' "$code")
    printf "\\${oct}"
    return 0
  fi
  if [[ -x /usr/bin/perl ]]; then
    /usr/bin/perl -e 'binmode(STDOUT, ":utf8"); print chr(hex($ARGV[0]))' "$hex"
    return 0
  fi
  return 1
}

append_escape() {
  ESC_CHAR=""
  case "$1" in
    '"') ESC_CHAR='"' ;;
    '\') ESC_CHAR='\' ;;
    n) ESC_CHAR=$'\n' ;;
    t) ESC_CHAR=$'\t' ;;
    r) ESC_CHAR=$'\r' ;;
    b) ESC_CHAR=$'\b' ;;
    f) ESC_CHAR=$'\f' ;;
    *) return 1 ;;
  esac
  return 0
}

trim_toml_value_start() {
  local s="$1"
  while true; do
    s="${s#"${s%%[![:space:]]*}"}"
    if [[ "$s" == \#* ]]; then
      if [[ "$s" != *$'\n'* ]]; then
        TOML_TRIMMED=""
        return 0
      fi
      s="${s#*$'\n'}"
      continue
    fi
    TOML_TRIMMED="$s"
    return 0
  done
}

parse_basic_string() {
  local s="$1"
  local i=1
  local n=${#s}
  local out="" c next hex digits
  while (( i < n )); do
    c=${s:i:1}
    if [[ "$c" == '\' ]]; then
      if (( i + 1 >= n )); then
        TOML_SCALAR_STATE=incomplete
        return 1
      fi
      next=${s:i+1:1}
      if [[ "$next" == "u" || "$next" == "U" ]]; then
        digits=4
        if [[ "$next" == "U" ]]; then
          digits=8
        fi
        if (( i + 2 + digits > n )); then
          TOML_SCALAR_STATE=incomplete
          return 1
        fi
        hex=${s:i+2:digits}
        if [[ ! "$hex" =~ ^[0-9A-Fa-f]+$ ]] || (( ${#hex} != digits )); then
          TOML_SCALAR_STATE=invalid
          return 1
        fi
        if ! ESC_CHAR=$(decode_codepoint "$hex"); then
          TOML_SCALAR_STATE=invalid
          return 1
        fi
        out="${out}${ESC_CHAR}"
        i=$((i + 2 + digits))
        continue
      fi
      if ! append_escape "$next"; then
        TOML_SCALAR_STATE=invalid
        return 1
      fi
      out="${out}${ESC_CHAR}"
      i=$((i + 2))
      continue
    fi
    if [[ "$c" == $'\n' || "$c" == $'\r' ]]; then
      TOML_SCALAR_STATE=invalid
      return 1
    fi
    if [[ "$c" == '"' ]]; then
      if ! trailing_ok "${s:i+1}"; then
        TOML_SCALAR_STATE=invalid
        return 1
      fi
      TOML_SCALAR_VALUE="$out"
      TOML_SCALAR_STATE=ok
      return 0
    fi
    out="${out}${c}"
    i=$((i + 1))
  done
  TOML_SCALAR_STATE=incomplete
  return 1
}

parse_literal_string() {
  local s="$1"
  local i=1
  local n=${#s}
  local out="" c
  while (( i < n )); do
    c=${s:i:1}
    if [[ "$c" == $'\n' || "$c" == $'\r' ]]; then
      TOML_SCALAR_STATE=invalid
      return 1
    fi
    if [[ "$c" == "'" ]]; then
      if ! trailing_ok "${s:i+1}"; then
        TOML_SCALAR_STATE=invalid
        return 1
      fi
      TOML_SCALAR_VALUE="$out"
      TOML_SCALAR_STATE=ok
      return 0
    fi
    out="${out}${c}"
    i=$((i + 1))
  done
  TOML_SCALAR_STATE=incomplete
  return 1
}

parse_multiline_basic() {
  local s="$1"
  local i=3
  local n=${#s}
  local out="" c next hex digits
  if (( n >= 4 )) && [[ ${s:3:1} == $'\n' ]]; then
    i=4
  fi
  while (( i < n )); do
    if (( i + 2 < n )) && [[ ${s:i:3} == '"""' ]]; then
      if ! trailing_ok "${s:i+3}"; then
        TOML_SCALAR_STATE=invalid
        return 1
      fi
      TOML_SCALAR_VALUE="$out"
      TOML_SCALAR_STATE=ok
      return 0
    fi
    c=${s:i:1}
    if [[ "$c" == '\' ]]; then
      if (( i + 1 >= n )); then
        TOML_SCALAR_STATE=incomplete
        return 1
      fi
      next=${s:i+1:1}
      if [[ "$next" == $'\n' ]]; then
        i=$((i + 2))
        while (( i < n )); do
          c=${s:i:1}
          if [[ "$c" != " " && "$c" != $'\t' && "$c" != $'\r' ]]; then
            break
          fi
          i=$((i + 1))
        done
        continue
      fi
      if [[ "$next" == "u" || "$next" == "U" ]]; then
        digits=4
        if [[ "$next" == "U" ]]; then
          digits=8
        fi
        if (( i + 2 + digits > n )); then
          TOML_SCALAR_STATE=incomplete
          return 1
        fi
        hex=${s:i+2:digits}
        if [[ ! "$hex" =~ ^[0-9A-Fa-f]+$ ]] || (( ${#hex} != digits )); then
          TOML_SCALAR_STATE=invalid
          return 1
        fi
        if ! ESC_CHAR=$(decode_codepoint "$hex"); then
          TOML_SCALAR_STATE=invalid
          return 1
        fi
        out="${out}${ESC_CHAR}"
        i=$((i + 2 + digits))
        continue
      fi
      if ! append_escape "$next"; then
        TOML_SCALAR_STATE=invalid
        return 1
      fi
      out="${out}${ESC_CHAR}"
      i=$((i + 2))
      continue
    fi
    out="${out}${c}"
    i=$((i + 1))
  done
  TOML_SCALAR_STATE=incomplete
  return 1
}

parse_multiline_literal() {
  local s="$1"
  local i=3
  local n=${#s}
  local out=""
  if (( n >= 4 )) && [[ ${s:3:1} == $'\n' ]]; then
    i=4
  fi
  while (( i < n )); do
    if (( i + 2 < n )) && [[ ${s:i:3} == "'''" ]]; then
      if ! trailing_ok "${s:i+3}"; then
        TOML_SCALAR_STATE=invalid
        return 1
      fi
      TOML_SCALAR_VALUE="$out"
      TOML_SCALAR_STATE=ok
      return 0
    fi
    out="${out}${s:i:1}"
    i=$((i + 1))
  done
  TOML_SCALAR_STATE=incomplete
  return 1
}

parse_bare_scalar() {
  local s="$1"
  local bare="$s"
  local cut
  if [[ "$bare" == *$'\n'* ]]; then
    bare="${bare%%$'\n'*}"
  fi
  if [[ "$bare" =~ ^(.*)[[:space:]]# ]]; then
    cut="${BASH_REMATCH[1]}"
    bare="$cut"
  elif [[ "$bare" == \#* ]]; then
    TOML_SCALAR_STATE=invalid
    return 1
  fi
  bare="${bare%"${bare##*[![:space:]]}"}"
  bare="${bare#"${bare%%[![:space:]]*}"}"
  if [[ -z "$bare" ]]; then
    TOML_SCALAR_STATE=invalid
    return 1
  fi
  TOML_SCALAR_VALUE="$bare"
  TOML_SCALAR_STATE=ok
  return 0
}

parse_toml_scalar() {
  local s="$1"
  TOML_SCALAR_VALUE=""
  TOML_SCALAR_STATE=invalid
  if [[ "$s" == '"""'* ]]; then
    if parse_multiline_basic "$s"; then
      return 0
    fi
    return 1
  fi
  if [[ "$s" == "'''"* ]]; then
    if parse_multiline_literal "$s"; then
      return 0
    fi
    return 1
  fi
  if [[ "$s" == '"'* ]]; then
    if parse_basic_string "$s"; then
      return 0
    fi
    return 1
  fi
  if [[ "$s" == "'"* ]]; then
    if parse_literal_string "$s"; then
      return 0
    fi
    return 1
  fi
  if parse_bare_scalar "$s"; then
    return 0
  fi
  return 1
}

windows_profile_to_unix() {
  local win="$1"
  local unix drive
  win="${win%$'\r'}"
  unix="${win//\\//}"
  if [[ "$unix" =~ ^([A-Za-z]):(.*)$ ]]; then
    drive=$(printf '%s' "${BASH_REMATCH[1]}" | /usr/bin/tr '[:upper:]' '[:lower:]')
    unix="/${drive}${BASH_REMATCH[2]}"
  fi
  printf '%s' "$unix"
}

normalize_codex_root() {
  local root="$1"
  if [[ "$root" =~ ^[A-Za-z]:[\\/] ]]; then
    root=$(windows_profile_to_unix "$root")
  fi
  while [[ "$root" == */ ]]; do
    root="${root%/}"
  done
  printf '%s' "$root"
}

codex_is_windows() {
  local platform="${1:-}"
  if [[ -z "$platform" ]]; then
    platform=$(uname -s 2>/dev/null || true)
  fi
  case "$platform" in
    Windows|windows|Win*|MINGW*|MSYS*|CYGWIN*)
      return 0
      ;;
  esac
  if [[ "${OS:-}" == "Windows_NT" && "$platform" != Darwin && "$platform" != Linux ]]; then
    return 0
  fi
  return 1
}

codex_config_path_for_platform() {
  local platform="$1"
  local root=""
  if [[ -n "${CODEX_HOME:-}" ]]; then
    root=$(normalize_codex_root "$CODEX_HOME")
    printf '%s\n' "$root/config.toml"
    return 0
  fi
  if codex_is_windows "$platform"; then
    if [[ -z "${USERPROFILE:-}" ]]; then
      echo "Error: USERPROFILE is not set. On Windows the Codex config is %USERPROFILE%\\.codex\\config.toml. Set CODEX_HOME if Codex uses another directory. Do not ask the user for an API key." >&2
      return 1
    fi
    root=$(normalize_codex_root "$USERPROFILE")
    printf '%s\n' "$root/.codex/config.toml"
    return 0
  fi
  if [[ -z "${HOME:-}" ]]; then
    echo "Error: HOME is not set. On macOS the Codex config is ~/.codex/config.toml. Set CODEX_HOME if Codex uses another directory. Do not ask the user for an API key." >&2
    return 1
  fi
  root=$(normalize_codex_root "$HOME")
  printf '%s\n' "$root/.codex/config.toml"
  return 0
}

codex_config_path() {
  local platform
  platform=$(uname -s 2>/dev/null || true)
  codex_config_path_for_platform "$platform"
}

parse_bearer_file() {
  local file="$1"
  local -a lines
  local -a tok_tables
  local -a tok_values
  local -a url_tables
  local -a url_values
  local line="" idx=0 total=0 end=0
  local table="" lhs="" rhs="" key="" full_key="" parent="" leaf=""
  local interesting=0 text="" value="" next_line=""
  local count=0 i=0 j=0 chosen="" url="" url_lc=""
  local -a matches
  lines=()
  tok_tables=()
  tok_values=()
  url_tables=()
  url_values=()
  matches=()

  if [[ ! -f "$file" ]]; then
    echo "Error: Codex config not found: $file. Do not ask the user for an API key." >&2
    return 1
  fi
  if [[ ! -r "$file" ]]; then
    echo "Error: Codex config is not readable: $file. Do not ask the user for an API key." >&2
    return 1
  fi

  while IFS= read -r line || [[ -n "$line" ]]; do
    lines+=("$line")
  done < "$file"
  total=${#lines[@]}

  while (( idx < total )); do
    line="${lines[$idx]}"
    line=${line%$'\r'}
    if (( idx == 0 )); then
      line=${line#$'\ufeff'}
      line=${line#$'\xef\xbb\xbf'}
    fi
    line="${line#"${line%%[![:space:]]*}"}"
    if [[ -z "$line" || "$line" == \#* ]]; then
      idx=$((idx + 1))
      continue
    fi
    if [[ "$line" =~ ^\[\[([^]]+)\]\][[:space:]]*(#.*)?$ ]]; then
      table=$(normalize_toml_key "${BASH_REMATCH[1]}")
      idx=$((idx + 1))
      continue
    fi
    if [[ "$line" =~ ^\[([^]]+)\][[:space:]]*(#.*)?$ ]]; then
      table=$(normalize_toml_key "${BASH_REMATCH[1]}")
      idx=$((idx + 1))
      continue
    fi
    if [[ "$line" != *"="* ]]; then
      idx=$((idx + 1))
      continue
    fi

    lhs="${line%%=*}"
    lhs="${lhs%"${lhs##*[![:space:]]}"}"
    lhs="${lhs#"${lhs%%[![:space:]]*}"}"
    rhs="${line#*=}"
    rhs=$(trim_left_ws "$rhs")
    key=$(normalize_toml_key "$lhs")
    if [[ -z "$key" ]]; then
      idx=$((idx + 1))
      continue
    fi
    if [[ -n "$table" ]]; then
      full_key="${table}.${key}"
    else
      full_key="$key"
    fi
    if [[ "$full_key" == *.* ]]; then
      parent="${full_key%.*}"
    else
      parent=""
    fi
    leaf="${full_key##*.}"
    interesting=0
    if [[ "$leaf" == "experimental_bearer_token" || "$leaf" == "base_url" ]]; then
      interesting=1
    fi

    text="$rhs"
    end=$idx
    while true; do
      trim_toml_value_start "$text"
      if [[ -z "$TOML_TRIMMED" ]]; then
        TOML_SCALAR_STATE=incomplete
      elif parse_toml_scalar "$TOML_TRIMMED"; then
        :
      fi
      if [[ "$TOML_SCALAR_STATE" == "ok" ]]; then
        break
      fi
      continue_value=0
      if [[ -z "$TOML_TRIMMED" ]]; then
        continue_value=1
      elif [[ "$TOML_SCALAR_STATE" == "incomplete" && ( "$TOML_TRIMMED" == '"""'* || "$TOML_TRIMMED" == "'''"* ) ]]; then
        continue_value=1
      fi
      if (( continue_value )); then
        end=$((end + 1))
        if (( end >= total )); then
          if (( interesting )); then
            echo "Error: Unterminated value while reading Codex config: $file. Do not ask the user for an API key." >&2
            return 1
          fi
          break
        fi
        next_line="${lines[$end]}"
        next_line=${next_line%$'\r'}
        text="${text}"$'\n'"${next_line}"
        continue
      fi
      if (( interesting )); then
        echo "Error: Invalid experimental_bearer_token or base_url in $file. Do not ask the user for an API key." >&2
        return 1
      fi
      end=$idx
      break
    done

    if [[ "$TOML_SCALAR_STATE" == "ok" && "$interesting" -eq 1 ]]; then
      value="$TOML_SCALAR_VALUE"
      if [[ "$leaf" == "experimental_bearer_token" ]]; then
        if [[ -z "${value//[[:space:]]/}" ]]; then
          echo "Error: experimental_bearer_token is empty in $file. Do not ask the user for an API key." >&2
          return 1
        fi
        if [[ "$value" == *$'\n'* || "$value" == *$'\r'* ]]; then
          echo "Error: experimental_bearer_token must be a single-line string in $file. Do not ask the user for an API key." >&2
          return 1
        fi
        tok_tables+=("$parent")
        tok_values+=("$value")
      else
        url_tables+=("$parent")
        url_values+=("$value")
      fi
    fi
    idx=$end
    idx=$((idx + 1))
  done

  count=${#tok_values[@]}
  if (( count == 0 )); then
    echo "Error: experimental_bearer_token was not found in $file. Do not ask the user for an API key." >&2
    return 1
  fi

  matches=()
  for (( i=0; i<count; i++ )); do
    url=""
    for (( j=0; j<${#url_values[@]}; j++ )); do
      if [[ "${url_tables[$j]}" == "${tok_tables[$i]}" ]]; then
        url="${url_values[$j]}"
      fi
    done
    url_lc=$(printf '%s' "$url" | /usr/bin/tr '[:upper:]' '[:lower:]')
    if [[ "$url_lc" == *terln.com* ]]; then
      matches+=("$i")
    fi
  done

  if (( ${#matches[@]} > 0 )); then
    chosen="${tok_values[${matches[0]}]}"
    for (( i=1; i<${#matches[@]}; i++ )); do
      if [[ "${tok_values[${matches[$i]}]}" != "$chosen" ]]; then
        echo "Error: Multiple different experimental_bearer_token values match a Terln base_url in $file. Do not ask the user for an API key." >&2
        return 1
      fi
    done
    printf '%s' "$chosen"
    return 0
  fi

  chosen="${tok_values[0]}"
  for (( i=1; i<count; i++ )); do
    if [[ "${tok_values[$i]}" != "$chosen" ]]; then
      chosen=""
      break
    fi
  done
  if [[ -n "$chosen" ]]; then
    printf '%s' "$chosen"
    return 0
  fi

  for (( i=0; i<count; i++ )); do
    if [[ "${tok_tables[$i]}" == "model_providers.custom" ]]; then
      printf '%s' "${tok_values[$i]}"
      return 0
    fi
  done

  echo "Error: Multiple experimental_bearer_token values in $file and none is tied to a Terln base_url. Do not ask the user for an API key." >&2
  return 1
}

load_codex_bearer_token() {
  local config="" status=0
  config=$(codex_config_path)
  status=$?
  if (( status != 0 )); then
    return 1
  fi
  parse_bearer_file "$config"
}
