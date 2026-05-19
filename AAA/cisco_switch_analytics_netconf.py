#!/usr/bin/env python3
"""
Cisco IOS-XE Switch Performance Analytics — NETCONF Edition
NETCONF/YANG-based data collection -> HTML report with findings & recommendations.

Advantages over SSH version:
  • Structured XML/YANG — no brittle CLI regex parsing
  • No enable/privilege-15 needed for operational data
  • Adds hardware environment monitoring (temp, fans, power)
  • Consistent across IOS-XE 16.6+

Requirements:
    pip install ncclient

Device prerequisites:
    netconf-yang
    aaa authorization exec default local   (if AAA configured)
"""

import sys
import getpass
import html as html_mod
from datetime import datetime
from xml.etree import ElementTree as ET

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

try:
    from ncclient import manager
    from ncclient.operations import RPCError
except ImportError:
    print("ERROR: ncclient not installed.  Run:  pip install ncclient")
    sys.exit(1)

# ─────────────────────────────────────────────────────────────
# Target
# ─────────────────────────────────────────────────────────────
SWITCH_IP    = "10.63.65.24"
USERNAME     = "mark"
PASSWORD     = getpass.getpass(f"Password for {USERNAME}@{SWITCH_IP}: ")
OUTPUT_HTML  = "Cisco_Switch_Analytics_NETCONF.html"
NETCONF_PORT = 830

# ─────────────────────────────────────────────────────────────
# YANG Namespaces
# ─────────────────────────────────────────────────────────────
_NS = {
    "cpu"     : "http://cisco.com/ns/yang/Cisco-IOS-XE-process-cpu-oper",
    "mem"     : "http://cisco.com/ns/yang/Cisco-IOS-XE-process-memory-oper",
    "memstat" : "http://cisco.com/ns/yang/Cisco-IOS-XE-memory-oper",
    "intf"    : "http://cisco.com/ns/yang/Cisco-IOS-XE-interfaces-oper",
    "stp"     : "http://cisco.com/ns/yang/Cisco-IOS-XE-spanning-tree-oper",
    "env"     : "http://cisco.com/ns/yang/Cisco-IOS-XE-environment-oper",
    "plat"    : "http://cisco.com/ns/yang/Cisco-IOS-XE-platform-oper",
    "matm"    : "http://cisco.com/ns/yang/Cisco-IOS-XE-matm-oper",
    "native"  : "http://cisco.com/ns/yang/Cisco-IOS-XE-native",
    "hw"      : "http://cisco.com/ns/yang/Cisco-IOS-XE-device-hardware-oper",
}


# ─────────────────────────────────────────────────────────────
# XML Helpers
# ─────────────────────────────────────────────────────────────

def _tag(ns_key, name):
    return f"{{{_NS[ns_key]}}}{name}"


def _child(elem, ns_key, tag):
    return elem.find(_tag(ns_key, tag)) if elem is not None else None


def _deep(elem, ns_key, *tags):
    cur = elem
    for t in tags:
        cur = _child(cur, ns_key, t)
        if cur is None:
            return None
    return cur


def _text(elem, ns_key, *tags, default=""):
    node = _deep(elem, ns_key, *tags)
    return node.text.strip() if node is not None and node.text else default


def _int(elem, ns_key, *tags, default=0):
    val = _text(elem, ns_key, *tags, default=None)
    if val is None:
        return default
    try:
        return int(val)
    except (ValueError, TypeError):
        return default


def _findall(root, ns_key, tag):
    return root.findall(f".//{_tag(ns_key, tag)}")


def _parse_reply(reply):
    try:
        return ET.fromstring(reply.data_xml)
    except Exception:
        try:
            full = ET.fromstring(reply.xml)
            for ns in ["urn:ietf:params:xml:ns:netconf:base:1.0", ""]:
                el = full.find(f".//{{{ns}}}data" if ns else ".//data")
                if el is not None:
                    return el
        except Exception:
            pass
        return ET.Element("empty")


# ─────────────────────────────────────────────────────────────
# NETCONF Fetch Wrappers
# ─────────────────────────────────────────────────────────────

def _get(m, filt, label):
    try:
        reply = m.get(filter=("subtree", filt))
        return _parse_reply(reply)
    except RPCError as e:
        print(f"    [!] RPC error ({label}): {e.message[:80]}")
        return ET.Element("empty")
    except Exception as e:
        print(f"    [!] Error ({label}): {e}")
        return ET.Element("empty")


def _get_config(m, filt, label):
    try:
        reply = m.get_config(source="running", filter=("subtree", filt))
        return _parse_reply(reply)
    except Exception as e:
        print(f"    [!] Config error ({label}): {e}")
        return ET.Element("empty")


# ─────────────────────────────────────────────────────────────
# Collection Functions
# ─────────────────────────────────────────────────────────────

