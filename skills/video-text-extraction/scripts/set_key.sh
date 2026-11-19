#!/usr/bin/env bash
set -euo pipefail

CONFIG_DIR="$HOME/.config/video-text-extraction"
CONFIG_FILE="$CONFIG_DIR/.env"

usage() {
  echo "用法: $0 <x-api-key>"
  exit 1
}

if [[ $# -ne 1 ]]; then
  usage
fi

KEY="$1"
if [[ -z "$KEY" ]]; then
  echo "错误: x-api-key 不能为空" >&2
  exit 1
fi

mkdir -p "$CONFIG_DIR"
printf 'X_API_KEY=%s\n' "$KEY" > "$CONFIG_FILE"
chmod 600 "$CONFIG_FILE"

if [[ ${#KEY} -ge 8 ]]; then
  MASKED="${KEY:0:2}****${KEY: -4}"
else
  MASKED="****"
fi

echo "已保存 x-api-key 到 $CONFIG_FILE"
echo "当前 key 掩码: $MASKED"
