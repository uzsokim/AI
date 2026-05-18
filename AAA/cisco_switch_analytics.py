#!/usr/bin/env python3
"""
Cisco IOS / IOS-XE Switch Performance Analytics
SSH-based collection -> HTML report with findings & recommendations.

Requirements:
    pip install netmiko
"""

import sys
import getpass
import re
import html as html_mod
from datetime import datetime

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

try:
    from netmiko import ConnectHandler, NetmikoTimeoutException, NetmikoAuthenticationException
except ImportError:
    print("ERROR: netmiko not installed.  Run:  pip install netmiko")
    sys.exit(1)

# ─────────────────────────────────────────────────────────────
# Target
# ─────────────────────────────────────────────────────────────
SWITCH_IP   = "10.63.65.24"
USERNAME    = "mark"
PASSWORD    = getpass.getpass(f"Password for {USERNAME}@{SWITCH_IP}: ")
OUTPUT_HTML = "Cisco_Switch_Analytics.html"

# ─────────────────────────────────────────────────────────────
# SSH Collection
# ─────────────────────────────────────────────────────────────

# Commands available from USER EXEC (privilege 1, prompt ">")
COMMANDS_USER = {
    "version"      : "show version",
    "interfaces"   : "show interfaces",
    "int_status"   : "show interfaces status",
    "stp_summary"  : "show spanning-tree summary",
    "stp_detail"   : "show spanning-tree detail",
    "mac_count"    : "show mac address-table count",
    "mac_aging"    : "show mac address-table aging-time",
    "inventory"    : "show inventory",
    "ip_brief"     : "show ip interface brief",
    "cdp_neighbors": "show cdp neighbors detail",
}

# Commands that require PRIVILEGED EXEC (privilege 15, prompt "#")
COMMANDS_PRIV = {
    "cpu_sorted"   : "show processes cpu sorted",
    "cpu_history"  : "show processes cpu history",
    "memory_sorted": "show processes memory sorted",
    "memory_stats" : "show memory statistics",
    "int_counters" : "show interfaces counters errors",
    "logging"      : "show logging | last 60",
    "environment"  : "show environment all",
}

# Error indicators returned when a command is not accessible
_PRIV_ERRORS = (
    "% invalid input",
    "% incomplete command",
    "% insufficient privileges",
    "% authorization failed",
    "% ambiguous command",
)


def _is_error(output: str) -> bool:
    """Return True if the command output is an IOS privilege/syntax error."""
    first = output.strip()[:120].lower()
    return any(e in first for e in _PRIV_ERRORS)


def collect(ip, username, password):
    device = {
        "device_type" : "cisco_ios",
        "host"        : ip,
        "username"    : username,
        "password"    : password,
        "timeout"     : 60,
        "fast_cli"    : False,
        # No 'secret' — never attempt enable (production, no pri 15)
    }
    raw = {}
    errors = []
    priv_level = 1  # assume user EXEC until confirmed

    print(f"\n[*] Connecting to {ip} via SSH...")
    try:
        with ConnectHandler(**device) as conn:
            prompt = conn.find_prompt()
            is_privileged = prompt.endswith("#")
            priv_level = 15 if is_privileged else 1
            print(f"[+] Connected — prompt: {prompt}  "
                  f"(privilege {'15 — full access' if is_privileged else '1 — user EXEC, limited commands'})")

            if not is_privileged:
                print("    [!] User EXEC mode: privileged commands will be skipped")

            # Always run user-level commands
            all_cmds = dict(COMMANDS_USER)
            if is_privileged:
                all_cmds.update(COMMANDS_PRIV)

            for key, cmd in all_cmds.items():
                print(f"    → {cmd}")
                try:
                    out = conn.send_command(cmd, read_timeout=30)
                    if _is_error(out):
                        print(f"      [!] Skipped (privilege error): {out.strip()[:80]}")
                        raw[key] = ""
                        errors.append(f"{cmd}: privilege denied")
                    else:
                        raw[key] = out
                except Exception as exc:
                    raw[key] = ""
                    errors.append(f"{cmd}: {exc}")
    except NetmikoAuthenticationException:
        print("[-] Authentication failed.")
        sys.exit(1)
    except NetmikoTimeoutException:
        print(f"[-] Connection timed out to {ip}")
        sys.exit(1)
    except Exception as e:
        print(f"[-] Connection error: {e}")
        sys.exit(1)

    if errors:
        print(f"\n[!] {len(errors)} command error(s):")
        for err in errors:
            print(f"    {err}")

    raw["_priv_level"] = priv_level
    return raw


# ─────────────────────────────────────────────────────────────
# Parsers
# ─────────────────────────────────────────────────────────────

def parse_version(txt):
    info = {}
    for pattern, key in [
        (r"Cisco IOS.*?Version\s+([\S]+)", "ios_version"),
        (r"hostname\s+(\S+)|^(\S+)\s+uptime", "hostname"),
        (r"uptime is (.+)", "uptime"),
        (r"cisco\s+(\S+)\s+.*?processor", "model"),
        (r"(\d+[KkMmGg]) bytes of physical memory", "dram"),
        (r"Processor board ID\s+(\S+)", "serial"),
        (r"System image file.*?\"(.+?)\"", "image"),
    ]:
        m = re.search(pattern, txt, re.IGNORECASE | re.MULTILINE)
        if m:
            info[key] = (m.group(1) or m.group(2) or "").strip()
    # hostname from prompt line
    if "hostname" not in info:
        m = re.search(r"^(\S+)\s+uptime", txt, re.MULTILINE)
        if m:
            info["hostname"] = m.group(1)
    return info


