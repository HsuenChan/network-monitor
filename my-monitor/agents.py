#!/usr/bin/env python3
"""偵測本機安裝的端點安全 / 管理代理（EDR / 防毒 / MDM / 網路代理），輸出 agents.json。
唯讀、不需 sudo。供「公司能看到」分頁動態呈現——沒裝任何代理就顯示「未偵測到」。"""
import subprocess, json, os, re, glob, time

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "agents.json")

def run(args):
    try:
        return subprocess.run(args, capture_output=True, text=True, timeout=12).stdout
    except Exception:
        return ""

# (關鍵字 regex, 顯示名稱, 類別)
VENDORS = [
    (r"avast", "Avast", "防毒 / EPP"),
    (r"crowdstrike|falcon", "CrowdStrike Falcon", "EDR"),
    (r"sentinel", "SentinelOne", "EDR"),
    (r"carbonblack|carbon black|cbdaemon", "VMware Carbon Black", "EDR"),
    (r"cylance", "Cylance", "EDR"),
    (r"cortex|\btraps\b|paloalto|palo alto", "Palo Alto Cortex XDR", "EDR"),
    (r"tanium", "Tanium", "EDR / 管理"),
    (r"mdatp|wdav|microsoft defender|com\.microsoft\.dlp", "Microsoft Defender", "EDR / 防毒"),
    (r"sophos", "Sophos", "防毒 / EDR"),
    (r"\beset\b", "ESET", "防毒"),
    (r"mcafee|trellix", "McAfee / Trellix", "防毒 / EDR"),
    (r"trend ?micro|tmccsf|tmsm", "Trend Micro", "防毒 / EDR"),
    (r"symantec|\bsep\b|norton", "Symantec / Norton", "防毒 / EDR"),
    (r"malwarebytes", "Malwarebytes", "防毒"),
    (r"bitdefender", "Bitdefender", "防毒"),
    (r"kaspersky", "Kaspersky", "防毒"),
    (r"elastic-agent|elastic-endpoint", "Elastic Agent", "EDR / 監控"),
    (r"osquery", "osquery", "監控 / 查詢"),
    (r"\bwazuh\b", "Wazuh", "EDR / 監控"),
    (r"velociraptor", "Velociraptor", "EDR / 鑑識"),
    (r"\bsanta\b|northpolesec|com\.google\.santa", "Santa", "應用程式管控"),
    (r"huntress", "Huntress", "EDR"),
    (r"jamf", "Jamf", "MDM / 管理"),
    (r"kandji", "Kandji", "MDM / 管理"),
    (r"mosyle", "Mosyle", "MDM / 管理"),
    (r"addigy", "Addigy", "MDM / 管理"),
    (r"airwatch|workspace ?one|awcm", "VMware Workspace ONE", "MDM / 管理"),
    (r"intune|company portal", "Microsoft Intune", "MDM / 管理"),
    (r"ivanti", "Ivanti", "MDM / 管理"),
    (r"netskope", "Netskope", "網路 / SWG"),
    (r"zscaler", "Zscaler", "網路 / SWG"),
    (r"forcepoint", "Forcepoint", "網路 / DLP"),
    (r"nessus|tenable", "Tenable / Nessus", "弱點掃描"),
    (r"qualys", "Qualys", "弱點掃描"),
    (r"rapid7|\binsight\b", "Rapid7 Insight", "弱點 / EDR"),
    (r"datadog", "Datadog Agent", "監控"),
    (r"\bfleetd\b", "Fleet", "監控 / 管理"),
    (r"xagt|fireeye", "FireEye / Trellix", "EDR"),
]

def cat_sees(cat):
    if "MDM" in cat or "管理" in cat:
        return "裝置清單、設定/政策下發，可遠端鎖定 / 清除 / 安裝 App"
    if "EDR" in cat:
        return "程序與網路行為遙測、檔案掃描，事件回報雲端主控台"
    if "SWG" in cat or "網路" in cat or "DLP" in cat:
        return "攔截 / 檢視網路流量與外傳資料"
    if "弱點" in cat:
        return "掃描系統弱點與設定"
    if "監控" in cat:
        return "系統 / 查詢遙測並回報"
    if "管控" in cat:
        return "限制可執行的程式"
    return "檔案掃描、即時防護、裝置狀態回報"

def detect():
    sources = {
        "系統擴充": run(["systemextensionsctl", "list"]),
        "執行程序": run(["ps", "-axww", "-o", "command="]),
        "應用程式": "\n".join(glob.glob("/Applications/*")),
        "背景服務": "\n".join(glob.glob("/Library/LaunchDaemons/*") + glob.glob("/Library/LaunchAgents/*")),
    }
    try:
        sources["支援檔案"] = "\n".join(os.listdir("/Library/Application Support"))
    except OSError:
        pass
    found = {}
    for rx, name, cat in VENDORS:
        r = re.compile(rx, re.I)
        vias = [s for s, txt in sources.items() if r.search(txt or "")]
        if vias:
            found[name] = {"name": name, "cat": cat, "via": " / ".join(vias), "sees": cat_sees(cat)}
    return list(found.values())

def mdm_status():
    out = run(["profiles", "status", "-type", "enrollment"])
    if re.search(r"MDM enrollment:\s*Yes", out):
        return "已透過 MDM 受管" + ("（DEP 自動註冊）" if re.search(r"Enrolled via DEP:\s*Yes", out) else "")
    if re.search(r"MDM enrollment:\s*No", out):
        return "未受 MDM 控管"
    return "未知"

def main():
    data = {"ts": time.strftime("%Y-%m-%d %H:%M:%S"), "mdm": mdm_status(), "agents": detect()}
    tmp = OUT + ".tmp"
    with open(tmp, "w") as f:
        json.dump(data, f, ensure_ascii=False)
    os.replace(tmp, OUT)
    print(f"偵測到 {len(data['agents'])} 個代理；MDM：{data['mdm']}")

if __name__ == "__main__":
    main()
