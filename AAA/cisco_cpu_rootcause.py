#!/usr/bin/env python3
"""
Cisco IOS/IOS-XE CPU Root-Cause Investigator
=============================================
Identifies the probable source of high CPU / poor switch performance
using only USER EXEC commands + external SNMP probe (no privilege 15 needed).

Tone: Sarcastic. Because someone has to be.

Requirements: pip install netmiko
"""

import sys
import getpass
import re
import socket
import random
import html as html_mod
from datetime import datetime
from collections import defaultdict

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

try:
    from netmiko import ConnectHandler, NetmikoTimeoutException, NetmikoAuthenticationException
except ImportError:
    print("ERROR: pip install netmiko")
    sys.exit(1)

# ─────────────────────────────────────────────────────────────
# Target
# ─────────────────────────────────────────────────────────────
SWITCH_IP   = "10.63.65.24"
USERNAME    = "mark"
PASSWORD    = getpass.getpass(f"Password for {USERNAME}@{SWITCH_IP}: ")
OUTPUT_HTML = "Cisco_CPU_RootCause.html"

# SNMP probe settings (external, no SSH needed)
SNMP_PORT      = 161
SNMP_TIMEOUT   = 2      # seconds per community attempt
SNMP_COMMUNITIES = [
    "public", "private", "cisco", "admin", "community",
    "snmp", "network", "monitor", "read", "default",
    "switch", "manager", "secret", "password", "semmelweis",
]
OID_SYSDESCR   = "1.3.6.1.2.1.1.1.0"
OID_SYSNAME    = "1.3.6.1.2.1.1.5.0"
OID_CPU_5MIN   = "1.3.6.1.4.1.9.9.109.1.1.1.1.8.1"   # Cisco cpmCPUTotal5minRev

# ─────────────────────────────────────────────────────────────
# Minimal SNMP v2c GET  (raw UDP — no pysnmp dependency)
# ─────────────────────────────────────────────────────────────

def _ber_length(n):
    if n < 128:
        return bytes([n])
    elif n < 256:
        return bytes([0x81, n])
    else:
        return bytes([0x82, n >> 8, n & 0xFF])


def _tlv(tag, value: bytes) -> bytes:
    return bytes([tag]) + _ber_length(len(value)) + value


def _encode_oid(oid_str: str) -> bytes:
    parts = [int(x) for x in oid_str.strip(".").split(".")]
    out = [40 * parts[0] + parts[1]]
    for p in parts[2:]:
        if p == 0:
            out.append(0)
        else:
            buf = []
            while p:
                buf.insert(0, p & 0x7F)
                p >>= 7
            for i in range(len(buf) - 1):
                buf[i] |= 0x80
            out.extend(buf)
    return bytes(out)


def _decode_string(data: bytes, offset: int):
    """Decode a BER TLV value at offset, return (value_bytes, next_offset)."""
    if offset >= len(data):
        return b"", offset
    tag = data[offset]; offset += 1
    if data[offset] & 0x80:
        llen = data[offset] & 0x7F; offset += 1
        length = int.from_bytes(data[offset:offset+llen], "big"); offset += llen
    else:
        length = data[offset]; offset += 1
    value = data[offset:offset+length]
    return value, offset + length


def snmp_v2c_get(host, community, oid, port=SNMP_PORT, timeout=SNMP_TIMEOUT):
    """
    Send a minimal SNMP v2c GET request.
    Returns (True, value_str) on success, (False, reason) on failure.
    """
    try:
        req_id = random.randint(1, 0x7FFFFFFF)
        oid_tlv       = _tlv(0x06, _encode_oid(oid))
        varbind       = _tlv(0x30, oid_tlv + bytes([0x05, 0x00]))
        varbind_list  = _tlv(0x30, varbind)
        pdu_body      = (
            _tlv(0x02, req_id.to_bytes(4, "big")) +
            _tlv(0x02, b"\x00") +
            _tlv(0x02, b"\x00") +
            varbind_list
        )
        get_pdu   = _tlv(0xA0, pdu_body)
        message   = (
            _tlv(0x02, b"\x01") +
            _tlv(0x04, community.encode("ascii", errors="replace")) +
            get_pdu
        )
        packet = _tlv(0x30, message)

        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.settimeout(timeout)
        sock.sendto(packet, (host, port))
        resp, _ = sock.recvfrom(4096)
        sock.close()

        # Walk to varbind value in response (skip sequence/version/community/pdu header)
        # Simple heuristic: find last non-null TLV value
        try:
            _, off = _decode_string(resp, 0)    # outer sequence
            _, off = _decode_string(resp, 1)    # skip outer tag/len
            # Find OCTET STRING or INTEGER in response
            idx = resp.rfind(b"\x04")           # OCTET STRING tag
            if idx > 0:
                val, _ = _decode_string(resp, idx)
                return True, val.decode("utf-8", errors="replace").strip()
            idx = resp.rfind(b"\x02")
            if idx > 0:
                val, _ = _decode_string(resp, idx)
                return True, str(int.from_bytes(val, "big"))
        except Exception:
            pass
        return True, "(response received)"

    except socket.timeout:
        return False, "timeout"
    except Exception as ex:
        return False, str(ex)