def collect_device_info(m):
    info = {
        "hostname"   : SWITCH_IP,
        "ios_version": "Unknown",
        "model"      : "Unknown",
        "serial"     : "Unknown",
        "uptime"     : "Unknown",
    }

    # Hostname + version from native config
    filt = f'<filter><native xmlns="{_NS["native"]}"><hostname/><version/></native></filter>'
    root = _get_config(m, filt, "hostname")
    h = root.find(f".//{_tag('native','hostname')}")
    if h is not None and h.text:
        info["hostname"] = h.text.strip()
    v = root.find(f".//{_tag('native','version')}")
    if v is not None and v.text:
        info["ios_version"] = v.text.strip()

    # Hardware oper: software version + boot time
    filt_hw = f'<filter><device-hardware-data xmlns="{_NS["hw"]}"/></filter>'
    hw = _get(m, filt_hw, "hardware")
    sys_data = hw.find(f".//{_tag('hw','device-system-data')}")
    if sys_data is not None:
        sw = _child(sys_data, "hw", "software-version")
        if sw is not None and sw.text:
            info["ios_version"] = sw.text.strip()
        bt = _child(sys_data, "hw", "boot-time")
        if bt is not None and bt.text:
            info["uptime"] = f"since {bt.text.strip()}"

    # Platform components: model + serial
    filt_plat = f'<filter><components xmlns="{_NS["plat"]}"/></filter>'
    plat = _get(m, filt_plat, "platform")
    for comp in _findall(plat, "plat", "component"):
        cname = _text(comp, "plat", "cname").lower()
        if cname in ("1", "chassis") or "chassis" in cname:
            state = _child(comp, "plat", "state")
            if state is not None:
                ser = _text(state, "plat", "serial-no")
                desc = _text(state, "plat", "description")
                if ser:
                    info["serial"] = ser
                if desc:
                    info["model"] = desc
            break

    return info


def collect_cpu(m):
    result = {"five_sec": 0, "one_min": 0, "five_min": 0, "processes": []}
    filt = f'<filter><cpu-usage xmlns="{_NS["cpu"]}"/></filter>'
    root = _get(m, filt, "CPU")

    util = root.find(f".//{_tag('cpu','cpu-utilization')}")
    if util is not None:
        result["five_sec"] = _int(util, "cpu", "five-seconds")
        result["one_min"]  = _int(util, "cpu", "one-minute")
        result["five_min"] = _int(util, "cpu", "five-minutes")

    procs = []
    for p in _findall(root, "cpu", "cpu-usage-process"):
        procs.append({
            "pid"      : _text(p, "cpu", "pid"),
            "name"     : _text(p, "cpu", "name"),
            "five_sec" : _int(p, "cpu", "five-seconds"),
            "one_min"  : _int(p, "cpu", "one-minute"),
            "five_min" : _int(p, "cpu", "five-minutes"),
        })
    procs.sort(key=lambda x: x["five_min"], reverse=True)
    result["processes"] = procs[:15]
    return result


def collect_memory(m):
    result = {"processor": {}, "top_procs": []}

    # System-level totals from memory-oper
    filt_stat = f'<filter><memory-statistics xmlns="{_NS["memstat"]}"/></filter>'
    root_stat = _get(m, filt_stat, "memory-stats")
    for stat in _findall(root_stat, "memstat", "memory-statistic"):
        name = _text(stat, "memstat", "name").lower()
        if "processor" in name or name == "processor":
            total = _int(stat, "memstat", "total-memory")
            used  = _int(stat, "memstat", "used-memory")
            free  = _int(stat, "memstat", "free-memory")
            result["processor"] = {
                "total": total,
                "used" : used,
                "free" : free,
                "pct"  : round(used / total * 100, 1) if total else 0,
            }
            break

    # Per-process memory top consumers
    filt_proc = f'<filter><memory-usage-processes xmlns="{_NS["mem"]}"/></filter>'
    root_proc = _get(m, filt_proc, "memory-procs")
    procs = []
    for p in _findall(root_proc, "mem", "memory-usage-process"):
        hold = _int(p, "mem", "holding-memory")
        procs.append({
            "pid"     : _text(p, "mem", "pid"),
            "name"    : _text(p, "mem", "name"),
            "holding" : hold,
        })

    # Fallback if memory-oper not available: estimate from process totals
    if not result["processor"] and procs:
        total_alloc = sum(
            _int(p, "mem", "allocated-memory")
            for p in _findall(root_proc, "mem", "memory-usage-process")
        )
        total_hold = sum(x["holding"] for x in procs)
        result["processor"] = {
            "total": total_alloc,
            "used" : total_hold,
            "free" : max(0, total_alloc - total_hold),
            "pct"  : round(total_hold / total_alloc * 100, 1) if total_alloc else 0,
        }

    procs.sort(key=lambda x: x["holding"], reverse=True)
    result["top_procs"] = procs[:10]
    return result


