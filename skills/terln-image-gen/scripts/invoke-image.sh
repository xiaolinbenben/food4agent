#!/bin/bash

set -euo pipefail

SCRIPT_DIR=$(CDPATH= cd "$(dirname "$0")" && pwd)
# shellcheck disable=SC1091
source "$SCRIPT_DIR/read-codex-bearer.sh"

MODEL='gpt-image-2'
prompt=''
api_key=''
size='1024x1024'
quality='auto'
output_path=''
timeout_seconds='300'
references=()

usage() {
  cat <<'EOF'
Usage:
  /bin/bash invoke-image.sh --prompt <text> [options]

The bearer token is read from experimental_bearer_token in Codex config.toml.
macOS: $HOME/.codex/config.toml
Windows: %USERPROFILE%\.codex\config.toml via invoke-image.ps1
CODEX_HOME/config.toml overrides the directory on both platforms.
Do not pass an API key and do not ask the user for one.

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
    --api-key|--api-key=*)
      echo 'Error: Do not pass --api-key. The script reads experimental_bearer_token from Codex config.toml. Do not ask the user for an API key.' >&2
      exit 1
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
case "$(uname -s 2>/dev/null || true)" in
  MINGW*|MSYS*|CYGWIN*)
    echo 'Error: On Windows, run scripts/invoke-image.ps1 with PowerShell. invoke-image.sh is the macOS script.' >&2
    exit 1
    ;;
esac
if ! api_key=$(load_codex_bearer_token); then
  exit 1
fi
if [[ -z "${api_key//[[:space:]]/}" ]]; then
  echo 'Error: experimental_bearer_token is empty. Do not ask the user for an API key.' >&2
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

for required_command in /usr/bin/curl /usr/bin/osascript /usr/bin/plutil /usr/bin/base64 /usr/bin/mktemp /usr/bin/uuidgen; do
  if [[ ! -x "$required_command" ]]; then
    echo "Error: Missing required macOS system utility: $required_command" >&2
    exit 1
  fi
done

base_url='https://api.terln.com/v1'

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
  output_dir="$PWD/generated-images"
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
auth_header_file="$temp_dir/authorization.header"
printf 'Authorization: Bearer %s\n' "$api_key" > "$auth_header_file"
/bin/chmod 600 "$auth_header_file"
cleanup() {
  /bin/rm -f "$request_file" "$response_file" "$base64_file" "$decoded_file" "$auth_header_file"
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
    -H @"$auth_header_file" \
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
    -H @"$auth_header_file"
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
  api_error=${api_error//"$api_key"/***}
  echo "Error: Image API request failed ($http_status): $api_error" >&2
  exit 1
fi

if /usr/bin/plutil -extract data.0.b64_json raw -o "$base64_file" "$response_file" 2>/dev/null; then
  /usr/bin/sed 's/^data:[^;]*;base64,//' "$base64_file" | /usr/bin/base64 -D > "$decoded_file"
elif image_url=$(/usr/bin/plutil -extract data.0.url raw -o - "$response_file" 2>/dev/null) && [[ -n "$image_url" ]]; then
  /usr/bin/curl -sS --fail --max-time "$timeout_seconds" -o "$decoded_file" "$image_url"
else
  response_preview=$(/usr/bin/head -c 500 "$response_file" | /usr/bin/tr '\n' ' ')
  response_preview=${response_preview//"$api_key"/***}
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
