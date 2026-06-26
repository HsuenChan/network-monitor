#!/usr/bin/env bash
# 測試：DNS 查詢是不是明文（能被 tcpdump 在 port 53 抓到）。
# 用法： sudo bash dns_test.sh
echo "側錄 DNS (udp/53) 8 秒，同時自動查 3 個網域…"
tcpdump -i any -n -c 12 'udp port 53' 2>/dev/null &
TPID=$!
sleep 1
for d in example.com wikipedia.org github.com; do
  nslookup "$d" >/dev/null 2>&1
done
sleep 2
kill "$TPID" 2>/dev/null
wait "$TPID" 2>/dev/null
echo "----- 結束 -----"
echo "有看到 'A? wikipedia.org' 之類 = DNS 明文（可做 DNS 監看）"
echo "完全空白          = DNS 被加密/攔截（要改用 QUIC 封包側錄）"