def collect_interfaces(m):
    ifaces = {}
    filt = f'<filter><interfaces xmlns="{_NS["intf"]}"/></filter>'
    root = _get(m, filt, "interfaces")

    for iface in _findall(root, "intf", "interface"):
        name = _text(iface, "intf", "name")
        if not name:
            continue

        oper  = _text(iface, "intf", "oper-status")
        admin = _text(iface, "intf", "admin-status")

        if admin == "if-oper-state-no-pass":
            link  = "administratively down"
            proto = "down"
        elif oper == "if-oper-state-ready":
            link  = "up"
            proto = "up"
        else:
            link  = "down"
            proto = "down"

        duplex_raw = _text(iface, "intf", "duplex-mode")
        duplex = ("Full-duplex" if "full" in duplex_raw.lower()
                  else "Half-duplex" if "half" in duplex_raw.lower()
                  else "Auto-duplex" if "auto" in duplex_raw.lower()
                  else "")

        speed_val = _int(iface, "intf", "speed")
        if speed_val >= 1_000_000_000:
            speed_str = f"{speed_val // 1_000_000_000}Gb/s"
        elif speed_val >= 1_000_000:
            speed_str = f"{speed_val // 1_000_000}Mb/s"
        elif speed_val > 0:
            speed_str = f"{speed_val}b/s"
        else:
            speed_str = ""

        stats = _child(iface, "intf", "statistics")
        def _s(tag):
            return _int(stats, "intf", tag) if stats is not None else 0

        ifaces[name] = {
            "link"         : link,
            "proto"        : proto,
            "description"  : _text(iface, "intf", "description"),
            "duplex"       : duplex,
            "speed"        : speed_str,
            "input_errors" : _s("in-errors"),
            "crc"          : _s("in-crc-errors"),
            "output_errors": _s("out-errors"),
            "drops"        : _s("in-discards") + _s("out-discards"),
            "collisions"   : _s("out-collision-pkts"),
            "resets"       : 0,
            "runts"        : 0,
            "giants"       : 0,
            "in_rate"      : "",
            "out_rate"     : "",
            "in_octets"    : _s("in-octets"),
            "out_octets"   : _s("out-octets"),
        }
    return ifaces


def collect_stp(m):
    result = {
        "mode": "", "total_vlans": 0, "root_vlans": 0,
        "bpdu_guard": False, "portfast_default": False,
        "loop_guard": False, "tcn_events": 0,
    }

    # Operational STP data
    filt_oper = f'<filter><stp-details xmlns="{_NS["stp"]}"/></filter>'
    root_oper = _get(m, filt_oper, "STP-oper")

    global_stp = root_oper.find(f".//{_tag('stp','stp-global')}")
    if global_stp is not None:
        result["bpdu_guard"]       = _text(global_stp, "stp", "bpduguard-default") == "true"
        result["portfast_default"] = _text(global_stp, "stp", "portfast-default")  == "true"
        result["loop_guard"]       = _text(global_stp, "stp", "loopguard-default") == "true"
        result["mode"]             = _text(global_stp, "stp", "mode")

    instances = _findall(root_oper, "stp", "stp-detail")
    result["total_vlans"] = len(instances)
    result["root_vlans"]  = sum(
        1 for i in instances if _text(i, "stp", "is-root") == "true"
    )
    for inst in instances:
        result["tcn_events"] += _int(inst, "stp", "topology-changes")

    # Fallback: check native running config for portfast/bpduguard/loopguard
    filt_cfg = (f'<filter><native xmlns="{_NS["native"]}">'
                f'<spanning-tree/></native></filter>')
    cfg = _get_config(m, filt_cfg, "STP-config")
    stp_n = cfg.find(f".//{_tag('native','spanning-tree')}")
    if stp_n is not None:
        pf = _child(stp_n, "native", "portfast")
        if pf is not None:
            pf_default = _child(pf, "native", "default")
            if pf_default is not None:
                result["portfast_default"] = True
            bg = _child(pf, "native", "bpduguard")
            if bg is not None and _child(bg, "native", "default") is not None:
                result["bpdu_guard"] = True
        lg = _child(stp_n, "native", "loopguard")
        if lg is not None and _child(lg, "native", "default") is not None:
            result["loop_guard"] = True
        if not result["mode"]:
            mode_c = _child(stp_n, "native", "mode")
            if mode_c is not None:
                for m_name in ("pvst", "rapid-pvst", "mst"):
                    if mode_c.find(_tag("native", m_name)) is not None:
                        result["mode"] = m_name
                        break

    return result


def collect_mac(m):
    result = {"total": 0, "dynamic": 0, "static": 0, "max": 0}
    filt = f'<filter><matm-table xmlns="{_NS["matm"]}"/></filter>'
    root = _get(m, filt, "MAC-table")

    entries = _findall(root, "matm", "matm-mac-table-entry")
    result["total"] = len(entries)
    for entry in entries:
        t = _text(entry, "matm", "entry-type").lower()
        if "dynamic" in t:
            result["dynamic"] += 1
        elif "static" in t:
            result["static"] += 1
    return result


