#!/bin/bash

set -euo pipefail

MODEL='gpt-image-2'
prompt=''
size='1024x1024'
quality='auto'
output_path=''
timeout_seconds='300'
references=()

usage() {
  cat <<'EOF'
Usage:
  /bin/bash invoke-image.sh --prompt <text> [options]

Options:
  --reference-image <path>  Local reference image; repeat up to 16 times
  --size <value>            auto or WIDTHxHEIGHT (default: 1024x1024)
  --quality <value>         auto, low, medium, or high (default: auto)
  --output <path>           .png, .jpg, .jpeg, or .webp output path
  --timeout-seconds <n>     Request timeout from 1 to 1800 (default: 300)
  --help                    Show this help
EOF
}

require_value() {
  if [[ $# -lt 2 || "$2" == --* ]]; then
    echo "Error: Missing value for $1" >&2
    exit 1
  fi
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --help)
      usage
      exit 0
      ;;
    --prompt)
      require_value "$@"
      prompt=$2
      shift 2
      ;;
    --reference-image)
      require_value "$@"
      references+=("$2")
      shift 2
      ;;
    --size)
      require_value "$@"
      size=$2
      shift 2
      ;;
    --quality)
      require_value "$@"
      quality=$2
      shift 2
      ;;
    --output)
      require_value "$@"
      output_path=$2
      shift 2
      ;;
    --timeout-seconds)
      require_value "$@"
      timeout_seconds=$2
      shift 2
      ;;
    *)
      echo "Error: Unknown option: $1" >&2
      exit 1
      ;;
  esac
done

if [[ -z "${prompt//[[:space:]]/}" ]]; then
  echo 'Error: --prompt must not be empty' >&2
  exit 1
fi
if [[ ! "$size" =~ ^(auto|[0-9]{2,5}x[0-9]{2,5})$ ]]; then
  echo 'Error: --size must be auto or WIDTHxHEIGHT' >&2
  exit 1
fi
case "$quality" in
  auto|low|medium|high) ;;
  *)
    echo 'Error: --quality must be auto, low, medium, or high' >&2
    exit 1
    ;;
esac
case "$timeout_seconds" in
  ''|*[!0-9]*)
    echo 'Error: --timeout-seconds must be an integer from 1 to 1800' >&2
    exit 1
    ;;
esac
if (( timeout_seconds < 1 || timeout_seconds > 1800 )); then
  echo 'Error: --timeout-seconds must be an integer from 1 to 1800' >&2
  exit 1
