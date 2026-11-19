#!/usr/bin/env bash
set -euo pipefail

API_URL="https://agent.mathmind.cn/minimalist/api/video-audio/recognize"
CONFIG_FILE="$HOME/.config/video-text-extraction/.env"

print_usage() {
  cat <<'EOF'
用法:
  抖音链接: ./extract.sh --url <videoUrl> [--key <x-api-key>]
  本地文件: ./extract.sh --file </absolute/path/video.mp4> [--key <x-api-key>]

参数说明:
  --url   公网可访问视频地址（支持抖音短链接）
  --file  本地 .mp4 文件路径
  --key   本次调用临时使用的 x-api-key（优先级最高）
EOF
}

INPUT_URL=""
INPUT_FILE=""
INLINE_KEY=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --url)
      [[ $# -ge 2 ]] || { echo "错误: --url 缺少值" >&2; exit 1; }
      INPUT_URL="$2"
      shift 2
      ;;
    --file)
      [[ $# -ge 2 ]] || { echo "错误: --file 缺少值" >&2; exit 1; }
      INPUT_FILE="$2"
      shift 2
      ;;
    --key)
      [[ $# -ge 2 ]] || { echo "错误: --key 缺少值" >&2; exit 1; }
      INLINE_KEY="$2"
      shift 2
      ;;
    -h|--help)
      print_usage
      exit 0
      ;;
    *)
      echo "错误: 不支持的参数 $1" >&2
      print_usage
      exit 1
      ;;
  esac
done

if [[ -n "$INPUT_URL" && -n "$INPUT_FILE" ]]; then
  echo "错误: --url 和 --file 只能二选一" >&2
  exit 1
fi

if [[ -z "$INPUT_URL" && -z "$INPUT_FILE" ]]; then
  echo "错误: 必须提供 --url 或 --file" >&2
  print_usage
  exit 1
fi

X_API_KEY="${INLINE_KEY:-${X_API_KEY:-}}"
if [[ -z "$X_API_KEY" && -f "$CONFIG_FILE" ]]; then
  set -a
  # shellcheck disable=SC1090
  . "$CONFIG_FILE"
  set +a
  X_API_KEY="${X_API_KEY:-}"
fi

if [[ -z "$X_API_KEY" ]]; then
  echo "错误: 未找到 x-api-key，请先执行 ./set_key.sh <x-api-key> 或传入 --key" >&2
  exit 1
fi

VIDEO_URL="$INPUT_URL"

if [[ -n "$INPUT_FILE" ]]; then
  if [[ ! -f "$INPUT_FILE" ]]; then
    echo "错误: 文件不存在: $INPUT_FILE" >&2
    exit 1
  fi

  lower_name="${INPUT_FILE,,}"
  if [[ "$lower_name" != *.mp4 ]]; then
    echo "错误: 仅支持 .mp4 文件" >&2
    exit 1
  fi

  echo "正在上传本地文件..."
  VIDEO_URL="$(curl --silent --show-error --upload-file "$INPUT_FILE" "https://transfer.sh/$(basename "$INPUT_FILE")")"
  if [[ -z "$VIDEO_URL" ]]; then
    echo "错误: 文件上传失败，未获得公网 URL" >&2
    exit 1
  fi
fi

echo "正在调用文案提取接口..."
PAYLOAD=$(printf '{"videoUrl":"%s"}' "$VIDEO_URL")

TMP_BODY=$(mktemp)
HTTP_CODE=$(curl --silent --show-error --location "$API_URL" \
  --header 'Content-Type: application/json' \
  --header "x-api-key: $X_API_KEY" \
  --data "$PAYLOAD" \
  --output "$TMP_BODY" \
  --write-out '%{http_code}')

if [[ "$HTTP_CODE" != "200" ]]; then
  echo "接口调用失败，HTTP 状态码: $HTTP_CODE" >&2
  cat "$TMP_BODY" >&2
  rm -f "$TMP_BODY"
  exit 1
fi

cat "$TMP_BODY"
rm -f "$TMP_BODY"