def collect_environment(m):
    result = {"sensors": [], "alarms": []}
    filt = f'<filter><environment-sensors xmlns="{_NS["env"]}"/></filter>'
    root = _get(m, filt, "environment")

    for sensor in _findall(root, "env", "environment-sensor"):
        name     = _text(sensor, "env", "name")
        location = _text(sensor, "env", "location")
        state    = _text(sensor, "env", "state")
        value    = _text(sensor, "env", "current-reading")
        units    = _text(sensor, "env", "sensor-units")

        entry = {"name": name, "location": location,
                 "state": state, "value": value, "units": units}
        result["sensors"].append(entry)

        if state.lower() not in ("ok", "normal", "not present", ""):
            result["alarms"].append({
                "name" : f"{name} ({location})" if location else name,
                "state": state,
                "value": f"{value} {units}".strip(),
            })
    return result


def collect_all(ip, username, password):
    data = {}
    errors = []

    print(f"\n[*] Connecting to {ip}:{NETCONF_PORT} via NETCONF...")
    try:
        with manager.connect(
            host=ip,
            port=NETCONF_PORT,
            username=username,
            password=password,
            hostkey_verify=False,
            manager_params={"timeout": 60},
            device_params={"name": "iosxe"},
        ) as m:
            caps = [c for c in m.server_capabilities
                    if "cisco.com/ns/yang" in c]
            print(f"[+] NETCONF session established  "
                  f"({len(caps)} Cisco YANG models advertised)")

            steps = [
                ("device_info" , collect_device_info),
                ("cpu"         , collect_cpu),
                ("memory"      , collect_memory),
                ("interfaces"  , collect_interfaces),
                ("stp"         , collect_stp),
                ("mac"         , collect_mac),
                ("environment" , collect_environment),
            ]
            for key, fn in steps:
                print(f"    → {key}...")
                try:
                    data[key] = fn(m)
                except Exception as exc:
                    print(f"      [!] Failed: {exc}")
                    errors.append(f"{key}: {exc}")
                    data[key] = {}

            data["_capabilities"] = len(caps)

    except Exception as e:
        print(f"[-] NETCONF connection failed: {e}")
        sys.exit(1)

    if errors:
        print(f"\n[!] {len(errors)} collection error(s):")
        for err in errors:
            print(f"    {err}")

    return data


# ─────────────────────────────────────────────────────────────
# Analysis Engine
# ─────────────────────────────────────────────────────────────

def finding(sev, area, title, detail, recommendation):
    return {"sev": sev, "area": area, "title": title,
            "detail": detail, "rec": recommendation}


