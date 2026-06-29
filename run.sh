#!/usr/bin/env bash
# 啟動 network-monitor：連線擷取 + 埠擷取 + 本機網頁伺服器，並開啟監控首頁。
set -euo pipefail

cd "$(dirname "$0")"
PORT="${PORT:-8791}"

# 若已在跑，先停掉舊的
for f in .conn.pid .ports.pid .server.pid; do
  [ -f "$f" ] && kill "$(cat "$f")" 2>/dev/null || true
done

# 0) 裝置身分 + 端點代理偵測（公司能看到分頁）一次性擷取
python3 my-monitor/identity.py > /dev/null 2>&1 && echo "✓ 裝置身分已擷取"
python3 my-monitor/agents.py  > /dev/null 2>&1 && echo "✓ 端點代理已掃描"

# 1) 我自己的監控：對外連線擷取 → my-monitor/connections.json
nohup python3 my-monitor/collect.py > my-monitor/collect.log 2>&1 &
echo $! > .conn.pid; disown 2>/dev/null || true
echo "✓ 連線擷取啟動 (pid $(cat .conn.pid))"

# 2) 我自己的監控：監聽埠擷取 → my-monitor/ports.json
nohup python3 my-monitor/ports.py > my-monitor/ports.log 2>&1 &
echo $! > .ports.pid; disown 2>/dev/null || true
echo "✓ 埠擷取啟動 (pid $(cat .ports.pid))"

# 3) 本機網頁伺服器（artifact 沙箱讀不到本機，所以走 localhost）
nohup python3 -m http.server "$PORT" --bind 127.0.0.1 > server.log 2>&1 &
echo $! > .server.pid; disown 2>/dev/null || true
echo "✓ 網頁伺服器啟動 (pid $(cat .server.pid))"

URL="http://127.0.0.1:${PORT}/index.html"
echo "✓ 網址 $URL"
if [ -z "${NO_OPEN:-}" ]; then
  sleep 1
  open "$URL" 2>/dev/null || echo "  請手動開啟：$URL"
fi

echo
echo "監控中。停止請執行：./stop.sh"