fi
if (( ${#references[@]} > 16 )); then
  echo 'Error: --reference-image supports at most 16 files' >&2
  exit 1
fi

for required_command in /usr/bin/curl /usr/bin/awk /usr/bin/osascript /usr/bin/plutil /usr/bin/base64 /usr/bin/mktemp /usr/bin/uuidgen; do
  if [[ ! -x "$required_command" ]]; then
    echo "Error: Missing required macOS system utility: $required_command" >&2
    exit 1
  fi
done

config_path="$HOME/.codex/config.toml"
if [[ ! -f "$config_path" ]]; then
  echo "Error: Missing Codex config: $config_path" >&2
  exit 1
fi

read_config_value() {
  local key=$1
  /usr/bin/awk -v wanted="$key" '
    /^[[:space:]]*\[[^]]+\][[:space:]]*$/ {
      table = $0
      gsub(/^[[:space:]]+|[[:space:]]+$/, "", table)
      in_custom = (table == "[model_providers.custom]")
      next
    }
    in_custom {
      line = $0
      if (line ~ "^[[:space:]]*" wanted "[[:space:]]*=") {
        sub("^[[:space:]]*" wanted "[[:space:]]*=[[:space:]]*", "", line)
        print line
        exit
      }
    }
  ' "$config_path"
}

decode_config_value() {
  local raw=$1
  case "$raw" in
    \"*\")
      /usr/bin/osascript -l JavaScript - "$raw" <<'JXA'
function run(argv) {
  return JSON.parse(argv[0]);
}
JXA
      ;;
    \'*\')
      raw=${raw#\'}
      raw=${raw%\'}
      printf '%s\n' "$raw"
      ;;
    *)
      printf '%s\n' "$raw"
      ;;
  esac
}

base_url_raw=$(read_config_value 'base_url')
api_key_raw=$(read_config_value 'experimental_bearer_token')
if [[ -z "$base_url_raw" ]]; then
  echo "Error: Missing base_url in [model_providers.custom] of $config_path" >&2
  exit 1
fi
if [[ -z "$api_key_raw" ]]; then
  echo "Error: Missing experimental_bearer_token in [model_providers.custom] of $config_path" >&2
  exit 1
fi
base_url=$(decode_config_value "$base_url_raw")
api_key=$(decode_config_value "$api_key_raw")
case "$base_url" in
  http://*|https://*) ;;
  *)
    echo "Error: Invalid base_url in [model_providers.custom] of $config_path" >&2
    exit 1
    ;;
esac
base_url=${base_url%/}

load_codex_proxy() {
  local key value line
  for key in HTTPS_PROXY https_proxy HTTP_PROXY http_proxy ALL_PROXY all_proxy; do
    value=$(/usr/bin/printenv "$key" 2>/dev/null || true)
    if [[ -n "$value" ]]; then
      return
    fi
  done

  local env_path="$HOME/.codex/.env"
  [[ -f "$env_path" ]] || return
  while IFS= read -r line || [[ -n "$line" ]]; do
    line=${line#export }
    [[ "$line" == *=* ]] || continue
    key=${line%%=*}
    value=${line#*=}
    key=$(printf '%s' "$key" | /usr/bin/sed 's/^[[:space:]]*//;s/[[:space:]]*$//')
    value=$(printf '%s' "$value" | /usr/bin/sed 's/^[[:space:]]*//;s/[[:space:]]*$//')
    case "$value" in
      \"*\") value=${value#\"}; value=${value%\"} ;;
      \'*\') value=${value#\'}; value=${value%\'} ;;
    esac
    case "$key" in
      HTTPS_PROXY|https_proxy|HTTP_PROXY|http_proxy|ALL_PROXY|all_proxy)
        if [[ -n "$value" ]]; then
          export "$key=$value"
        fi
        ;;
    esac
  done < "$env_path"
}

load_codex_proxy

resolved_references=()
for reference in ${references[@]+"${references[@]}"}; do
  case "$reference" in
    http://*|https://*)
      echo "Error: Reference image must be a local file path: $reference" >&2
      exit 1
      ;;
  esac
  if [[ ! -f "$reference" ]]; then
    echo "Error: Reference image not found: $reference" >&2
    exit 1
  fi
  extension=$(printf '%s' "${reference##*.}" | /usr/bin/tr '[:upper:]' '[:lower:]')
  case "$extension" in
    png|jpg|jpeg|webp) ;;
    *)
      echo "Error: Unsupported reference image type '.$extension': $reference" >&2
      exit 1
      ;;
  esac
  reference_dir=$(CDPATH= cd "$(/usr/bin/dirname "$reference")" && /bin/pwd -P)
  resolved_references+=("$reference_dir/$(/usr/bin/basename "$reference")")
done

if [[ -z "$output_path" ]]; then
  output_dir="$PWD/.codex/generated-images"
  /bin/mkdir -p "$output_dir"
  short_id=$(/usr/bin/uuidgen | /usr/bin/tr -d '-' | /usr/bin/cut -c1-8)
  output_path="$output_dir/$(/bin/date '+%Y%m%d-%H%M%S')-$short_id.png"
else
  output_dir=$(/usr/bin/dirname "$output_path")
  /bin/mkdir -p "$output_dir"
  output_dir=$(CDPATH= cd "$output_dir" && /bin/pwd -P)
  output_path="$output_dir/$(/usr/bin/basename "$output_path")"
fi

if [[ -e "$output_path" ]]; then
  echo "Error: --output already exists: $output_path" >&2
  exit 1
fi
output_extension=$(printf '%s' "${output_path##*.}" | /usr/bin/tr '[:upper:]' '[:lower:]')
case "$output_extension" in
  png) output_format='png' ;;
  jpg|jpeg) output_format='jpeg' ;;
  webp) output_format='webp' ;;
  *)
    echo "Error: --output must end in .png, .jpg, .jpeg, or .webp: $output_path" >&2
    exit 1
    ;;
