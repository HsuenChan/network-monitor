#!/usr/bin/env bash
# 停止所有背景擷取與網頁伺服器。
cd "$(dirname "$0")"

declare -a items=("conn:連線擷取" "ports:埠擷取" "server:網頁伺服器")
for item in "${items[@]}"; do
  key="${item%%:*}"; label="${item##*:}"
  pidfile=".${key}.pid"
  if [ -f "$pidfile" ]; then
    pid="$(cat "$pidfile")"
    if kill "$pid" 2>/dev/null; then
      echo "✓ 已停止 ${label} (pid ${pid})"
    fi
    rm -f "$pidfile"
  fi
done
echo "監控已停止。"