def parse_cpu(txt):
    result = {"five_sec": 0, "one_min": 0, "five_min": 0, "processes": []}
    m = re.search(r"CPU utilization.*?:\s*(\d+)%/\d+%.*?(\d+)%.*?(\d+)%", txt)
    if m:
        result["five_sec"] = int(m.group(1))
        result["one_min"]  = int(m.group(2))
        result["five_min"] = int(m.group(3))
    # top processes
    procs = re.findall(
        r"(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)%\s+(\d+)%\s+(\d+)%\s+\d+\s+(\S+.*?)$",
        txt, re.MULTILINE)
    for p in procs[:10]:
        result["processes"].append({
            "pid": p[0], "runtime": p[1],
            "five_sec": int(p[4]), "one_min": int(p[5]), "five_min": int(p[6]),
            "name": p[7].strip()
        })
    return result


def parse_memory(txt):
    result = {"processor": {}, "io": {}}
    # show processes memory sorted — first line summary
    m = re.search(r"Total:\s*(\d+),\s*Used:\s*(\d+),\s*Free:\s*(\d+)", txt)
    if m:
        total = int(m.group(1))
        used  = int(m.group(2))
        free  = int(m.group(3))
        result["processor"] = {
            "total": total, "used": used, "free": free,
            "pct": round(used / total * 100, 1) if total else 0
        }
    return result


def parse_interfaces(txt):
    ifaces = {}
    blocks = re.split(r"(?=^\S+\s+is\s+(?:up|down|administratively down))", txt, flags=re.MULTILINE)
    for block in blocks:
        m_name = re.match(r"^(\S+)\s+is\s+(up|down|administratively down),\s+line protocol is\s+(up|down)", block)
        if not m_name:
            continue
        name = m_name.group(1)
        link = m_name.group(2)
        proto = m_name.group(3)

        def _int(pattern, default=0):
            mx = re.search(pattern, block, re.IGNORECASE)
            return int(mx.group(1).replace(",", "")) if mx else default

        def _str(pattern, default=""):
            mx = re.search(pattern, block, re.IGNORECASE)
            return mx.group(1).strip() if mx else default

        ifaces[name] = {
            "link"         : link,
            "proto"        : proto,
            "description"  : _str(r"Description:\s*(.+)"),
            "duplex"       : _str(r"(\w+-duplex|Auto-duplex|Full-duplex|Half-duplex)"),
            "speed"        : _str(r"(\d+[MmGg]b/s|Auto-speed)"),
            "input_errors" : _int(r"(\d[\d,]*)\s+input errors"),
            "crc"          : _int(r"(\d[\d,]*)\s+CRC"),
            "output_errors": _int(r"(\d[\d,]*)\s+output errors"),
            "drops"        : _int(r"(\d[\d,]*)\s+output drops") + _int(r"(\d[\d,]*)\s+input drops"),
            "collisions"   : _int(r"(\d[\d,]*)\s+collisions"),
            "resets"       : _int(r"(\d[\d,]*)\s+interface resets"),
            "runts"        : _int(r"(\d[\d,]*)\s+runts"),
            "giants"       : _int(r"(\d[\d,]*)\s+giants"),
            "in_rate"      : _str(r"input rate\s+(\d+\s+\w+/sec)"),
            "out_rate"     : _str(r"output rate\s+(\d+\s+\w+/sec)"),
            "last_clear"   : _str(r"Last clearing.*?:\s*(.+)"),
        }
    return ifaces


def parse_stp_summary(txt):
    result = {"mode": "", "total_vlans": 0, "root_vlans": 0, "bpdu_guard": False,
              "portfast_default": False, "loop_guard": False}
    m = re.search(r"Switch is in\s+(\S+)\s+mode", txt, re.IGNORECASE)
    if m:
        result["mode"] = m.group(1)
    m = re.search(r"(\d+)\s+vlans?", txt, re.IGNORECASE)
    if m:
        result["total_vlans"] = int(m.group(1))
    result["bpdu_guard"]       = bool(re.search(r"bpdu guard\s+enabled", txt, re.IGNORECASE))
    result["portfast_default"] = bool(re.search(r"portfast\s+default", txt, re.IGNORECASE))
    result["loop_guard"]       = bool(re.search(r"loop guard\s+enabled", txt, re.IGNORECASE))
    # TCN count
    tcn_count = len(re.findall(r"topology change", txt, re.IGNORECASE))
    result["tcn_events"] = tcn_count
    return result


def parse_mac_count(txt):
    result = {"total": 0, "dynamic": 0, "static": 0, "max": 0}
    m = re.search(r"Total Mac Addresses.*?:\s*(\d+)", txt, re.IGNORECASE)
    if m:
        result["total"] = int(m.group(1))
    m = re.search(r"Dynamic Address Count.*?:\s*(\d+)", txt, re.IGNORECASE)
    if m:
        result["dynamic"] = int(m.group(1))
    m = re.search(r"Static Address.*?:\s*(\d+)", txt, re.IGNORECASE)
    if m:
        result["static"] = int(m.group(1))
    m = re.search(r"Maximum MAC Addresses.*?:\s*(\d+)", txt, re.IGNORECASE)
    if m:
        result["max"] = int(m.group(1))
    return result


def parse_log_issues(txt):
    issues = []
    patterns = [
        (r"(%LINEPROTO-\d-UPDOWN.+)",         "Interface flap"),
        (r"(%LINK-\d-CHANGED.+)",              "Link state change"),
        (r"(%SPANTREE.+)",                     "Spanning Tree event"),
        (r"(%SYS-\d-CPUHOG.+)",               "CPU HOG"),
        (r"(%PLATFORM.+ERR.+)",               "Platform error"),
        (r"(%SW_MATM.+)",                      "MAC table issue"),
        (r"(%STORM_CONTROL.+)",               "Storm control"),
        (r"(%DOT1X.+)",                        "802.1X event"),
        (r"(%ETHCNTR.+)",                      "Ethernet counter"),
        (r"(duplex mismatch.+)",              "Duplex mismatch"),
    ]
    for line in txt.splitlines():
        for pattern, label in patterns:
            if re.search(pattern, line, re.IGNORECASE):
                issues.append({"label": label, "line": line.strip()})
                break
    return issues[-40:]  # last 40 relevant log lines