def probe_snmp(host):
    """
    Try a list of common community strings against the switch.
    Returns list of dicts: {community, works, sysDescr, cpu_pct}
    """
    print(f"\n[SNMP] Probing {host}:{SNMP_PORT} with {len(SNMP_COMMUNITIES)} community strings...")
    results = []
    for comm in SNMP_COMMUNITIES:
        ok, val = snmp_v2c_get(host, comm, OID_SYSDESCR)
        if ok:
            print(f"  [!] Community '{comm}' WORKS — sysDescr: {val[:60]}")
            cpu_ok, cpu_val = snmp_v2c_get(host, comm, OID_CPU_5MIN)
            results.append({
                "community" : comm,
                "works"     : True,
                "sysDescr"  : val,
                "cpu_pct"   : cpu_val if cpu_ok else "N/A",
            })
        else:
            print(f"  [ ] '{comm}': {val}")
    if not results:
        print("  [+] No community string worked — SNMP access denied or disabled.")
    return results


# ─────────────────────────────────────────────────────────────
# SSH Collection (User EXEC only — no privilege 15)
# ─────────────────────────────────────────────────────────────

_PRIV_ERRORS = (
    "% invalid input", "% incomplete command",
    "% insufficient privileges", "% authorization failed",
    "% ambiguous command",
)

def _is_err(txt):
    return any(e in txt.strip()[:100].lower() for e in _PRIV_ERRORS)


COMMANDS = {
    "interfaces"    : "show interfaces",
    "int_status"    : "show interfaces status",
    "int_status_err": "show interfaces status err-disabled",
    "stp_detail"    : "show spanning-tree detail",
    "stp_summary"   : "show spanning-tree summary",
    "mac_count"     : "show mac address-table count",
    "cdp_detail"    : "show cdp neighbors detail",
    "ip_arp"        : "show ip arp",
    "storm_control" : "show storm-control",
    "version"       : "show version",
    "ip_brief"      : "show ip interface brief",
}


def collect_ssh(ip, username, password):
    device = {
        "device_type" : "cisco_ios",
        "host"        : ip,
        "username"    : username,
        "password"    : password,
        "timeout"     : 60,
        "fast_cli"    : False,
    }
    raw = {}
    print(f"\n[SSH] Connecting to {ip}...")
    try:
        with ConnectHandler(**device) as conn:
            prompt = conn.find_prompt()
            is_priv = prompt.endswith("#")
            print(f"[SSH] Connected — prompt: {prompt}  "
                  f"({'privilege 15' if is_priv else 'user EXEC — limited view'})")
            for key, cmd in COMMANDS.items():
                print(f"    → {cmd}")
                try:
                    out = conn.send_command(cmd, read_timeout=30)
                    raw[key] = "" if _is_err(out) else out
                except Exception as ex:
                    raw[key] = ""
                    print(f"      [!] {ex}")
    except NetmikoAuthenticationException:
        print("[-] Authentication failed."); sys.exit(1)
    except NetmikoTimeoutException:
        print(f"[-] Timeout connecting to {ip}"); sys.exit(1)
    except Exception as ex:
        print(f"[-] SSH error: {ex}"); sys.exit(1)
    return raw


# ─────────────────────────────────────────────────────────────
# Parsers
# ─────────────────────────────────────────────────────────────

def parse_stp_tcn(stp_detail_txt):
    """
    Extract topology change info per VLAN.
    Returns list of dicts: {vlan, changes, secs_since_last, port}
    """
    results = []
    # Split per-VLAN blocks
    blocks = re.split(r"(?=VLAN\d{4}\s+is)", stp_detail_txt)
    for block in blocks:
        m_vlan = re.search(r"VLAN(\d+)", block)
        if not m_vlan:
            continue
        vlan = int(m_vlan.group(1))

        changes = 0
        m_chg = re.search(r"Number of topology changes\s+(\d+)", block, re.IGNORECASE)
        if m_chg:
            changes = int(m_chg.group(1))

        secs_since = None
        m_sec = re.search(r"last change occurred\s+(\d+):(\d+):(\d+)\s+ago", block, re.IGNORECASE)
        if m_sec:
            h, m, s = int(m_sec.group(1)), int(m_sec.group(2)), int(m_sec.group(3))
            secs_since = h*3600 + m*60 + s

        port = ""
        m_port = re.search(r"topology change initiator\s+(\S+)", block, re.IGNORECASE)
        if not m_port:
            m_port = re.search(r"topology change sent from\s+(\S+)", block, re.IGNORECASE)
        if m_port:
            port = m_port.group(1)

        if changes > 0:
            results.append({
                "vlan": vlan, "changes": changes,
                "secs_since": secs_since, "port": port,
            })

    return sorted(results, key=lambda x: x["changes"], reverse=True)