def analyze(data):
    findings = []
    cpu   = data.get("cpu", {})
    mem   = data.get("memory", {})
    ifaces = data.get("interfaces", {})
    stp   = data.get("stp", {})
    mac   = data.get("mac", {})
    env   = data.get("environment", {})

    # ── CPU ──────────────────────────────────────────────────
    five_min = cpu.get("five_min", 0)
    if five_min >= 90:
        findings.append(finding("critical", "CPU",
            f"CPU utilization critical: {five_min}% (5-min avg)",
            "Sustained CPU above 90% causes packet drops, slow CLI, "
            "and protocol timeouts (OSPF, HSRP, STP).",
            "Identify top process via NETCONF cpu-usage-process table. "
            "Common causes: broadcast storm, routing protocol instability, "
            "ACL on high-traffic ports, excessive SNMP polling."))
    elif five_min >= 70:
        findings.append(finding("high", "CPU",
            f"CPU utilization high: {five_min}% (5-min avg)",
            "CPU above 70% risks protocol adjacency drops.",
            "Review top CPU processes. Check for STP TCN storms, "
            "excessive ARP/broadcast, or misconfigured SNMP."))
    elif five_min >= 50:
        findings.append(finding("warning", "CPU",
            f"CPU utilization elevated: {five_min}% (5-min avg)",
            "Normal IOS-XE switch baseline is typically <20%.",
            "Monitor trend over time. Profile top processes."))

    # ── Memory ───────────────────────────────────────────────
    pmem = mem.get("processor", {})
    pct  = pmem.get("pct", 0)
    if pct >= 85:
        findings.append(finding("critical", "Memory",
            f"Processor memory critical: {pct}% used",
            "Memory above 85% risks IOS crashes and process restarts.",
            "Check top memory processes in NETCONF report. "
            "Common culprits: BGP full table, large ACL, netflow cache."))
    elif pct >= 70:
        findings.append(finding("high", "Memory",
            f"Processor memory high: {pct}% used",
            "Approaching critical threshold. Monitor trend.",
            "Identify top memory consumers and review routing table size."))

    # ── Interfaces ───────────────────────────────────────────
    half_duplex_up  = []
    high_error_ifaces = []

    for name, iface in ifaces.items():
        if (iface["link"] == "up" and iface["proto"] == "up"
                and "half" in iface["duplex"].lower()):
            half_duplex_up.append(name)

        total_err = iface["input_errors"] + iface["crc"] + iface["output_errors"]
        if total_err > 1000:
            high_error_ifaces.append((name, total_err, iface["crc"],
                                      iface["input_errors"], iface["output_errors"],
                                      iface["drops"]))

    if half_duplex_up:
        findings.append(finding("high", "Interfaces",
            f"Half-duplex on {len(half_duplex_up)} active port(s): "
            f"{', '.join(half_duplex_up[:5])}",
            "Half-duplex causes collisions and degrades throughput below 20% of nominal.",
            "Set explicit 'duplex full' + 'speed' on both ends. "
            "Never use auto/auto on uplinks or trunks."))

    if high_error_ifaces:
        top = sorted(high_error_ifaces, key=lambda x: x[1], reverse=True)[:5]
        detail = "; ".join(f"{n}: {e} errors (CRC:{c})" for n, e, c, *_ in top)
        findings.append(finding("high", "Interfaces",
            f"{len(high_error_ifaces)} port(s) with >1000 errors",
            f"High errors indicate L1 or duplex problems: {detail}",
            "Check cabling (replace patch cable), SFP health, duplex/speed mismatch."))

    up_ports   = sum(1 for i in ifaces.values() if i["link"] == "up")
    admin_down = sum(1 for i in ifaces.values() if "administratively" in i["link"])
    if admin_down > 0:
        findings.append(finding("info", "Interfaces",
            f"{admin_down} port(s) administratively shut down",
            "Ensure unused ports are intentionally disabled.",
            "Place unused ports in a dedicated black-hole VLAN (e.g. 999) + 'shutdown'."))

    # ── Spanning Tree ─────────────────────────────────────────
    tcn = stp.get("tcn_events", 0)
    if tcn > 100:
        findings.append(finding("high", "Spanning Tree",
            f"High topology-change counter: {tcn:,}",
            "Excessive TCNs flush the MAC table causing flooding on all ports.",
            "Enable 'spanning-tree portfast' on access ports and "
            "'spanning-tree bpduguard enable' to prevent non-switch TCNs."))

    if not stp.get("bpdu_guard"):
        findings.append(finding("high", "Spanning Tree",
            "BPDU Guard not enabled globally",
            "Without BPDU Guard, a rogue switch can trigger STP topology changes.",
            "Apply: 'spanning-tree portfast bpduguard default'"))

    if not stp.get("portfast_default"):
        findings.append(finding("warning", "Spanning Tree",
            "PortFast not enabled as global default for access ports",
            "Without PortFast, access ports wait 30 seconds before forwarding, "
            "causing endpoint delays and DHCP timeouts.",
            "Enable: 'spanning-tree portfast default' (non-trunk ports only)."))

    if not stp.get("loop_guard"):
        findings.append(finding("info", "Spanning Tree",
            "Loop Guard not enabled",
            "Loop Guard protects against unidirectional link failures.",
            "Enable: 'spanning-tree loopguard default'"))

    # ── MAC Table ─────────────────────────────────────────────
    if mac.get("max", 0) > 0:
        fill_pct = round(mac["total"] / mac["max"] * 100, 1)
        if fill_pct >= 80:
            findings.append(finding("critical", "MAC Table",
                f"CAM table {fill_pct}% full ({mac['total']}/{mac['max']} entries)",
                "Full CAM table causes the switch to flood unknown unicast on all ports.",
                "Investigate rogue hubs/VMs with many MACs. Enable port-security."))
        elif fill_pct >= 60:
            findings.append(finding("warning", "MAC Table",
                f"CAM table {fill_pct}% full",
                "Approaching CAM table capacity. Monitor trend.",
                "Implement port-security with maximum MAC limit per port."))

    # ── Environment (NETCONF bonus data) ─────────────────────
    for alarm in env.get("alarms", []):
        sev = ("critical" if any(w in alarm["state"].lower()
                                 for w in ("critical", "failure", "failed", "alarm"))
               else "high" if "warn" in alarm["state"].lower()
               else "warning")
        findings.append(finding(sev, "Environment",
            f"Sensor alarm: {alarm['name']}",
            f"State: {alarm['state']}  Reading: {alarm['value']}",
            "Check hardware for overheating, fan failure, or power supply issue. "
            "Verify airflow and ambient temperature."))

    return findings


# ─────────────────────────────────────────────────────────────
# Score
# ─────────────────────────────────────────────────────────────

def score_calc(findings):
    c = {"critical": 0, "high": 0, "warning": 0, "info": 0}
    for f in findings:
        c[f["sev"]] = c.get(f["sev"], 0) + 1
    s = max(0, 100 - c["critical"]*20 - c["high"]*10 - c["warning"]*4 - c["info"]*1)
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


def bar(pct, color_fn):
    color = color_fn(pct)
    return (f'<div style="background:#1e293b;border-radius:4px;height:10px;width:200px;'
            f'display:inline-block;vertical-align:middle">'
            f'<div style="width:{min(pct,100)}%;height:100%;background:{color};'
            f'border-radius:4px"></div></div> '
            f'<span style="font-size:.82rem;color:{color}">{pct}%</span>')


def cpu_bar(pct):
    return bar(pct, lambda p: "#dc2626" if p>=80 else "#d97706" if p>=50 else "#16a34a")


def mem_bar(pct):
    return bar(pct, lambda p: "#dc2626" if p>=85 else "#d97706" if p>=70 else "#38bdf8")


def fmt_bytes(b):
    if b >= 1_073_741_824:
        return f"{b/1_073_741_824:.1f} GB"
    if b >= 1_048_576:
        return f"{b/1_048_576:.1f} MB"
    if b >= 1024:
        return f"{b/1024:.1f} KB"
    return f"{b} B"


