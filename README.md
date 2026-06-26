# network-monitor

一個**純本機**的網路可視性儀表板——單一頁面、頁內分頁切換，讓你監看自己這台機器，並對照「公司 / 管理方透過端點代理可能看得到什麼」。

> ⚠️ **只支援 macOS。** 依賴 `lsof` / `tcpdump` / `scutil` / `system_profiler` / `ifconfig` / `ipconfig` / `systemextensionsctl` / `profiles` 等 macOS 內建指令，**無法在 Linux / Windows 執行**。

## 系統需求
- **macOS**（Apple Silicon 或 Intel 皆可）
- **Python 3**（系統內建即可，無需安裝任何套件）
- DNS 分頁需要 **sudo**（`tcpdump` 要管理員權限）；其餘分頁免 sudo

---

## 安裝與啟動

```bash
git clone https://github.com/HsuenChan/network-monitor.git
cd network-monitor
chmod +x run.sh stop.sh        # 第一次才需要
./run.sh                       # 啟動並自動開瀏覽器
```

瀏覽器會打開 <http://127.0.0.1:8791/index.html>。停止：`./stop.sh`　｜　換埠號：`PORT=9000 ./run.sh`

DNS 分頁要另開一個終端機、以 sudo 啟動擷取器（在專案目錄下）：

```bash
sudo python3 my-monitor/dns_capture.py    # Ctrl+C 停止
```

---

## 四個分頁

| 分頁 | 看什麼 | 資料來源 | 權限 |
|---|---|---|---|
| 🏢 **公司能看到** | 本機偵測到的端點代理（EDR/防毒/MDM）+ 這類代理通常看得到/看不到什麼 | `systemextensionsctl` / `ps` / `/Applications` / `profiles` | 免 sudo |
| 🌐 **對外連線** | 哪個程式連到哪個 IP / 網域（TCP） | `lsof` | 免 sudo |
| 🔌 **監聽埠** | 哪個程式在聽哪個埠 | `lsof` | 免 sudo |
| 🔎 **DNS / 服務** | 你連的網域 → 歸類成服務 + 行為輪廓 | `tcpdump udp/53` | **需 sudo** |

「公司能看到」分頁是**動態偵測本機**——沒裝任何代理就顯示「未偵測到」，裝了什麼就列什麼。裝置身分（序號 / IP / MAC）也是即時讀本機，**不寫死、repo 內不含任何 PII**。

每個即時分頁都有：KPI 數字、**趨勢面積圖**（含流動動畫、可 hover 看時間與數量）、**分布長條圖**、明細表格。

---

## 為什麼需要 DNS 分頁？(Chrome / QUIC 盲區)

「對外連線」用 `lsof` 只看得到 **TCP**。Chrome 等瀏覽器大量走 **QUIC（HTTP/3 = UDP 443）**，其 UDP socket 在核心層為「未連接」狀態（`*:*`），**讀不到遠端 IP**。DNS 分頁從查詢層補上：不論 TCP/QUIC，連線前都會先查 DNS，所以看得到**網域名稱**並歸類成服務。

> 前提：DNS 為明文（udp/53）。若用 DoH 加密 DNS 則抓不到（可用 `my-monitor/dns_test.sh` 測試）。

---

## 運作原理

```
my-monitor/identity.py    ─(一次性)──> identity.json    （裝置身分）┐
my-monitor/agents.py      ─(一次性)──> agents.json      （端點代理）│
my-monitor/collect.py     ─(每2秒)───> connections.json （TCP 連線）├─ index.html 輪詢重繪
my-monitor/ports.py       ─(每3秒)───> ports.json       （監聽埠）  │
my-monitor/dns_capture.py ─(tcpdump)─> dns.json (需sudo) （DNS 查詢）┘
            python3 -m http.server 127.0.0.1:8791  ←  run.sh 啟動
```

伺服器綁 `127.0.0.1`，所有資料只存在本機 JSON（皆已被 `.gitignore` 排除），**不對外傳輸**。

---

## 檔案結構

```
network-monitor/
├── index.html              # 整合儀表板（唯一頁面，4 分頁）
├── favicon.svg
├── run.sh / stop.sh        # 一鍵啟動 / 停止
├── README.md · .gitignore
└── my-monitor/
    ├── identity.py         # 裝置身分（即時讀本機）
    ├── agents.py           # 端點代理偵測（EDR/防毒/MDM）
    ├── collect.py          # 對外連線 (lsof TCP)
    ├── ports.py            # 監聽埠 (lsof LISTEN/UDP)
    ├── dns_capture.py      # DNS 擷取 (sudo / tcpdump)
    ├── dns_test.sh         # 測 DNS 是否明文
    └── （執行後產生）*.json / *.log（皆已 gitignore）
```

---

## 常見問題

**只能在 macOS 跑嗎？** 是。指令與偵測邏輯都是 macOS 專屬。

**分頁小燈紅色 / 表格空白？** 對應背景腳本沒在跑。連線/埠 → `./run.sh`；DNS → sudo 啟動 `dns_capture.py`。

**8791 開不起來 / 404？** 埠被佔用，用 `PORT=其他埠 ./run.sh`。網址固定用 `127.0.0.1` 避免 IPv6 走到別的服務。

**會外傳資料嗎？** 不會。綁 `127.0.0.1`，資料只在本機。

---

## Social preview
GitHub 分享預覽圖在 `assets/social-preview.png`（1280×640）。需更新時改 `assets/social-preview.html` 再重新截圖：

```bash
"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" --headless=new --hide-scrollbars \
  --window-size=1280,640 --screenshot=assets/social-preview.png "file://$PWD/assets/social-preview.html"
```

> 圖片本身要到 GitHub repo **Settings → General → Social preview → Upload an image** 手動上傳（此設定無法用 API / git 設定）。

## 之後想擴充
- 連線 / DNS 的歷史與流量 bytes（改用 `nettop`）
- 目的地的國家 / ASN 標註
- 可疑目的地或非預期監聽埠告警
- Linux 版（改用 `ss` / `journalctl` 等對應指令）