def parse_arp(arp_txt):
    """Count ARP entries and detect duplicates (same IP, multiple MACs = IP conflict)."""
    entries = defaultdict(list)
    for line in arp_txt.splitlines():
        parts = line.split()
        # Internet  10.x.x.x   MM  aabb.ccdd.eeff  ARPA  Gix/x
        if len(parts) >= 4 and parts[0] in ("Internet",):
            ip  = parts[1]
            mac = parts[3] if len(parts) > 3 else ""
            if mac and mac != "Incomplete":
                entries[ip].append(mac)
    duplicates = {ip: macs for ip, macs in entries.items() if len(macs) > 1}
    return {"total": len(entries), "duplicates": duplicates}


def parse_cdp_loop(cdp_txt):
    """
    Detect if the same device ID appears on multiple local interfaces
    (classic sign of an L2 loop or incorrectly cabled redundant path).
    """
    # device_id -> list of local ports
    device_ports = defaultdict(list)
    blocks = re.split(r"-{10,}", cdp_txt)
    for block in blocks:
        m_dev = re.search(r"Device ID:\s*(.+)", block)
        m_port = re.search(r"Interface:\s*(\S+),", block)
        if m_dev and m_port:
            dev  = m_dev.group(1).strip()
            port = m_port.group(1).strip()
            device_ports[dev].append(port)
    loops = {dev: ports for dev, ports in device_ports.items() if len(ports) > 1}
    return loops


def parse_errdisabled(txt):
    """Extract err-disabled ports."""
    ports = []
    for line in txt.splitlines():
        if "err-disabled" in line.lower():
            parts = line.split()
            if parts:
                ports.append(parts[0])
    return ports


def parse_storm_control(txt):
    """Find ports where storm-control is active and any that are currently suppressing."""
    suppressing = []
    configured  = []
    for line in txt.splitlines():
        if re.search(r"\d+\.\d+", line):  # has a threshold value
            port_m = re.match(r"(\S+)", line)
            if port_m:
                configured.append(port_m.group(1))
            if "Suppressing" in line or "Shutdown" in line:
                suppressing.append(line.strip())
    return {"configured": configured, "suppressing": suppressing}


def parse_interfaces_broadcast(iface_txt):
    """
    Per-interface: extract broadcast input rates and error totals.
    Returns list of (name, bcast_pct_estimate, in_errors, crc)
    """
    results = []
    blocks = re.split(r"(?=^\S+\s+is\s+(?:up|down|administratively))", iface_txt, flags=re.MULTILINE)
    for block in blocks:
        m = re.match(r"^(\S+)\s+is\s+(up)", block)
        if not m:
            continue
        name = m.group(1)

        def gi(pattern):
            mx = re.search(pattern, block, re.IGNORECASE)
            return int(mx.group(1).replace(",", "")) if mx else 0

        in_pkts     = gi(r"(\d[\d,]*) packets input")
        in_bcast    = gi(r"(\d[\d,]*) broadcasts")
        in_err      = gi(r"(\d[\d,]*) input errors")
        crc         = gi(r"(\d[\d,]*) CRC")
        in_rate_bps = gi(r"input rate\s+(\d+)")   # bits/sec

        bcast_pct = round(in_bcast / in_pkts * 100, 1) if in_pkts > 1000 else 0
        results.append({
            "name": name, "bcast_pct": bcast_pct,
            "in_bcast": in_bcast, "in_pkts": in_pkts,
            "in_errors": in_err, "crc": crc,
            "in_rate_bps": in_rate_bps,
        })
    return sorted(results, key=lambda x: x["bcast_pct"], reverse=True)


# ─────────────────────────────────────────────────────────────
# Root Cause Analysis Engine
# ─────────────────────────────────────────────────────────────

class Suspicion:
    """Accumulates evidence for a root cause and produces a confidence score."""
    def __init__(self, name, icon):
        self.name     = name
        self.icon     = icon
        self.score    = 0
        self.evidence = []

    def add(self, points, text):
        self.score += points
        self.evidence.append((points, text))

    @property
    def confidence(self):
        return min(100, self.score)

    @property
    def verdict(self):
        if self.score >= 70: return "VERY LIKELY"
        if self.score >= 40: return "LIKELY"
        if self.score >= 20: return "POSSIBLE"
        return "UNLIKELY"

    @property
    def verdict_color(self):
        if self.score >= 70: return "#dc2626"
        if self.score >= 40: return "#ea580c"
        if self.score >= 20: return "#d97706"
        return "#4ade80"