def generate_html(data, findings):
    ts       = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    score, score_color, score_label, cnt = score_calc(findings)
    total_f  = len(findings)
    sorted_f = sorted(findings, key=lambda x: SEV_ORDER.get(x["sev"], 9))

    dev   = data.get("device_info", {})
    cpu   = data.get("cpu", {"five_sec":0,"one_min":0,"five_min":0,"processes":[]})
    mem   = data.get("memory", {"processor":{},"top_procs":[]})
    ifaces = data.get("interfaces", {})
    stp   = data.get("stp", {})
    mac   = data.get("mac", {})
    env   = data.get("environment", {"sensors":[],"alarms":[]})
    ncaps = data.get("_capabilities", 0)

    hostname = dev.get("hostname", SWITCH_IP)
    pmem     = mem.get("processor", {})
    mem_pct  = pmem.get("pct", 0)
    cam_fill = round(mac["total"] / mac["max"] * 100, 1) if mac.get("max") else 0
    cam_color = "#dc2626" if cam_fill >= 80 else "#d97706" if cam_fill >= 60 else "#4ade80"

    # ── Finding cards ─────────────────────────────────────────
    cards = ""
    for i, f in enumerate(sorted_f, 1):
        cards += f"""
<div class="fcard {f['sev']}" data-sev="{f['sev']}">
  <div class="fhead">{badge(f['sev'])} <span class="fnum">#{i}</span>
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
    for p in cpu.get("processes", []):
        clr = "#dc2626" if p["five_min"]>=30 else "#d97706" if p["five_min"]>=10 else "#94a3b8"
        cpu_rows += (f"<tr><td>{e(p['pid'])}</td><td>{e(p['name'])}</td>"
                     f"<td style='color:{clr}'>{p['five_sec']}%</td>"
                     f"<td style='color:{clr}'>{p['one_min']}%</td>"
                     f"<td style='color:{clr}'>{p['five_min']}%</td></tr>")
    if not cpu_rows:
        cpu_rows = '<tr><td colspan="5" class="muted">No process data available</td></tr>'

    # ── Memory process table ──────────────────────────────────
    mem_rows = ""
    for p in mem.get("top_procs", []):
        mem_rows += (f"<tr><td>{e(p['pid'])}</td><td>{e(p['name'])}</td>"
                     f"<td>{fmt_bytes(p['holding'])}</td></tr>")
    if not mem_rows:
        mem_rows = '<tr><td colspan="3" class="muted">No process memory data</td></tr>'

    # ── Interface table ───────────────────────────────────────
    iface_rows = ""
    sorted_ifaces = sorted(
        ifaces.items(),
        key=lambda kv: kv[1]["input_errors"] + kv[1]["crc"] + kv[1]["output_errors"],
        reverse=True
    )
    for name, iface in sorted_ifaces[:40]:
        link_color   = "#4ade80" if iface["link"] == "up" else "#f87171"
        duplex_color = "#f87171" if "half" in iface["duplex"].lower() else "#94a3b8"
        err_total    = iface["input_errors"] + iface["crc"] + iface["output_errors"]
        err_color    = "#dc2626" if err_total > 10000 else "#d97706" if err_total > 1000 else "#94a3b8"
        iface_rows += (
            f"<tr>"
            f"<td>{e(name)}</td>"
            f"<td><span style='color:{link_color}'>{e(iface['link'])}</span></td>"
            f"<td>{e(iface['description'][:30]) or '—'}</td>"
            f"<td><span style='color:{duplex_color}'>{e(iface['duplex']) or '—'}</span></td>"
            f"<td>{e(iface['speed']) or '—'}</td>"
            f"<td style='color:{err_color}'>{iface['input_errors']:,}</td>"
            f"<td style='color:{err_color}'>{iface['crc']:,}</td>"
            f"<td style='color:{err_color}'>{iface['output_errors']:,}</td>"
            f"<td>{iface['drops']:,}</td>"
            f"<td>{fmt_bytes(iface['in_octets'])}</td>"
            f"<td>{fmt_bytes(iface['out_octets'])}</td>"
            f"</tr>")
    if not iface_rows:
        iface_rows = '<tr><td colspan="11" class="muted">No interface data</td></tr>'

    # ── Environment table ─────────────────────────────────────
    env_rows = ""
    for s in env.get("sensors", []):
        state_color = ("#dc2626" if any(w in s["state"].lower()
                                        for w in ("critical","fail","alarm"))
                       else "#d97706" if "warn" in s["state"].lower()
                       else "#4ade80" if s["state"].lower() in ("ok","normal")
                       else "#94a3b8")
        env_rows += (f"<tr><td>{e(s['name'])}</td><td>{e(s['location'])}</td>"
                     f"<td>{e(s['value'])} {e(s['units'])}</td>"
                     f"<td style='color:{state_color}'>{e(s['state'])}</td></tr>")
    if not env_rows:
        env_rows = '<tr><td colspan="4" class="muted">No environment sensor data</td></tr>'

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>Switch Analytics NETCONF — {e(hostname)}</title>
<style>
:root{{--bg:#0f172a;--card:#1e293b;--border:#334155;--text:#e2e8f0;--muted:#94a3b8;--accent:#38bdf8}}
*{{box-sizing:border-box;margin:0;padding:0}}
body{{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;background:var(--bg);color:var(--text);padding:28px;line-height:1.5}}
h1{{font-size:1.75rem;font-weight:800;color:#f1f5f9}}
h2{{font-size:1.1rem;font-weight:700;color:#cbd5e1;margin:32px 0 14px;padding-bottom:6px;border-bottom:1px solid var(--border)}}
.header{{display:flex;align-items:center;justify-content:space-between;padding:24px 28px;background:var(--card);border:1px solid var(--border);border-radius:14px;margin-bottom:26px}}
.header-meta{{font-size:.78rem;color:var(--muted);margin-top:4px}}
.netconf-badge{{display:inline-block;padding:3px 12px;border-radius:999px;font-size:.72rem;font-weight:700;color:#fff;background:#0ea5e9;letter-spacing:.04em;margin-left:10px}}
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
footer{{text-align:center;color:var(--muted);font-size:.72rem;margin-top:44px;padding-top:18px;border-top:1px solid var(--border)}}
@media(max-width:768px){{.grid2{{grid-template-columns:1fr}}}}
</style>
</head>
<body>

<div class="header">
  <div>
    <h1>Cisco Switch Performance Analytics
      <span class="netconf-badge">NETCONF</span>
    </h1>
    <div class="header-meta">
      {e(hostname)} &nbsp;|&nbsp; {e(SWITCH_IP)} &nbsp;|&nbsp;
      Model: {e(dev.get('model','Unknown'))} &nbsp;|&nbsp;
      IOS-XE: {e(dev.get('ios_version','Unknown'))}<br>
      Serial: {e(dev.get('serial','Unknown'))} &nbsp;|&nbsp;
      Uptime: {e(dev.get('uptime','Unknown'))} &nbsp;|&nbsp;
      YANG models: {ncaps} &nbsp;|&nbsp; Generated: {ts}
    </div>
  </div>
  <div style="font-size:2.4rem">🔀</div>
</div>

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
  <div class="stat"><div class="stat-n" style="color:#38bdf8">{cpu.get('five_min',0)}%</div><div class="stat-l">CPU 5min</div></div>
  <div class="stat"><div class="stat-n" style="color:#94a3b8">{mem_pct}%</div><div class="stat-l">Mem used</div></div>
  <div class="stat"><div class="stat-n" style="color:#94a3b8">{sum(1 for i in ifaces.values() if i['link']=='up')}</div><div class="stat-l">Ports Up</div></div>
  <div class="stat"><div class="stat-n" style="color:{cam_color}">{cam_fill}%</div><div class="stat-l">CAM Table</div></div>
</div>

<div class="grid2">
  <div class="card">
    <h3>CPU Utilization</h3>
    <div class="metric"><label>5 seconds</label>{cpu_bar(cpu.get('five_sec',0))}</div>
    <div class="metric"><label>1 minute</label>{cpu_bar(cpu.get('one_min',0))}</div>
    <div class="metric"><label>5 minutes</label>{cpu_bar(cpu.get('five_min',0))}</div>
  </div>
  <div class="card">
    <h3>Memory (Processor)</h3>
    <div class="metric"><label>Used</label>{mem_bar(mem_pct)}</div>
    <div class="metric"><label>Total</label><span>{fmt_bytes(pmem.get('total',0))}</span></div>
    <div class="metric"><label>Used</label><span>{fmt_bytes(pmem.get('used',0))}</span></div>
    <div class="metric"><label>Free</label><span>{fmt_bytes(pmem.get('free',0))}</span></div>
  </div>
  <div class="card">
    <h3>Spanning Tree</h3>
    <div class="metric"><label>Mode</label><span>{e(stp.get('mode','')) or '—'}</span></div>
    <div class="metric"><label>Active VLANs</label><span>{stp.get('total_vlans',0)}</span></div>
    <div class="metric"><label>Root VLANs</label><span>{stp.get('root_vlans',0)}</span></div>
    <div class="metric"><label>BPDU Guard</label>
      <span style="color:{'#4ade80' if stp.get('bpdu_guard') else '#f87171'}">
        {'Enabled' if stp.get('bpdu_guard') else 'DISABLED'}</span></div>
    <div class="metric"><label>PortFast Default</label>
      <span style="color:{'#4ade80' if stp.get('portfast_default') else '#f87171'}">
        {'Enabled' if stp.get('portfast_default') else 'DISABLED'}</span></div>
    <div class="metric"><label>Loop Guard</label>
      <span style="color:{'#4ade80' if stp.get('loop_guard') else '#d97706'}">
        {'Enabled' if stp.get('loop_guard') else 'Disabled'}</span></div>
    <div class="metric"><label>Topology Changes</label>
      <span style="color:{'#dc2626' if stp.get('tcn_events',0)>100 else '#94a3b8'}">
        {stp.get('tcn_events',0):,}</span></div>
  </div>
  <div class="card">
    <h3>CAM / MAC Table</h3>
    <div class="metric"><label>Total MACs</label><span>{mac.get('total',0):,}</span></div>
    <div class="metric"><label>Dynamic</label><span>{mac.get('dynamic',0):,}</span></div>
    <div class="metric"><label>Static</label><span>{mac.get('static',0):,}</span></div>
    <div class="metric"><label>Max Capacity</label><span>{mac.get('max',0):,}</span></div>
    <div class="metric"><label>Fill %</label>
      <span style="color:{cam_color}">{cam_fill}%</span></div>
  </div>
</div>

<h2>Top CPU Processes (YANG: Cisco-IOS-XE-process-cpu-oper)</h2>
<div class="tw">
<table>
  <thead><tr><th>PID</th><th>Process Name</th><th>CPU 5s</th><th>CPU 1m</th><th>CPU 5m</th></tr></thead>
  <tbody>{cpu_rows}</tbody>
</table>
</div>

<h2>Top Memory Consumers (YANG: Cisco-IOS-XE-process-memory-oper)</h2>
<div class="tw">
<table>
  <thead><tr><th>PID</th><th>Process Name</th><th>Holding Memory</th></tr></thead>
  <tbody>{mem_rows}</tbody>
</table>
</div>

<h2>Interfaces (sorted by error count, top 40 — YANG: Cisco-IOS-XE-interfaces-oper)</h2>
<div class="tw">
<table>
  <thead><tr>
    <th>Interface</th><th>Status</th><th>Description</th><th>Duplex</th><th>Speed</th>
    <th>In Errors</th><th>CRC</th><th>Out Errors</th><th>Drops</th>
    <th>In Octets</th><th>Out Octets</th>
  </tr></thead>
  <tbody>{iface_rows}</tbody>
</table>
</div>

<h2>Environment Sensors (YANG: Cisco-IOS-XE-environment-oper) — {len(env.get('sensors',[]))} sensors</h2>
<div class="tw">
<table>
  <thead><tr><th>Sensor</th><th>Location</th><th>Reading</th><th>State</th></tr></thead>
  <tbody>{env_rows}</tbody>
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
  <li><strong style="color:#dc2626">Critical first:</strong> Resolve environment alarms, CAM overflow and CPU &gt;90% before any other work.</li>
  <li><strong style="color:#ea580c">Half-duplex:</strong> Set explicit <code>duplex full</code> + <code>speed</code> on ALL uplinks — never leave auto/auto on trunks.</li>
  <li><strong style="color:#ea580c">BPDU Guard:</strong> <code>spanning-tree portfast bpduguard default</code> on ALL switches in the domain.</li>
  <li><strong style="color:#ea580c">High error ports:</strong> Replace cables, check SFPs, verify NIC settings on connected servers.</li>
  <li><strong style="color:#d97706">PortFast:</strong> <code>spanning-tree portfast default</code> eliminates 30-second port delays for end devices.</li>
  <li><strong style="color:#d97706">Storm control:</strong> <code>storm-control broadcast level 20</code> on access ports.</li>
  <li><strong style="color:#2563eb">Loop Guard:</strong> <code>spanning-tree loopguard default</code> on all non-edge ports.</li>
  <li><strong style="color:#2563eb">Port security:</strong> <code>switchport port-security maximum 3</code> on access ports.</li>
</ol>
</div>

<footer>
  Cisco IOS-XE Switch Analytics — NETCONF Edition &nbsp;|&nbsp;
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
    print("  Cisco IOS-XE Switch Analytics — NETCONF Edition")
    print(f"  Target : {SWITCH_IP}:{NETCONF_PORT}")
    print(f"  User   : {USERNAME}")
    print(f"  Output : {OUTPUT_HTML}")
    print("=" * 62)

    data = collect_all(SWITCH_IP, USERNAME, PASSWORD)

    print("\n[*] Analyzing...")
    findings = analyze(data)

    print("[*] Generating HTML report...")
    html = generate_html(data, findings)
    with open(OUTPUT_HTML, "w", encoding="utf-8") as fh:
        fh.write(html)

    score, _, label, cnt = score_calc(findings)
    dev = data.get("device_info", {})

    print("=" * 62)
    print(f"  Report  : {OUTPUT_HTML}")
    print(f"  Host    : {dev.get('hostname', SWITCH_IP)}")
    print(f"  Model   : {dev.get('model', 'Unknown')}")
    print(f"  IOS-XE  : {dev.get('ios_version', 'Unknown')}")
    print(f"  Score   : {score}/100 — {label}")
    print(f"  Issues  : {cnt['critical']} Critical | {cnt['high']} High | "
          f"{cnt['warning']} Warning | {cnt['info']} Info")
    env_alarms = len(data.get("environment", {}).get("alarms", []))
    if env_alarms:
        print(f"  Env     : {env_alarms} hardware sensor alarm(s)!")
    print("=" * 62)


if __name__ == "__main__":
    main()
