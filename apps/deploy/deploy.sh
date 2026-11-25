#!/bin/sh
set -eu

cd "$(dirname "$0")/.."

host=${1:?用法: deploy/deploy.sh user@host}
dir=${DEPLOY_DIR:-/opt/food4agent}
arch=${GOARCH:-amd64}

case $dir in
  *[!A-Za-z0-9/_-]*)
    echo "DEPLOY_DIR 只允许字母、数字、斜线和短横线"
    exit 1
    ;;
esac
case $arch in
  amd64|arm64) ;;
  *)
    echo "GOARCH 只允许 amd64 或 arm64"
    exit 1
    ;;
esac

echo "本地构建前端并打进 Linux 二进制 ($arch)"
GOARCH="$arch" make linux-build
artifact="server/bin/food4agent-linux-$arch"
test -f "$artifact"

unit=$(mktemp)
sed "s#__DIR__#$dir#g" deploy/food4agent.service > "$unit"
trap 'rm -f "$unit"' EXIT

echo "上传到 $host:$dir"
scp "$artifact" "$host:/tmp/food4agent-server"
scp "$unit" "$host:/tmp/food4agent.service"
scp deploy/install-remote.sh "$host:/tmp/food4agent-install.sh"

if ssh "$host" '[ "$(id -u)" -eq 0 ]'; then
  ssh "$host" "sh /tmp/food4agent-install.sh '$dir'"
else
  ssh -t "$host" "sudo sh /tmp/food4agent-install.sh '$dir'"
fi

echo "服务已在服务器本机 127.0.0.1:8888 运行。把域名反代到这个地址即可。"