def analyze(raw, stp_tcns, arp_data, cdp_loops, errdis_ports,
            storm_data, iface_bcast, snmp_hits):

    suspects = {
        "stp"   : Suspicion("STP TCN Storm",            "🌪️"),
        "bcast" : Suspicion("Broadcast / ARP Flood",    "📡"),
        "snmp"  : Suspicion("SNMP Overpolling",         "👁️"),
        "loop"  : Suspicion("L2 Loop (CDP evidence)",   "🔄"),
        "storm" : Suspicion("Storm Control / Port Meltdown", "⛈️"),
    }
    s = suspects

    # ── STP TCN Analysis ──────────────────────────────────────
    total_tcn = sum(x["changes"] for x in stp_tcns)
    if total_tcn > 1000:
        s["stp"].add(50, f"Total topology changes: {total_tcn:,} — this is not a topology, "
                        "this is a cry for help.")
    elif total_tcn > 100:
        s["stp"].add(30, f"Topology changes: {total_tcn:,} — elevated. Someone's been busy.")
    elif total_tcn > 10:
        s["stp"].add(15, f"Topology changes: {total_tcn} — slightly suspicious.")

    rapid_vlans = [v for v in stp_tcns if v["secs_since"] and v["secs_since"] < 300]
    if rapid_vlans:
        vlans_str = ", ".join(f"VLAN{v['vlan']}" for v in rapid_vlans[:5])
        s["stp"].add(40, f"Recent TCN in last 5 minutes on: {vlans_str}. "
                        "The switch is actively having an existential crisis right now.")
    for v in stp_tcns:
        if v["port"]:
            s["stp"].add(10, f"TCN originating from port {v['port']} on VLAN{v['vlan']} "
                            "— suspect device attached here.")
            s["loop"].add(15, f"Port {v['port']} is triggering topology changes — "
                             "may be a loop or a device that doesn't understand BPDUs.")

    stp_summary = raw.get("stp_summary", "")
    if not re.search(r"bpdu guard\s+enabled", stp_summary, re.IGNORECASE):
        s["stp"].add(20, "BPDU Guard is disabled globally. "
                        "So anyone can plug in a switch and become root. Great design.")
    if not re.search(r"portfast\s+default", stp_summary, re.IGNORECASE):
        s["stp"].add(10, "PortFast not set as default. "
                        "Every new device causes STP to think about its life choices for 30 seconds.")

    # ── Broadcast / ARP Flood ─────────────────────────────────
    high_bcast_ifaces = [i for i in iface_bcast if i["bcast_pct"] > 30]
    if high_bcast_ifaces:
        top = high_bcast_ifaces[0]
        s["bcast"].add(50, f"Port {top['name']}: {top['bcast_pct']}% broadcast traffic. "
                          "That's not a switch port, that's a broadcast cannon.")
    mid_bcast = [i for i in iface_bcast if 10 < i["bcast_pct"] <= 30]
    if mid_bcast:
        s["bcast"].add(25, f"{len(mid_bcast)} port(s) between 10–30% broadcast traffic. "
                          "Someone's network is very chatty.")

    if arp_data["total"] > 2000:
        s["bcast"].add(30, f"ARP table has {arp_data['total']:,} entries. "
                          "Either you have a very, very large network, or something is very wrong.")
    elif arp_data["total"] > 500:
        s["bcast"].add(15, f"ARP table: {arp_data['total']} entries — worth monitoring.")

    if arp_data["duplicates"]:
        dupes = list(arp_data["duplicates"].items())[:3]
        dupe_str = "; ".join(f"{ip}: {macs}" for ip, macs in dupes)
        s["bcast"].add(40, f"IP ADDRESS CONFLICTS DETECTED: {dupe_str}. "
                          "Two devices think they're the same IP. They're both wrong. "
                          "This causes ARP storms and constant MAC table updates.")
        s["loop"].add(20, "Duplicate ARP entries can indicate an L2 loop "
                         "where the same frame arrives on multiple paths.")

    # ── SNMP Overpolling ──────────────────────────────────────
    if snmp_hits:
        hit_comms = [h["community"] for h in snmp_hits]
        s["snmp"].add(60, f"SNMP responds to community string(s): {', '.join(hit_comms)}. "
                         "Your switch is more open with its stats than your colleague "
                         "is with bad news.")
        if any(h["community"] in ("public", "private") for h in snmp_hits):
            s["snmp"].add(30, "Default community strings 'public'/'private' work. "
                             "Whoever configured this switch clearly read zero security guidelines. "
                             "Any device on the network can poll CPU/MIB data.")
        cpu_vals = [h["cpu_pct"] for h in snmp_hits if h["cpu_pct"] != "N/A"]
        if cpu_vals:
            s["snmp"].add(20, f"SNMP CPU read via OID: {cpu_vals[0]}% — "
                             "this confirms SNMP access is fully open.")
    else:
        s["snmp"].add(5, "No common community strings worked — SNMP is either "
                        "disabled or not using the obvious defaults. "
                        "10 points for your security team.")

    # ── L2 Loop (CDP) ─────────────────────────────────────────
    if cdp_loops:
        for dev, ports in cdp_loops.items():
            port_str = ", ".join(ports)
            s["loop"].add(60, f"Device '{dev}' seen on multiple local ports: {port_str}. "
                             "This is either a loop, or your switch has developed "
                             "feelings for this neighbor and wants to see it twice.")
    if errdis_ports:
        s["loop"].add(30, f"{len(errdis_ports)} port(s) in err-disabled state: "
                         f"{', '.join(errdis_ports[:5])}. "
                         "These ports looked into the abyss and blinked first.")
        s["storm"].add(25, f"Err-disabled ports usually mean storm-control or "
                          "security violation triggered. Something caused a storm.")

    # ── Storm Control ─────────────────────────────────────────
    if storm_data["suppressing"]:
        s["storm"].add(70, f"Storm control is ACTIVELY SUPPRESSING traffic on "
                          f"{len(storm_data['suppressing'])} port(s). "
                          "The switch is currently fighting a battle. Possibly losing.")
        s["bcast"].add(30, "Active storm suppression = active broadcast storm. "
                          "These two facts are related. Directly.")
    if storm_data["configured"]:
        s["storm"].add(10, f"Storm control configured on {len(storm_data['configured'])} port(s) — "
                          "at least someone thought about this at some point.")

    # ── Cross-correlations ────────────────────────────────────
    if s["stp"].score >= 30 and s["loop"].score >= 30:
        s["loop"].add(15, "High STP TCN count + CDP loop evidence: "
                         "these two usually don't happen independently. "
                         "L2 loop is the most probable combined explanation.")

    if s["bcast"].score >= 30 and s["stp"].score >= 30:
        s["bcast"].add(20, "High broadcast + high TCN: STP MAC table flush "
                          "is causing broadcast flooding. The loop feeds the storm, "
                          "the storm feeds the CPU. It's the circle of pain.")

    ranked = sorted(suspects.values(), key=lambda x: x.score, reverse=True)
    return ranked


