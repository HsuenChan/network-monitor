#!/usr/bin/env python3
"""一次性讀取本機裝置身分，寫成 identity.json（供「公司能看到」分頁即時填入）。
不含寫死資料；identity.json 已被 .gitignore 排除，不會進 repo。"""
import subprocess, json, os, socket, getpass, platform, re

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "identity.json")

def run(args):
    try:
        return subprocess.run(args, capture_output=True, text=True, timeout=10).stdout.strip()
    except Exception:
        return ""

def hostname():
    h = run(["scutil", "--get", "LocalHostName"])
    return (h + ".local") if h else socket.gethostname()

def model_and_serial():
    out = run(["system_profiler", "SPHardwareDataType"])
    model = re.search(r"Model Name:\s*(.+)", out)
    serial = re.search(r"Serial Number.*:\s*(\S+)", out)
    s = serial.group(1) if serial else run(["sh", "-c",
        "ioreg -rd1 -c IOPlatformExpertDevice | awk -F'\\\"' '/IOPlatformSerialNumber/{print $4}'"])
    return (model.group(1).strip() if model else "Mac"), (s or "—")

def primary_ip():
    for iface in ("en0", "en1"):
        ip = run(["ipconfig", "getifaddr", iface])
        if ip:
            return ip
    return "—"

def primary_mac():
    for iface in ("en0", "en1"):
        out = run(["ifconfig", iface])
        m = re.search(r"ether\s+([0-9a-f:]{17})", out)
        if m:
            return m.group(1)
    return "—"

def avast_uuid():
    p = "/Library/Application Support/com.gendigital.data/endpoint_uuid"
    try:
        with open(p) as f:
            return f.read().strip()
    except OSError:
        return ""

def main():
    model, serial = model_and_serial()
    data = {
        "ts": "",  # 由呼叫端不需要；保留欄位
        "hostname": hostname(),
        "user": getpass.getuser(),
        "model": model,
        "os": "macOS " + (platform.mac_ver()[0] or platform.release()),
        "serial": serial,
        "ip": primary_ip(),
        "mac": primary_mac(),
        "uuid": avast_uuid(),
    }
    tmp = OUT + ".tmp"
    with open(tmp, "w") as f:
        json.dump(data, f)
    os.replace(tmp, OUT)
    print("identity.json 已更新")

if __name__ == "__main__":
    main()