# ─────────────────────────────────────────────────────────────
# Analysis Engine
# ─────────────────────────────────────────────────────────────

def finding(sev, area, title, detail, recommendation):
    return {"sev": sev, "area": area, "title": title,
            "detail": detail, "rec": recommendation}


def analyze(parsed):
    findings = []
    cpu   = parsed["cpu"]
    mem   = parsed["memory"]
    ifaces = parsed["interfaces"]
    stp   = parsed["stp"]
    mac   = parsed["mac"]
    logs  = parsed["log_issues"]

    # ── CPU ──────────────────────────────────────────────────
    if cpu["five_min"] >= 90:
        findings.append(finding("critical", "CPU",
            f"CPU utilization critical: {cpu['five_min']}% (5-min avg)",
            "Sustained CPU above 90% causes packet drops, slow CLI, "
            "and protocol timeouts (OSPF, HSRP, STP).",
            "Identify top process (see table below). Common causes: "
            "broadcast storm, routing protocol instability, ACL on high-traffic ports, "
            "SNMP polling too frequent. Consider 'ip cef' verification and CoPP policy."))
    elif cpu["five_min"] >= 70:
        findings.append(finding("high", "CPU",
            f"CPU utilization high: {cpu['five_min']}% (5-min avg)",
            "CPU above 70% for extended periods risks protocol adjacency drops.",
            "Profile top processes. Check for STP TCN storms, excessive ARP/broadcast, "
            "or misconfigured SNMP community strings causing heavy polling."))
    elif cpu["five_min"] >= 50:
        findings.append(finding("warning", "CPU",
            f"CPU utilization elevated: {cpu['five_min']}% (5-min avg)",
            "Normal IOS switch baseline is typically <20%. Investigate if sustained.",
            "Run 'show processes cpu history' to confirm trend, then profile top processes."))

    # ── Memory ───────────────────────────────────────────────
    pct = mem.get("processor", {}).get("pct", 0)
    if pct >= 85:
        findings.append(finding("critical", "Memory",
            f"Processor memory critical: {pct}% used",
            "Memory above 85% risks IOS crashes, process restarts, and unpredictable behavior.",
            "Check for memory leaks: 'show processes memory sorted'. "
            "Common culprits: BGP full table, large ACL, netflow cache. "
            "Consider upgrading DRAM or reducing feature load."))
    elif pct >= 70:
        findings.append(finding("high", "Memory",
            f"Processor memory high: {pct}% used",
            "Approaching critical threshold. Monitor trend.",
            "Identify top memory consumers. Review routing table size and ACL complexity."))

    # ── Interfaces ───────────────────────────────────────────
    half_duplex_up = []
    high_error_ifaces = []
    flapping_ifaces = []

    for name, iface in ifaces.items():
        # Half duplex on active links
        if (iface["link"] == "up" and iface["proto"] == "up"
                and "half" in iface["duplex"].lower()):
            half_duplex_up.append(name)

        # High error rate
        total_err = iface["input_errors"] + iface["crc"] + iface["output_errors"]
        if total_err > 1000:
            high_error_ifaces.append((name, total_err,
                iface["crc"], iface["input_errors"], iface["output_errors"],
                iface["drops"], iface["runts"], iface["giants"]))

        # Resets suggest instability
        if iface["resets"] > 10:
            flapping_ifaces.append((name, iface["resets"]))

    if half_duplex_up:
        findings.append(finding("high", "Interfaces",
            f"Half-duplex detected on {len(half_duplex_up)} active port(s): "
            f"{', '.join(half_duplex_up[:5])}",
            "Half-duplex on modern infrastructure causes collisions, retransmits, "
            "and dramatically reduces effective throughput (sometimes below 20% of nominal).",
            "Set explicit 'duplex full' and matching 'speed' on both ends. "
            "Never use 'auto' on uplinks/trunks. Verify NIC settings on connected devices."))

    if high_error_ifaces:
        top = sorted(high_error_ifaces, key=lambda x: x[1], reverse=True)[:5]
        detail_lines = "; ".join(
            f"{n}: {e} total errors (CRC:{c})" for n, e, c, *_ in top)
        findings.append(finding("high", "Interfaces",
            f"{len(high_error_ifaces)} port(s) with >1000 errors",
            f"High error counts indicate layer 1 or duplex problems: {detail_lines}",
            "Check cabling (replace patch cable), SFP module health, "
            "duplex/speed mismatch. Use 'show interfaces <name> counters errors' "
            "and clear counters after fixes to verify improvement."))

    if flapping_ifaces:
        top_f = sorted(flapping_ifaces, key=lambda x: x[1], reverse=True)[:5]
        findings.append(finding("warning", "Interfaces",
            f"{len(flapping_ifaces)} port(s) with repeated interface resets",
            "Interface resets: " + ", ".join(f"{n}({r})" for n, r in top_f),
            "Check for negotiation issues, ErrDisable recovery loops, "
            "or attached device reboots. Enable 'errdisable recovery cause all' "
            "and review 'show errdisable recovery'."))

    # Count down ports that are up/up vs admin-down
    up_ports = sum(1 for i in ifaces.values()
                   if i["link"] == "up" and i["proto"] == "up")
    admin_down = sum(1 for i in ifaces.values()
                     if "administratively" in i["link"])
    if admin_down > 0:
        findings.append(finding("info", "Interfaces",
            f"{admin_down} port(s) administratively shut down",
            "Ensure these are intentionally disabled. Unused ports should be "
            "shut and placed in an unused VLAN as best practice.",
            "Verify with: 'show interfaces status | include disabled'. "
            "Place unused ports in a dedicated black-hole VLAN (e.g. VLAN 999) "
            "and apply 'shutdown'."))

    # ── Spanning Tree ─────────────────────────────────────────
    if stp["tcn_events"] > 5:
        findings.append(finding("high", "Spanning Tree",
            f"High TCN (Topology Change Notification) activity: {stp['tcn_events']} events in logs",
            "Excessive TCNs flush the MAC table causing temporary flooding on ALL ports, "
            "dramatically increasing CPU and broadcast traffic. Common cause: "
            "access port connected to a hub/IP phone cycling.",
            "Enable 'spanning-tree portfast' on all access ports and "
            "'spanning-tree bpduguard enable' to prevent non-switch devices "
            "from triggering TCNs. Check 'show spanning-tree detail | inc exec|occur'."))

    if not stp["bpdu_guard"]:
        findings.append(finding("high", "Spanning Tree",
            "BPDU Guard not enabled globally",
            "Without BPDU Guard on PortFast ports, a rogue switch or misconfigured device "
            "can trigger STP topology changes and potentially become root bridge.",
            "Apply globally: 'spanning-tree portfast bpduguard default'. "
            "This shuts the port immediately if a BPDU is received on a PortFast port."))

    if not stp["portfast_default"]:
        findings.append(finding("warning", "Spanning Tree",
            "PortFast not enabled as global default for access ports",
            "Without PortFast, access ports wait 30 seconds (listening+learning) "
            "before forwarding. This causes endpoint connection delays and "
            "can trigger DHCP timeouts.",
            "Enable: 'spanning-tree portfast default' (applies to non-trunk ports). "
            "Combine with BPDU Guard to maintain security."))

    if not stp["loop_guard"]:
        findings.append(finding("info", "Spanning Tree",
            "Loop Guard not enabled",
            "Loop Guard protects against unidirectional link failures "
            "that could cause a blocked port to incorrectly transition to forwarding.",
            "Enable: 'spanning-tree loopguard default'. "
            "Particularly important on uplinks and trunk ports."))

    # ── MAC Table ─────────────────────────────────────────────
    if mac["max"] > 0:
        fill_pct = round(mac["total"] / mac["max"] * 100, 1)
        if fill_pct >= 80:
            findings.append(finding("critical", "MAC Table",
                f"CAM table {fill_pct}% full ({mac['total']}/{mac['max']} entries)",
                "When the CAM table is full, the switch floods all unknown unicast traffic "
                "on all ports — effectively operating as a hub. This saturates links and "
                "is also exploitable (MAC flooding attack).",
                "Investigate source of MAC addresses (rogue hubs, VMs with many MACs). "
                "Enable 'port-security' or 'ip dhcp snooping' to limit per-port MACs. "
                "Consider dynamic ARP inspection (DAI) to harden against spoofing."))
        elif fill_pct >= 60:
            findings.append(finding("warning", "MAC Table",
                f"CAM table {fill_pct}% full ({mac['total']}/{mac['max']} entries)",
                "Approaching CAM table capacity. Monitor trend.",
                "Review unusually high MAC counts per port with: "
                "'show mac address-table count interface <x>'. "
                "Implement port-security with maximum MAC limit per port."))

    # ── Syslog events ─────────────────────────────────────────
    storm_events = [l for l in logs if "Storm control" in l["label"]]
    if storm_events:
        findings.append(finding("high", "Traffic",
            f"Storm control triggered ({len(storm_events)} events in recent logs)",
            "Storm control activations indicate broadcast/multicast/unicast storms "
            "that the switch had to suppress.",
            "Identify the source port from log messages. Check for "
            "misconfigured network loops, failing NIC, or broadcast-heavy applications. "
            "Tune storm-control thresholds per port type."))

    cpu_hog = [l for l in logs if "CPU HOG" in l["label"]]
    if cpu_hog:
        findings.append(finding("high", "CPU",
            f"CPU HOG events detected in syslog ({len(cpu_hog)} occurrences)",
            "CPUHOG messages indicate a process held the CPU for too long, "
            "blocking other processes and potentially dropping packets.",
            "Note the process name in the log. Common causes: "
            "large routing table recalculation, misconfigured SNMP, "
            "EEM script loop, or software bug (check for IOS updates)."))

    return findings