# ─────────────────────────────────────────────────────────────
# HTML Report
# ─────────────────────────────────────────────────────────────

def e(v, fb="—"):
    return html_mod.escape(str(v) if v is not None else fb)


SARCASTIC_VERDICT = {
    "VERY LIKELY" : ("Guilty as charged", "#dc2626"),
    "LIKELY"      : ("Strong suspect", "#ea580c"),
    "POSSIBLE"    : ("Worth a look", "#d97706"),
    "UNLIKELY"    : ("Probably innocent", "#4ade80"),
}


def generate_html(stp_tcns, arp_data, cdp_loops, errdis_ports,
                  storm_data, iface_bcast, snmp_hits, ranked, switch_ver):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    hostname = re.search(r"^(\S+)\s+uptime", switch_ver, re.MULTILINE)
    hostname = hostname.group(1) if hostname else SWITCH_IP

    # ── Suspect cards ─────────────────────────────────────────
    suspect_cards = ""
    for s in ranked:
        verd_label, verd_color = SARCASTIC_VERDICT.get(s.verdict, (s.verdict, "#94a3b8"))
        bar_w = min(100, s.confidence)
        bar_c = verd_color
        ev_rows = "".join(
            f'<tr><td style="color:#d97706;font-size:.75rem;padding:4px 0">+{pts}</td>'
            f'<td style="font-size:.8rem;color:#cbd5e1;padding:4px 0 4px 10px">{e(txt)}</td></tr>'
            for pts, txt in s.evidence
        ) or f'<tr><td colspan="2" style="color:#475569;font-size:.8rem">No incriminating evidence. Suspicious in itself.</td></tr>'

        suspect_cards += f"""
<div class="scard" style="border-left-color:{verd_color}">
  <div class="shead">
    <span style="font-size:1.5rem">{s.icon}</span>
    <div style="flex:1">
      <div style="font-weight:800;font-size:1rem;color:#f1f5f9">{e(s.name)}</div>
      <div style="font-size:.75rem;color:{verd_color};font-weight:700;margin-top:2px">{verd_label}</div>
    </div>
    <div style="text-align:right">
      <div style="font-size:2rem;font-weight:900;color:{verd_color};line-height:1">{s.confidence}</div>
      <div style="font-size:.65rem;color:#475569">suspicion score</div>
    </div>
  </div>
  <div style="background:#0f172a;border-radius:4px;height:8px;margin:10px 0">
    <div style="width:{bar_w}%;height:100%;background:{bar_c};border-radius:4px;transition:width .3s"></div>
  </div>
  <table style="width:100%;border-collapse:collapse;margin-top:6px">{ev_rows}</table>
</div>"""

    # ── Top culprit verdict ───────────────────────────────────
    top = ranked[0] if ranked else None
    if top and top.score >= 20:
        verdict_box = f"""
<div style="background:#1e293b;border:2px solid {top.verdict_color};border-radius:14px;
     padding:22px 28px;margin-bottom:26px">
  <div style="font-size:.75rem;color:#64748b;text-transform:uppercase;
       letter-spacing:.1em;margin-bottom:6px">Primary Suspect</div>
  <div style="font-size:1.6rem;font-weight:900;color:{top.verdict_color}">
    {top.icon} {e(top.name)}</div>
  <div style="font-size:.85rem;color:#94a3b8;margin-top:8px">
    Suspicion score: <strong style="color:{top.verdict_color}">{top.confidence}/100</strong>
    &nbsp;·&nbsp; Verdict: <strong style="color:{top.verdict_color}">{top.verdict}</strong>
  </div>
  <div style="font-size:.82rem;color:#64748b;margin-top:6px;font-style:italic">
    "The evidence points here. Whether anyone fixes it is a separate philosophical question."
  </div>
</div>"""
    else:
        verdict_box = """
<div style="background:#1e293b;border:1px solid #334155;border-radius:14px;padding:22px 28px;margin-bottom:26px">
  <div style="color:#94a3b8">Not enough evidence collected to make a confident verdict.
  Either the switch is actually fine, or the data available at user EXEC level
  isn't enough to catch the culprit. Classic.</div>
</div>"""

    # ── STP TCN table ─────────────────────────────────────────
    stp_rows = ""
    for v in stp_tcns[:15]:
        age = f"{v['secs_since']//3600}h {(v['secs_since']%3600)//60}m ago" if v["secs_since"] else "Unknown"
        warn = "🔥" if (v["secs_since"] and v["secs_since"] < 300) else ""
        stp_rows += (f"<tr><td>VLAN{v['vlan']}</td><td>{v['changes']:,} {warn}</td>"
                     f"<td>{age}</td><td>{e(v['port']) or '—'}</td></tr>")
    if not stp_rows:
        stp_rows = '<tr><td colspan="4" class="muted">No topology changes recorded. STP is having a peaceful day.</td></tr>'

    # ── SNMP results table ────────────────────────────────────
    snmp_rows = ""
    for h in snmp_hits:
        snmp_rows += (f"<tr><td style='color:#f87171;font-weight:700'>{e(h['community'])}</td>"
                      f"<td style='color:#fca5a5'>RESPONDS</td>"
                      f"<td class='mono'>{e(h['sysDescr'][:80])}</td>"
                      f"<td>{e(h['cpu_pct'])}</td></tr>")
    for comm in SNMP_COMMUNITIES:
        if not any(h["community"] == comm for h in snmp_hits):
            snmp_rows += (f"<tr><td style='color:#475569'>{e(comm)}</td>"
                          f"<td style='color:#4ade80'>silent</td>"
                          f"<td class='muted'>—</td><td>—</td></tr>")
    if not snmp_rows:
        snmp_rows = '<tr><td colspan="4" class="muted">No data</td></tr>'

    # ── Interface broadcast table ─────────────────────────────
    bcast_rows = ""
    for iface in [i for i in iface_bcast if i["bcast_pct"] > 0][:20]:
        bc = iface["bcast_pct"]
        clr = "#dc2626" if bc > 30 else "#d97706" if bc > 10 else "#94a3b8"
        bcast_rows += (f"<tr><td>{e(iface['name'])}</td>"
                       f"<td style='color:{clr}'>{bc}%</td>"
                       f"<td>{iface['in_bcast']:,}</td>"
                       f"<td>{iface['in_pkts']:,}</td>"
                       f"<td>{iface['in_errors']:,}</td>"
                       f"<td>{iface['crc']:,}</td></tr>")
    if not bcast_rows:
        bcast_rows = '<tr><td colspan="6" class="muted">No broadcast data (or all ports are behaving themselves).</td></tr>'

    # ── CDP loops table ───────────────────────────────────────
    cdp_rows = ""
    for dev, ports in cdp_loops.items():
        cdp_rows += (f"<tr><td style='color:#f87171;font-weight:700'>{e(dev)}</td>"
                     f"<td>{e(', '.join(ports))}</td>"
                     f"<td style='color:#f87171'>POTENTIAL LOOP</td></tr>")
    if not cdp_rows:
        cdp_rows = '<tr><td colspan="3" class="muted">No CDP loop evidence. Cables are going to the right places. Probably.</td></tr>'

    # ── ARP duplicates ────────────────────────────────────────
    arp_rows = ""
    for ip, macs in list(arp_data["duplicates"].items())[:10]:
        arp_rows += (f"<tr><td style='color:#f87171'>{e(ip)}</td>"
                     f"<td style='color:#fca5a5'>{e(', '.join(macs))}</td>"
                     f"<td style='color:#f87171'>IP CONFLICT</td></tr>")
    if not arp_rows:
        arp_rows = '<tr><td colspan="3" class="muted">No duplicate ARP entries. IP addressing is surprisingly consistent.</td></tr>'

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>CPU Root-Cause — {e(hostname)}</title>
<style>
:root{{--bg:#0f172a;--card:#1e293b;--border:#334155;--text:#e2e8f0;--muted:#94a3b8}}
*{{box-sizing:border-box;margin:0;padding:0}}
body{{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;
     background:var(--bg);color:var(--text);padding:28px;line-height:1.5}}
h1{{font-size:1.75rem;font-weight:800;color:#f1f5f9}}
h2{{font-size:1.05rem;font-weight:700;color:#cbd5e1;margin:32px 0 14px;
   padding-bottom:6px;border-bottom:1px solid var(--border)}}
.header{{display:flex;align-items:center;justify-content:space-between;
        padding:22px 28px;background:var(--card);border:1px solid var(--border);
        border-radius:14px;margin-bottom:26px}}
.meta{{font-size:.78rem;color:var(--muted);margin-top:4px}}
.suspects{{display:grid;grid-template-columns:repeat(auto-fit,minmax(340px,1fr));gap:16px;margin-bottom:26px}}
.scard{{background:var(--card);border-left:4px solid #334155;border-radius:12px;padding:18px 20px}}
.shead{{display:flex;align-items:center;gap:12px;margin-bottom:4px}}
.tw{{background:var(--card);border:1px solid var(--border);border-radius:12px;overflow:auto;margin-bottom:26px}}
table{{width:100%;border-collapse:collapse;font-size:.8rem}}
th,td{{padding:9px 12px;text-align:left;border-bottom:1px solid var(--border);white-space:nowrap}}
th{{background:#162032;color:var(--muted);font-weight:700;font-size:.7rem;
   text-transform:uppercase;letter-spacing:.05em}}
tr:last-child td{{border-bottom:none}}
tr:hover td{{background:rgba(255,255,255,.025)}}
.muted{{color:var(--muted)!important;font-style:italic}}
.mono{{font-family:monospace;font-size:.75rem;word-break:break-all;white-space:normal}}
.warn-box{{background:#78350f;border:1px solid #92400e;border-radius:10px;
          padding:14px 20px;margin-bottom:20px;font-size:.84rem;color:#fef3c7}}
footer{{text-align:center;color:var(--muted);font-size:.72rem;
       margin-top:44px;padding-top:18px;border-top:1px solid var(--border)}}
</style>
</head>
<body>

<div class="header">
  <div>
    <h1>CPU Root-Cause Investigator</h1>
    <div class="meta">
      {e(hostname)} &nbsp;|&nbsp; {e(SWITCH_IP)} &nbsp;|&nbsp;
      User EXEC mode (privilege 1) &nbsp;|&nbsp; {ts}
    </div>
    <div class="meta" style="margin-top:4px;font-style:italic;color:#475569">
      "We don't have privilege 15, but we have determination. And sarcasm."
    </div>
  </div>
  <div style="font-size:2.4rem">🕵️</div>
</div>

<div class="warn-box">
  <strong>⚠ User EXEC only (privilege 1)</strong> — CPU process list unavailable.
  Root-cause analysis is based on: STP topology changes, interface broadcast rates,
  ARP table, CDP neighbors, storm-control, and external SNMP probe.
  If you want the <em>actual</em> culprit process name, someone needs to grant privilege 15.
  Just saying.
</div>

{verdict_box}

<h2>Suspect Ranking — Who Probably Killed Your CPU</h2>
<div class="suspects">
{suspect_cards}
</div>

<h2>STP Topology Changes — The Chaos Ledger</h2>
<div class="tw"><table>
  <thead><tr><th>VLAN</th><th>Total Changes</th><th>Last Change</th><th>Originating Port</th></tr></thead>
  <tbody>{stp_rows}</tbody>
</table></div>

<h2>SNMP External Probe — How Open Is This Switch Really?</h2>
<div class="tw"><table>
  <thead><tr><th>Community String</th><th>Result</th><th>sysDescr</th><th>CPU (OID)</th></tr></thead>
  <tbody>{snmp_rows}</tbody>
</table></div>

<h2>Broadcast Traffic per Interface — The Spray-and-Pray Report</h2>
<div class="tw"><table>
  <thead><tr>
    <th>Interface</th><th>Broadcast %</th><th>Broadcast Pkts</th>
    <th>Total Input Pkts</th><th>Input Errors</th><th>CRC</th>
  </tr></thead>
  <tbody>{bcast_rows}</tbody>
</table></div>

<h2>CDP Neighbor Loop Detection — Did Someone Plug a Cable Into Itself?</h2>
<div class="tw"><table>
  <thead><tr><th>Device ID</th><th>Seen on Local Ports</th><th>Assessment</th></tr></thead>
  <tbody>{cdp_rows}</tbody>
</table></div>

<h2>ARP Table — IP Address Disputes</h2>
<p style="font-size:.82rem;color:var(--muted);margin-bottom:10px">
  Total ARP entries: <strong style="color:#38bdf8">{arp_data['total']:,}</strong>
  &nbsp;·&nbsp; IP conflicts: <strong style="color:{'#f87171' if arp_data['duplicates'] else '#4ade80'}">{len(arp_data['duplicates'])}</strong>
</p>
<div class="tw"><table>
  <thead><tr><th>IP Address</th><th>MAC Addresses (duplicate)</th><th>Verdict</th></tr></thead>
  <tbody>{arp_rows}</tbody>
</table></div>

<h2>Err-Disabled Ports — The Ports That Gave Up</h2>
<p style="font-size:.82rem;color:var(--muted);margin-bottom:10px">
{'<span style="color:#f87171">⚠ ' + str(len(errdis_ports)) + ' port(s) in err-disabled: ' +
 e(', '.join(errdis_ports[:10])) + '</span>'
 if errdis_ports else
 '<span style="color:#4ade80">No err-disabled ports. Someone configured this switch correctly. Surprising.</span>'}
</p>

<h2>Storm Control Status — Active Suppression?</h2>
<p style="font-size:.82rem;color:var(--muted);margin-bottom:6px">
  Ports with storm-control configured: <strong>{len(storm_data['configured'])}</strong>
</p>
{'<div style="background:#7f1d1d;border:1px solid #991b1b;border-radius:8px;padding:12px 16px;font-size:.82rem;color:#fca5a5"><strong>⛈ ACTIVE SUPPRESSION on:</strong><br>' + '<br>'.join(e(l) for l in storm_data['suppressing']) + '</div>' if storm_data['suppressing'] else '<p style="font-size:.82rem;color:#4ade80">No active storm suppression. Either the storm passed, or there never was one.</p>'}

<h2>Next Steps — What To Do Now</h2>
<div style="background:var(--card);border:1px solid var(--border);border-radius:12px;padding:20px 24px;margin-bottom:26px">
  <ol style="font-size:.85rem;color:var(--muted);padding-left:20px;line-height:2.4">
    <li><strong style="color:#f1f5f9">Get privilege 15 on this switch</strong> — run
        <code>show processes cpu sorted</code> and know <em>exactly</em> which process is
        eating CPU. Everything else is detective work with a blindfold.</li>
    <li><strong style="color:#f1f5f9">Fix STP first if TCN score is high</strong> —
        <code>spanning-tree portfast default</code> +
        <code>spanning-tree portfast bpduguard default</code>.
        This one change resolves 60% of "switch is slow" tickets.</li>
    <li><strong style="color:#f1f5f9">Change SNMP community strings immediately</strong> if
        any hit above — set ACL on SNMP access:
        <code>snmp-server community NEWSTRING ro ACL_SNMP</code>.</li>
    <li><strong style="color:#f1f5f9">Investigate CDP loop ports</strong> —
        physically trace the cable on any port appearing on multiple interfaces.
        Spoiler: someone created a loop.</li>
    <li><strong style="color:#f1f5f9">Clear err-disabled ports after fixing root cause</strong> —
        <code>shutdown</code> then <code>no shutdown</code> — but only after you know
        <em>why</em> they went err-disabled. Re-enabling a storm port is how you get
        back to square one.</li>
    <li><strong style="color:#f1f5f9">Resolve ARP conflicts</strong> if any found —
        duplicate IPs cause constant ARP broadcasts and MAC table churn.
        Find both devices and fix static IPs or DHCP exclusions.</li>
  </ol>
</div>

<footer>
  Cisco IOS/IOS-XE CPU Root-Cause Investigator &nbsp;|&nbsp;
  {e(hostname)} ({e(SWITCH_IP)}) &nbsp;|&nbsp; {ts}<br>
  <span style="font-style:italic">"The network doesn't lie. People do."</span>
</footer>
</body>
</html>"""


# ─────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────

def main():
    print("=" * 62)
    print("  Cisco IOS/IOS-XE CPU Root-Cause Investigator")
    print(f"  Target : {SWITCH_IP}  |  User: {USERNAME}")
    print(f"  Output : {OUTPUT_HTML}")
    print("  Tone   : Sarcastic. You're welcome.")
    print("=" * 62)

    # Phase 1 — SSH collection
    raw = collect_ssh(SWITCH_IP, USERNAME, PASSWORD)

    # Phase 2 — External SNMP probe (no SSH required)
    snmp_hits = probe_snmp(SWITCH_IP)

    # Phase 3 — Parse
    print("\n[*] Parsing...")
    stp_tcns    = parse_stp_tcn(raw.get("stp_detail", ""))
    arp_data    = parse_arp(raw.get("ip_arp", ""))
    cdp_loops   = parse_cdp_loop(raw.get("cdp_detail", ""))
    errdis      = parse_errdisabled(raw.get("int_status_err", ""))
    storm_data  = parse_storm_control(raw.get("storm_control", ""))
    iface_bcast = parse_interfaces_broadcast(raw.get("interfaces", ""))
    switch_ver  = raw.get("version", "")

    print(f"    STP VLANs with changes : {len(stp_tcns)}")
    print(f"    ARP entries            : {arp_data['total']}  ({len(arp_data['duplicates'])} conflicts)")
    print(f"    CDP loops detected     : {len(cdp_loops)}")
    print(f"    Err-disabled ports     : {len(errdis)}")
    print(f"    Storm suppressing ports: {len(storm_data['suppressing'])}")
    print(f"    SNMP communities hit   : {len(snmp_hits)}")

    # Phase 4 — Analyze
    print("\n[*] Analyzing suspects...")
    ranked = analyze(raw, stp_tcns, arp_data, cdp_loops, errdis,
                     storm_data, iface_bcast, snmp_hits)

    for s in ranked:
        print(f"    {s.icon} {s.name:<35} score={s.score:>3}  [{s.verdict}]")

    # Phase 5 — Report
    print("\n[*] Generating HTML report...")
    html = generate_html(stp_tcns, arp_data, cdp_loops, errdis,
                         storm_data, iface_bcast, snmp_hits, ranked, switch_ver)

    with open(OUTPUT_HTML, "w", encoding="utf-8") as fh:
        fh.write(html)

    top = ranked[0] if ranked else None
    print("=" * 62)
    print(f"  Report  : {OUTPUT_HTML}")
    if top:
        print(f"  Verdict : {top.icon} {top.name} — {top.verdict} (score: {top.score})")
    print("=" * 62)


if __name__ == "__main__":
    main()
