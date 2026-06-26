#!/usr/bin/env python3
"""背景擷取：每 2 秒用 lsof 抓本機所有對外 TCP 連線，寫成 connections.json。"""
import subprocess, json, time, socket, os, ipaddress

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "connections.json")
socket.setdefaulttimeout(0.8)
dns_cache = {}

def rdns(ip):
    if ip in dns_cache:
        return dns_cache[ip]
    name = ""
    try:
        name = socket.gethostbyaddr(ip)[0]
    except Exception:
        name = ""
    dns_cache[ip] = name
    return name

def is_private(ip):
    try:
        a = ipaddress.ip_address(ip)
        return a.is_private or a.is_loopback or a.is_link_local or a.is_multicast
    except Exception:
        return False

def snapshot():
    # -F 機器可讀格式：每行首字母為欄位代號 (p=pid, c=command, n=name)
    try:
        out = subprocess.run(
            ["lsof", "-nP", "-Fpcn", "-iTCP", "-sTCP:ESTABLISHED"],
            capture_output=True, text=True, timeout=8
        ).stdout
    except Exception:
        out = ""
    seen, uniq = set(), []
    cmd, pid = "", ""
    for line in out.splitlines():
        if not line:
            continue
        tag, val = line[0], line[1:]
        if tag == "p":
            pid = val
        elif tag == "c":
            cmd = val
        elif tag == "n":
            name = val
            if "->" not in name:
                continue
            local, remote = name.split("->", 1)
            if ":" not in remote:
                continue
            rip, rport = remote.rsplit(":", 1)
            rip = rip.strip("[]")  # IPv6 包在 [] 內
            key = (cmd, rip, rport)
            if key in seen:
                continue
            seen.add(key)
            uniq.append({
                "cmd": cmd, "pid": pid, "user": "",
                "local": local, "rip": rip, "rport": rport,
                "priv": is_private(rip),
            })
    for c in uniq:
        c["host"] = "" if c["priv"] else rdns(c["rip"])
    uniq.sort(key=lambda c: (c["priv"], c["cmd"].lower(), c["rip"]))
    return uniq

def main():
    while True:
        try:
            data = {"ts": time.strftime("%Y-%m-%d %H:%M:%S"), "conns": snapshot()}
            tmp = OUT + ".tmp"
            with open(tmp, "w") as f:
                json.dump(data, f)
            os.replace(tmp, OUT)
        except Exception as e:
            with open(OUT, "w") as f:
                json.dump({"ts": time.strftime("%H:%M:%S"), "conns": [], "err": str(e)}, f)
        time.sleep(2)

if __name__ == "__main__":
    main()