# ─────────────────────────────────────────────────────────────
# Score
# ─────────────────────────────────────────────────────────────

def score_calc(findings):
    c = {"critical": 0, "high": 0, "warning": 0, "info": 0}
    for f in findings:
        c[f["sev"]] = c.get(f["sev"], 0) + 1
    s = max(0, 100 - c["critical"]*20 - c["high"]*10
                    - c["warning"]*4 - c["info"]*1)
    color = "#16a34a" if s >= 80 else "#d97706" if s >= 60 else "#dc2626"
    label = ("Healthy" if s >= 80
             else "Needs Attention" if s >= 60
             else "Critical — Immediate Action Required")
    return s, color, label, c


# ─────────────────────────────────────────────────────────────
# HTML
# ─────────────────────────────────────────────────────────────

SEV_STYLE = {
    "critical": ("#dc2626", "CRITICAL"),
    "high"    : ("#ea580c", "HIGH"),
    "warning" : ("#d97706", "WARNING"),
    "info"    : ("#2563eb", "INFO"),
}
SEV_ORDER = {"critical": 0, "high": 1, "warning": 2, "info": 3}


def e(v, fb="—"):
    return html_mod.escape(str(v) if v is not None else fb)


def badge(sev):
    color, label = SEV_STYLE.get(sev, ("#6b7280", sev.upper()))
    return (f'<span style="display:inline-block;padding:2px 10px;border-radius:999px;'
            f'font-size:.68rem;font-weight:700;color:#fff;background:{color}">{label}</span>')