esac

temp_dir=$(/usr/bin/mktemp -d "${TMPDIR:-/tmp}/terln-image-gen.XXXXXX")
request_file="$temp_dir/request.json"
response_file="$temp_dir/response.json"
base64_file="$temp_dir/image.base64"
decoded_file="$temp_dir/generated.$output_extension"
cleanup() {
  /bin/rm -f "$request_file" "$response_file" "$base64_file" "$decoded_file"
  /bin/rmdir "$temp_dir" 2>/dev/null || true
}
trap cleanup EXIT

if (( ${#resolved_references[@]} == 0 )); then
  operation='generation'
  /usr/bin/osascript -l JavaScript - "$MODEL" "$prompt" "$size" "$quality" "$output_format" > "$request_file" <<'JXA'
function run(argv) {
  return JSON.stringify({
    model: argv[0],
    prompt: argv[1],
    size: argv[2],
    quality: argv[3],
    output_format: argv[4],
    n: 1
  });
}
JXA
  set +e
  http_status=$(/usr/bin/curl -sS -o "$response_file" -w '%{http_code}' \
    --max-time "$timeout_seconds" \
    -X POST "$base_url/images/generations" \
    -H "Authorization: Bearer $api_key" \
    -H 'Content-Type: application/json' \
    --data-binary "@$request_file")
  curl_status=$?
  set -e
else
  operation='edit'
  curl_args=(
    -sS
    -o "$response_file"
    -w '%{http_code}'
    --max-time "$timeout_seconds"
    -X POST "$base_url/images/edits"
    -H "Authorization: Bearer $api_key"
    --form-string "model=$MODEL"
    --form-string "prompt=$prompt"
    --form-string "size=$size"
    --form-string "quality=$quality"
    --form-string "output_format=$output_format"
    --form-string 'n=1'
  )
  for reference in ${references[@]+"${references[@]}"}; do
    curl_args+=(-F "image[]=@$reference")
  done
  set +e
  http_status=$(/usr/bin/curl "${curl_args[@]}")
  curl_status=$?
  set -e
fi

if (( curl_status != 0 )); then
  echo "Error: Image API request failed in curl with exit code $curl_status" >&2
  exit 1
fi
case "$http_status" in
  ''|*[!0-9]*)
    echo "Error: Image API returned an invalid HTTP status: $http_status" >&2
    exit 1
    ;;
esac
if (( http_status < 200 || http_status >= 300 )); then
  api_error=$(/usr/bin/plutil -extract error.message raw -o - "$response_file" 2>/dev/null || true)
  if [[ -z "$api_error" ]]; then
    api_error=$(/usr/bin/head -c 500 "$response_file" | /usr/bin/tr '\n' ' ')
  fi
  echo "Error: Image API request failed ($http_status): $api_error" >&2
  exit 1
fi

if /usr/bin/plutil -extract data.0.b64_json raw -o "$base64_file" "$response_file" 2>/dev/null; then
  /usr/bin/sed 's/^data:[^;]*;base64,//' "$base64_file" | /usr/bin/base64 -D > "$decoded_file"
elif image_url=$(/usr/bin/plutil -extract data.0.url raw -o - "$response_file" 2>/dev/null) && [[ -n "$image_url" ]]; then
  /usr/bin/curl -sS --fail --max-time "$timeout_seconds" -o "$decoded_file" "$image_url"
else
  response_preview=$(/usr/bin/head -c 500 "$response_file" | /usr/bin/tr '\n' ' ')
  echo "Error: Image API response contains neither b64_json nor url: $response_preview" >&2
  exit 1
fi

if [[ ! -s "$decoded_file" ]]; then
  echo 'Error: Image API produced an empty image file' >&2
  exit 1
fi
/bin/mv "$decoded_file" "$output_path"

/usr/bin/osascript -l JavaScript - "$operation" "$MODEL" "$size" "$output_path" <<'JXA'
function run(argv) {
  const outputPath = argv[3];
  return JSON.stringify({
    status: "completed",
    operation: argv[0],
    model: argv[1],
    size: argv[2],
    saved_files: [outputPath],
    display_markdown: [`![Generated image](<${outputPath}>)`]
  });
}
JXA
