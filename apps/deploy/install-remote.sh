#!/bin/sh
set -eu
dir=${1:?缺少部署目录}
mkdir -p "$dir/data"
install -m 755 /tmp/food4agent-server "$dir/food4agent"
rm -f /tmp/food4agent-server
if [ ! -f "$dir/env" ]; then
  key=$(od -An -N24 -tx1 /dev/urandom | tr -d '[:space:]')
  (umask 077; printf 'SQLITE_PATH=%s/data/app.db\nENCRYPTION_KEY=%s\n' "$dir" "$key" > "$dir/env")
fi
install -m 644 /tmp/food4agent.service /etc/systemd/system/food4agent.service
rm -f /tmp/food4agent.service
systemctl daemon-reload
systemctl enable food4agent
systemctl restart food4agent
systemctl --no-pager --full status food4agent
rm -f /tmp/food4agent-install.sh