def cpu_bar(pct):
    color = "#dc2626" if pct >= 80 else "#d97706" if pct >= 50 else "#16a34a"
    return (f'<div style="background:#1e293b;border-radius:4px;height:10px;width:200px;'
            f'display:inline-block;vertical-align:middle">'
            f'<div style="width:{min(pct,100)}%;height:100%;background:{color};'
            f'border-radius:4px"></div></div> '
            f'<span style="font-size:.82rem;color:{color}">{pct}%</span>')


def mem_bar(pct):
    color = "#dc2626" if pct >= 85 else "#d97706" if pct >= 70 else "#38bdf8"
    return (f'<div style="background:#1e293b;border-radius:4px;height:10px;width:200px;'
            f'display:inline-block;vertical-align:middle">'
            f'<div style="width:{min(pct,100)}%;height:100%;background:{color};'
            f'border-radius:4px"></div></div> '
            f'<span style="font-size:.82rem;color:{color}">{pct}%</span>')


def generate_html(raw, parsed, findings, switch_info):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    score, score_color, score_label, cnt = score_calc(findings)
    total_f = len(findings)
    sorted_f = sorted(findings, key=lambda x: SEV_ORDER.get(x["sev"], 9))

    hostname  = switch_info.get("hostname", SWITCH_IP)
    model     = switch_info.get("model", "Unknown")
    version   = switch_info.get("ios_version", "Unknown")
    uptime    = switch_info.get("uptime", "Unknown")
    serial    = switch_info.get("serial", "Unknown")
    priv_lvl  = raw.get("_priv_level", 1)

    cpu    = parsed["cpu"]
    mem    = parsed["memory"]
    ifaces = parsed["interfaces"]
    stp    = parsed["stp"]
    mac    = parsed["mac"]
    logs   = parsed["log_issues"]

    # Warning banner when running as user EXEC
    priv_banner = ""
    if priv_lvl < 15:
        missing = ", ".join(COMMANDS_PRIV.values())
        priv_banner = (
            '<div style="background:#78350f;border:1px solid #92400e;border-radius:10px;'
            'padding:14px 20px;margin-bottom:20px;font-size:.84rem;color:#fef3c7">'
            '<strong>&#9888; Limited Data — User EXEC Mode (privilege 1)</strong><br>'
            'The following privileged commands were NOT available and are shown as empty: '
            f'<span style="font-family:monospace">{e(missing)}</span>.<br>'
            'CPU process details, memory breakdown, and syslog events require privilege 15. '
            'Contact the switch administrator to assign read-only privilege 15 or a '
            'custom privilege level that allows these <code>show</code> commands.'
            '</div>'
        )

    # ── Finding cards ─────────────────────────────────────────
    cards = ""
    for i, f in enumerate(sorted_f, 1):
        sev = f["sev"]
        color = SEV_STYLE.get(sev, ("#6b7280", ""))[0]
        cards += f"""
<div class="fcard {sev}" data-sev="{sev}">
  <div class="fhead">{badge(sev)} <span class="fnum">#{i}</span>
    <span class="ftitle">{e(f['title'])}</span>
  </div>
  <div class="fbody">
    <p><strong>Area:</strong> {e(f['area'])}</p>
    <p><strong>Detail:</strong> {e(f['detail'])}</p>
    <p class="rec"><strong>Recommendation:</strong> {e(f['rec'])}</p>
  </div>
</div>"""

    # ── CPU process table ─────────────────────────────────────
    cpu_rows = ""
    for p in cpu["processes"]:
        clr = "#dc2626" if p["five_min"] >= 30 else "#d97706" if p["five_min"] >= 10 else "#94a3b8"
        cpu_rows += (f"<tr><td>{e(p['pid'])}</td><td>{e(p['name'])}</td>"
                     f"<td style='color:{clr}'>{p['five_sec']}%</td>"
                     f"<td style='color:{clr}'>{p['one_min']}%</td>"
                     f"<td style='color:{clr}'>{p['five_min']}%</td></tr>")
    if not cpu_rows:
        cpu_rows = '<tr><td colspan="5" class="muted">No process data</td></tr>'

    # ── Interface table ───────────────────────────────────────
    iface_rows = ""
    sorted_ifaces = sorted(ifaces.items(),
        key=lambda kv: kv[1]["input_errors"] + kv[1]["crc"] + kv[1]["output_errors"],
        reverse=True)
    for name, iface in sorted_ifaces[:40]:
        link_color = "#4ade80" if iface["link"] == "up" else "#f87171"
        duplex_color = "#f87171" if "half" in iface["duplex"].lower() else "#94a3b8"
        err_total = iface["input_errors"] + iface["crc"] + iface["output_errors"]
        err_color = "#dc2626" if err_total > 10000 else "#d97706" if err_total > 1000 else "#94a3b8"
        iface_rows += (
            f"<tr>"
            f"<td>{e(name)}</td>"
            f"<td><span style='color:{link_color}'>{e(iface['link'])}</span></td>"
            f"<td>{e(iface['description'][:30] if iface['description'] else '—')}</td>"
            f"<td><span style='color:{duplex_color}'>{e(iface['duplex']) or '—'}</span></td>"
            f"<td>{e(iface['speed']) or '—'}</td>"
            f"<td style='color:{err_color}'>{iface['input_errors']:,}</td>"
            f"<td style='color:{err_color}'>{iface['crc']:,}</td>"
            f"<td style='color:{err_color}'>{iface['output_errors']:,}</td>"
            f"<td>{iface['drops']:,}</td>"
            f"<td>{iface['resets']:,}</td>"
            f"<td>{e(iface['in_rate']) or '—'}</td>"
            f"</tr>")
    if not iface_rows:
        iface_rows = '<tr><td colspan="11" class="muted">No interface data</td></tr>'

    # ── Log table ─────────────────────────────────────────────
    log_rows = ""
    for l in logs[-20:]:
        log_rows += f"<tr><td>{e(l['label'])}</td><td class='mono'>{e(l['line'][:120])}</td></tr>"
    if not log_rows:
        log_rows = '<tr><td colspan="2" class="muted">No relevant log events</td></tr>'

    # ── Memory ───────────────────────────────────────────────
    pmem = mem.get("processor", {})
    mem_total_mb = round(pmem.get("total", 0) / 1024 / 1024, 1)
    mem_used_mb  = round(pmem.get("used",  0) / 1024 / 1024, 1)
    mem_free_mb  = round(pmem.get("free",  0) / 1024 / 1024, 1)
    mem_pct      = pmem.get("pct", 0)

    # ── CAM fill % ───────────────────────────────────────────
    cam_fill = round(mac["total"] / mac["max"] * 100, 1) if mac["max"] else 0
    cam_color = "#dc2626" if cam_fill >= 80 else "#d97706" if cam_fill >= 60 else "#4ade80"

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>Switch Analytics — {e(hostname)}</title>
<style>
:root{{--bg:#0f172a;--card:#1e293b;--border:#334155;--text:#e2e8f0;--muted:#94a3b8;--accent:#38bdf8}}
*{{box-sizing:border-box;margin:0;padding:0}}
body{{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;background:var(--bg);color:var(--text);padding:28px;line-height:1.5}}
h1{{font-size:1.75rem;font-weight:800;color:#f1f5f9}}
h2{{font-size:1.1rem;font-weight:700;color:#cbd5e1;margin:32px 0 14px;padding-bottom:6px;border-bottom:1px solid var(--border)}}
.header{{display:flex;align-items:center;justify-content:space-between;padding:24px 28px;background:var(--card);border:1px solid var(--border);border-radius:14px;margin-bottom:26px}}
.header-meta{{font-size:.78rem;color:var(--muted);margin-top:4px}}
.score-row{{display:flex;align-items:center;gap:24px;background:var(--card);border:1px solid var(--border);border-radius:14px;padding:22px 28px;margin-bottom:26px}}
.score-num{{font-size:4rem;font-weight:900;line-height:1}}
.stats{{display:grid;grid-template-columns:repeat(auto-fit,minmax(130px,1fr));gap:14px;margin-bottom:26px}}
.stat{{background:var(--card);border:1px solid var(--border);border-radius:12px;padding:16px;text-align:center}}
.stat-n{{font-size:2.2rem;font-weight:800;line-height:1}}
.stat-l{{font-size:.72rem;color:var(--muted);margin-top:4px;text-transform:uppercase;letter-spacing:.05em}}
.grid2{{display:grid;grid-template-columns:1fr 1fr;gap:18px;margin-bottom:26px}}
.card{{background:var(--card);border:1px solid var(--border);border-radius:12px;padding:20px 22px}}
.card h3{{font-size:.88rem;font-weight:700;color:#94a3b8;text-transform:uppercase;letter-spacing:.06em;margin-bottom:14px}}
.metric{{display:flex;justify-content:space-between;align-items:center;padding:7px 0;border-bottom:1px solid #1e3040;font-size:.84rem}}
.metric:last-child{{border-bottom:none}}
.metric label{{color:var(--muted)}}
.filter-bar{{display:flex;gap:8px;margin-bottom:14px;flex-wrap:wrap}}
.fb{{padding:5px 16px;border:1px solid var(--border);border-radius:999px;background:var(--card);color:var(--muted);cursor:pointer;font-size:.78rem}}
.fb.active,.fb:hover{{background:#334155;color:#f1f5f9}}
.fcard{{background:var(--card);border-left:4px solid #334155;border-radius:10px;padding:16px 18px;margin-bottom:10px}}
.fcard.critical{{border-left-color:#dc2626}}
.fcard.high{{border-left-color:#ea580c}}
.fcard.warning{{border-left-color:#d97706}}
.fcard.info{{border-left-color:#2563eb}}
.fhead{{display:flex;align-items:center;gap:6px;margin-bottom:10px;flex-wrap:wrap}}
.fnum{{font-size:.72rem;color:var(--muted)}}
.ftitle{{font-weight:700;font-size:.92rem;color:#f1f5f9}}
.fbody p{{font-size:.82rem;color:var(--muted);margin-bottom:5px}}
.fbody strong{{color:#e2e8f0}}
.rec{{color:#86efac!important}}
.tw{{background:var(--card);border:1px solid var(--border);border-radius:12px;overflow:auto;margin-bottom:26px}}
table{{width:100%;border-collapse:collapse;font-size:.8rem}}
th,td{{padding:9px 12px;text-align:left;border-bottom:1px solid var(--border);white-space:nowrap}}
th{{background:#162032;color:var(--muted);font-weight:700;font-size:.7rem;text-transform:uppercase;letter-spacing:.05em}}
tr:last-child td{{border-bottom:none}}
tr:hover td{{background:rgba(255,255,255,.025)}}
.muted{{color:var(--muted)!important;font-style:italic}}
.mono{{font-family:monospace;font-size:.75rem;word-break:break-all;white-space:normal}}
footer{{text-align:center;color:var(--muted);font-size:.72rem;margin-top:44px;padding-top:18px;border-top:1px solid var(--border)}}
@media(max-width:768px){{.grid2{{grid-template-columns:1fr}}}}
</style>
</head>
<body>

<div class="header">
  <div>
    <h1>Cisco Switch Performance Analytics</h1>
    <div class="header-meta">
      {e(hostname)} &nbsp;|&nbsp; {e(SWITCH_IP)} &nbsp;|&nbsp;
      Model: {e(model)} &nbsp;|&nbsp; IOS: {e(version)}<br>
      Uptime: {e(uptime)} &nbsp;|&nbsp; Serial: {e(serial)} &nbsp;|&nbsp;
      Generated: {ts}
    </div>
  </div>
  <div style="font-size:2.4rem">🔀</div>
</div>

{priv_banner}
<div class="score-row">
  <div class="score-num" style="color:{score_color}">{score}</div>
  <div>
    <div style="font-size:1.15rem;font-weight:700;color:#f1f5f9">Switch Health Score <span style="font-size:.85rem;color:var(--muted)">/100</span></div>
    <div style="color:{score_color};font-weight:600;margin-top:3px">{score_label}</div>
    <div style="font-size:.82rem;color:var(--muted);margin-top:4px">
      {cnt['critical']} Critical &nbsp;·&nbsp; {cnt['high']} High &nbsp;·&nbsp;
      {cnt['warning']} Warning &nbsp;·&nbsp; {cnt['info']} Info
    </div>
    <div style="font-size:.72rem;color:#475569;margin-top:6px">Score = 100 − critical×20 − high×10 − warning×4 − info×1</div>
  </div>
</div>

<div class="stats">
  <div class="stat"><div class="stat-n" style="color:#dc2626">{cnt['critical']}</div><div class="stat-l">Critical</div></div>
  <div class="stat"><div class="stat-n" style="color:#ea580c">{cnt['high']}</div><div class="stat-l">High</div></div>
  <div class="stat"><div class="stat-n" style="color:#d97706">{cnt['warning']}</div><div class="stat-l">Warning</div></div>
  <div class="stat"><div class="stat-n" style="color:#2563eb">{cnt['info']}</div><div class="stat-l">Info</div></div>
  <div class="stat"><div class="stat-n" style="color:#38bdf8">{cpu['five_min']}%</div><div class="stat-l">CPU 5min</div></div>
  <div class="stat"><div class="stat-n" style="color:#94a3b8">{mem_pct}%</div><div class="stat-l">Mem used</div></div>
  <div class="stat"><div class="stat-n" style="color:#94a3b8">{sum(1 for i in ifaces.values() if i['link']=='up' and i['proto']=='up')}</div><div class="stat-l">Ports Up</div></div>
  <div class="stat"><div class="stat-n" style="color:{cam_color}">{cam_fill}%</div><div class="stat-l">CAM Table</div></div>
</div>

<div class="grid2">
  <div class="card">
    <h3>CPU Utilization</h3>
    <div class="metric"><label>5 seconds</label>{cpu_bar(cpu['five_sec'])}</div>
    <div class="metric"><label>1 minute</label>{cpu_bar(cpu['one_min'])}</div>
    <div class="metric"><label>5 minutes</label>{cpu_bar(cpu['five_min'])}</div>
  </div>
  <div class="card">
    <h3>Memory</h3>
    <div class="metric"><label>Used</label>{mem_bar(mem_pct)}</div>
    <div class="metric"><label>Total</label><span>{mem_total_mb} MB</span></div>
    <div class="metric"><label>Used</label><span>{mem_used_mb} MB</span></div>
    <div class="metric"><label>Free</label><span>{mem_free_mb} MB</span></div>
  </div>
  <div class="card">
    <h3>Spanning Tree</h3>
    <div class="metric"><label>Mode</label><span>{e(stp['mode']) or '—'}</span></div>
    <div class="metric"><label>Active VLANs</label><span>{stp['total_vlans']}</span></div>
    <div class="metric"><label>BPDU Guard</label>
      <span style="color:{'#4ade80' if stp['bpdu_guard'] else '#f87171'}">
        {'Enabled' if stp['bpdu_guard'] else 'DISABLED'}</span></div>
    <div class="metric"><label>PortFast Default</label>
      <span style="color:{'#4ade80' if stp['portfast_default'] else '#f87171'}">
        {'Enabled' if stp['portfast_default'] else 'DISABLED'}</span></div>
    <div class="metric"><label>Loop Guard</label>
      <span style="color:{'#4ade80' if stp['loop_guard'] else '#d97706'}">
        {'Enabled' if stp['loop_guard'] else 'Disabled'}</span></div>
    <div class="metric"><label>TCN Events (log)</label>
      <span style="color:{'#dc2626' if stp['tcn_events']>5 else '#94a3b8'}">
        {stp['tcn_events']}</span></div>
  </div>
  <div class="card">
    <h3>CAM / MAC Table</h3>
    <div class="metric"><label>Total MACs</label><span>{mac['total']:,}</span></div>
    <div class="metric"><label>Dynamic</label><span>{mac['dynamic']:,}</span></div>
    <div class="metric"><label>Static</label><span>{mac['static']:,}</span></div>
    <div class="metric"><label>Max Capacity</label><span>{mac['max']:,}</span></div>
    <div class="metric"><label>Fill %</label>
      <span style="color:{cam_color}">{cam_fill}%</span></div>
  </div>
</div>

<h2>Top CPU Processes</h2>
<div class="tw">
<table>
  <thead><tr><th>PID</th><th>Process Name</th><th>CPU 5s</th><th>CPU 1m</th><th>CPU 5m</th></tr></thead>
  <tbody>{cpu_rows}</tbody>
</table>
</div>

<h2>Interfaces (sorted by error count, top 40)</h2>
<div class="tw">
<table>
  <thead><tr>
    <th>Interface</th><th>Status</th><th>Description</th><th>Duplex</th><th>Speed</th>
    <th>Input Err</th><th>CRC</th><th>Output Err</th><th>Drops</th><th>Resets</th><th>In Rate</th>
  </tr></thead>
  <tbody>{iface_rows}</tbody>
</table>
</div>

<h2>Recent Syslog Events ({len(logs)} relevant entries)</h2>
<div class="tw">
<table>
  <thead><tr><th>Category</th><th>Log Line</th></tr></thead>
  <tbody>{log_rows}</tbody>
</table>
</div>

<h2>Findings &amp; Recommendations ({total_f} total)</h2>
<div class="filter-bar">
  <button class="fb fa active" onclick="filt('all')">All ({total_f})</button>
  <button class="fb fc" onclick="filt('critical')">Critical ({cnt['critical']})</button>
  <button class="fb fh" onclick="filt('high')">High ({cnt['high']})</button>
  <button class="fb fw" onclick="filt('warning')">Warning ({cnt['warning']})</button>
  <button class="fb fi" onclick="filt('info')">Info ({cnt['info']})</button>
</div>
<div id="fc">
{cards if cards else '<p class="muted">No findings — switch is healthy.</p>'}
</div>

<h2>Remediation Priority Checklist</h2>
<div style="background:var(--card);border:1px solid var(--border);border-radius:12px;padding:20px 24px;margin-bottom:26px">
<ol style="font-size:.85rem;color:var(--muted);padding-left:20px;line-height:2.2">
  <li><strong style="color:#dc2626">Critical first:</strong> Resolve CAM table overflow and CPU &gt;90% before any other work.</li>
  <li><strong style="color:#ea580c">Half-duplex:</strong> Set explicit <code>duplex full</code> + <code>speed</code> on ALL uplinks — never leave auto/auto on trunks.</li>
  <li><strong style="color:#ea580c">BPDU Guard:</strong> <code>spanning-tree portfast bpduguard default</code> on ALL switches in the domain.</li>
  <li><strong style="color:#ea580c">High error ports:</strong> Replace cables, check SFPs, verify NIC settings on connected servers.</li>
  <li><strong style="color:#d97706">PortFast:</strong> <code>spanning-tree portfast default</code> eliminates 30-second port delays for end devices.</li>
  <li><strong style="color:#d97706">Storm control:</strong> Configure per-port storm-control thresholds: <code>storm-control broadcast level 20</code> on access ports.</li>
  <li><strong style="color:#2563eb">Loop Guard:</strong> <code>spanning-tree loopguard default</code> on all non-edge ports.</li>
  <li><strong style="color:#2563eb">Port security:</strong> Limit MAC per access port: <code>switchport port-security maximum 3</code>.</li>
</ol>
</div>

<footer>
  Cisco IOS/IOS-XE Switch Performance Analytics &nbsp;|&nbsp;
  {e(hostname)} ({e(SWITCH_IP)}) &nbsp;|&nbsp; {ts}
</footer>

<script>
function filt(sev){{
  document.querySelectorAll('.fb').forEach(b=>b.classList.remove('active'));
  const map={{all:'.fa',critical:'.fc',high:'.fh',warning:'.fw',info:'.fi'}};
  document.querySelector(map[sev]||'.fa').classList.add('active');
  document.querySelectorAll('.fcard').forEach(c=>{{
    c.style.display=(sev==='all'||c.dataset.sev===sev)?'block':'none';
  }});
}}
</script>
</body>
</html>"""


# ─────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────

def main():
    print("=" * 62)
    print("  Cisco IOS/IOS-XE Switch Performance Analytics")
    print(f"  Target : {SWITCH_IP}")
    print(f"  User   : {USERNAME}")
    print(f"  Output : {OUTPUT_HTML}")
    print("=" * 62)

    raw = collect(SWITCH_IP, USERNAME, PASSWORD)

    print("\n[*] Parsing collected data...")
    switch_info = parse_version(raw.get("version", ""))
    parsed = {
        "switch_info" : switch_info,
        "cpu"         : parse_cpu(raw.get("cpu_sorted", "")),
        "memory"      : parse_memory(raw.get("memory_sorted", "") + raw.get("memory_stats", "")),
        "interfaces"  : parse_interfaces(raw.get("interfaces", "")),
        "stp"         : parse_stp_summary(raw.get("stp_summary", "") + raw.get("stp_detail", "")),
        "mac"         : parse_mac_count(raw.get("mac_count", "")),
        "log_issues"  : parse_log_issues(raw.get("logging", "")),
    }

    print("[*] Analyzing...")
    findings = analyze(parsed)

    print("[*] Generating HTML report...")
    html = generate_html(raw, parsed, findings, switch_info)

    with open(OUTPUT_HTML, "w", encoding="utf-8") as fh:
        fh.write(html)

    score, _, label, cnt = score_calc(findings)

    priv = raw.get("_priv_level", 1)
    print("=" * 62)
    print(f"  Report  : {OUTPUT_HTML}")
    print(f"  Host    : {switch_info.get('hostname', SWITCH_IP)}")
    print(f"  Priv    : {priv} ({'full data' if priv >= 15 else 'LIMITED — no CPU/mem/log data'})")
    print(f"  Score   : {score}/100 — {label}")
    print(f"  Issues  : {cnt['critical']} Critical | {cnt['high']} High | "
          f"{cnt['warning']} Warning | {cnt['info']} Info")
    print("=" * 62)


if __name__ == "__main__":
    main()
