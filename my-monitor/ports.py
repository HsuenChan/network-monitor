#!/usr/bin/env python3
"""背景擷取：每 3 秒用 lsof 抓本機監聽中的 TCP/UDP 埠，寫成 ports.json。"""
import subprocess, json, time, os

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "ports.json")

def parse(args):
    try:
        out = subprocess.run(args, capture_output=True, text=True, timeout=8).stdout
    except Exception:
        out = ""
    rows, cmd, pid = [], "", ""
    for line in out.splitlines():
        if not line:
            continue
        tag, val = line[0], line[1:]
        if tag == "p":
            pid = val
        elif tag == "c":
            cmd = val
        elif tag == "n":
            name = val.split("->", 1)[0]   # 連線型 UDP 取本地端
            if ":" not in name:
                continue
            addr, port = name.rsplit(":", 1)
            if not port.isdigit():
                continue
            rows.append({"cmd": cmd, "pid": pid, "addr": addr, "port": int(port)})
    return rows

def scope(addr):
    if addr in ("*",):
        return "全部介面"
    if addr in ("127.0.0.1", "[::1]", "::1", "localhost"):
        return "僅本機"
    return addr

def snapshot():
    tcp = [{**r, "proto": "TCP"} for r in
           parse(["lsof", "-nP", "-Fpcn", "-iTCP", "-sTCP:LISTEN"])]
    udp = [{**r, "proto": "UDP"} for r in
           parse(["lsof", "-nP", "-Fpcn", "-iUDP"])]
    seen, uniq = set(), []
    for r in tcp + udp:
        key = (r["proto"], r["port"], r["cmd"])
        if key in seen:
            continue
        seen.add(key)
        r["scope"] = scope(r["addr"])
        uniq.append(r)
    uniq.sort(key=lambda r: (r["proto"], r["port"]))
    return uniq

def main():
    while True:
        try:
            data = {"ts": time.strftime("%Y-%m-%d %H:%M:%S"), "ports": snapshot()}
            tmp = OUT + ".tmp"
            with open(tmp, "w") as f:
                json.dump(data, f)
            os.replace(tmp, OUT)
        except Exception as e:
            with open(OUT, "w") as f:
                json.dump({"ts": time.strftime("%H:%M:%S"), "ports": [], "err": str(e)}, f)
        time.sleep(3)

if __name__ == "__main__":
    main()
