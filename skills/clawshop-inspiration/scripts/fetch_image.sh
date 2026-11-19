#!/bin/bash
# fetch_image.sh - 下载商品图片到本地临时目录
# 用法: bash fetch_image.sh "<URL>" [filename]
# 返回: 本地文件路径（成功）或错误信息（失败）

set -e

URL="$1"
if [ -z "$URL" ]; then
  echo "Usage: bash fetch_image.sh <URL> [filename]" >&2
  exit 1
fi

# 自动生成文件名
if [ -n "$2" ]; then
  FILENAME="$2"
else
  # 从 URL 提取文件名，去掉 query string
  FILENAME="$(basename "$URL" | cut -d'?' -f1)"
  # 如果文件名不含扩展名，尝试根据 URL 路径推断
  if [[ "$FILENAME" != *.* ]]; then
    FILENAME="img_$(date +%s).jpg"
  fi
fi

DEST_DIR="/tmp/openclaw/uploads"
mkdir -p "$DEST_DIR"
DEST="$DEST_DIR/$FILENAME"

# 下载，带 User-Agent 避免部分防盗链
curl -sL \
  -H "User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36" \
  -H "Referer: https://www.taobao.com/" \
  --max-time 30 \
  -o "$DEST" \
  "$URL"

# 检查文件是否有效（至少 1KB）
SIZE=$(wc -c < "$DEST")
if [ "$SIZE" -lt 1024 ]; then
  echo "ERROR: Downloaded file too small (${SIZE} bytes), may be blocked" >&2
  rm -f "$DEST"
  exit 1
fi

echo "$DEST"
