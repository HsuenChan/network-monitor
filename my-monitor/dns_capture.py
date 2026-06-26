#!/usr/bin/env python3
"""以 sudo 執行：側錄 DNS 查詢 (udp/53)，彙整成 dns.json。
需要 sudo（tcpdump 要管理員權限）。
用法： sudo python3 dns_capture.py
"""
import subprocess, json, os, re, time

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "dns.json")
MAX = 300

# 比對查詢行：  ... .53: 1234+ A? example.com. (29)
QRE = re.compile(
    r'\.53:\s+\d+\S*\s+(A|AAAA|HTTPS|CNAME|MX|TXT|SRV|PTR|NS)\?\s+([A-Za-z0-9._-]+)'
)

domains = {}  # name -> {name,count,first,last,type,last_epoch}

def hhmmss():
    return time.strftime("%H:%M:%S")

def write():
    items = sorted(domains.values(), key=lambda d: d["last_epoch"], reverse=True)[:MAX]
    data = {
        "ts": time.strftime("%Y-%m-%d %H:%M:%S"),
        "total": sum(d["count"] for d in domains.values()),
        "domains": [{k: v for k, v in d.items() if k != "last_epoch"} for d in items],
    }
    tmp = OUT + ".tmp"
    with open(tmp, "w") as f:
        json.dump(data, f)
    os.replace(tmp, OUT)
    try:
        os.chmod(OUT, 0o644)  # 讓以一般使用者執行的網頁伺服器讀得到
    except OSError:
        pass

def main():
    write()  # 先寫空檔，讓網頁有東西可讀
    p = subprocess.Popen(
        ["tcpdump", "-i", "any", "-n", "-l", "udp port 53"],
        stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True, bufsize=1,
    )
    last_write = 0.0
    for line in p.stdout:
        m = QRE.search(line)
        if m:
            qtype, name = m.group(1), m.group(2).rstrip(".")
            if name and "." in name:
                e = time.time()
                d = domains.get(name)
                if d:
                    d["count"] += 1
                    d["last"] = hhmmss()
                    d["last_epoch"] = e
                    if qtype not in d["type"].split(","):
                        d["type"] += "," + qtype
                else:
                    domains[name] = {
                        "name": name, "count": 1, "first": hhmmss(),
                        "last": hhmmss(), "type": qtype, "last_epoch": e,
                    }
        t = time.time()
        if t - last_write >= 1.0:   # 節流：每秒最多寫一次
            write()
            last_write = t

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pass
