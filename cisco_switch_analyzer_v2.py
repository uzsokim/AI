#!/usr/bin/env python3
"""
Cisco IOS / IOS-XE Switch Performance Analytics (v2)
SSH-based collection -> HTML report with findings & recommendations.

Author: Gemini Code Assist
Version: 2.0

Improvements:
- Class-based structure for better organization.
- Command-line arguments for IP, user, and output file.
- Added environment checks (Power Supplies, Fans).
- Enhanced HTML report with environment status.

Requirements:
    pip install netmiko
"""

import sys
import getpass
import re
import html as html_mod
import argparse
from datetime import datetime

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

try:
    from netmiko import ConnectHandler, NetmikoTimeoutException, NetmikoAuthenticationException
except ImportError:
    print("ERROR: netmiko library not found. Please run: pip install netmiko")
    sys.exit(1)


class CiscoSwitchAnalyzer:
    """Analyzes a Cisco switch for performance issues via SSH."""

    # Commands available from USER EXEC (privilege 1, prompt ">")
    COMMANDS_USER = {
        "version": "show version",
        "interfaces": "show interfaces",
        "int_status": "show interfaces status",
        "stp_summary": "show spanning-tree summary",
        "stp_detail": "show spanning-tree detail",
        "mac_count": "show mac address-table count",
        "mac_aging": "show mac address-table aging-time",
        "inventory": "show inventory",
        "ip_brief": "show ip interface brief",
        "cdp_neighbors": "show cdp neighbors detail",
    }

    # Commands that require PRIVILEGED EXEC (privilege 15, prompt "#")
    COMMANDS_PRIV = {
        "cpu_sorted": "show processes cpu sorted",
        "cpu_history": "show processes cpu history",
        "memory_sorted": "show processes memory sorted",
        "memory_stats": "show memory statistics",
        "int_counters": "show interfaces counters errors",
        "logging": "show logging | last 60",
        "environment": "show environment all",
    }

    # Error indicators returned when a command is not accessible
    _PRIV_ERRORS = (
        "% invalid input",
        "% incomplete command",
        "% insufficient privileges",
        "% authorization failed",
        "% ambiguous command",
    )

    def __init__(self, ip, username, password, output_html):
        self.ip = ip
        self.username = username
        self.password = password
        self.output_html = output_html
        self.raw_data = {}
        self.parsed_data = {}
        self.findings = []

    def _is_error(self, output: str) -> bool:
        """Return True if the command output is an IOS privilege/syntax error."""
        first = output.strip()[:120].lower()
        return any(e in first for e in self._PRIV_ERRORS)

    def _collect_data(self):
        """Connects to the switch and collects data by running show commands."""
        device = {
            "device_type": "cisco_ios",
            "host": self.ip,
            "username": self.username,
            "password": self.password,
            "timeout": 60,
            "fast_cli": False,
        }
        errors = []
        priv_level = 1

        print(f"\n[*] Connecting to {self.ip} via SSH...")
        try:
            with ConnectHandler(**device) as conn:
                prompt = conn.find_prompt()
                is_privileged = prompt.endswith("#")
                priv_level = 15 if is_privileged else 1
                print(f"[+] Connected — prompt: {prompt} "
                      f"(privilege {'15 — full access' if is_privileged else '1 — user EXEC, limited commands'})")

                if not is_privileged:
                    print("    [!] User EXEC mode: privileged commands will be skipped")

                all_cmds = dict(self.COMMANDS_USER)
                if is_privileged:
                    all_cmds.update(self.COMMANDS_PRIV)

                for key, cmd in all_cmds.items():
                    print(f"    → {cmd}")
                    try:
                        out = conn.send_command(cmd, read_timeout=45)
                        if self._is_error(out):
                            print(f"      [!] Skipped (privilege error): {out.strip()[:80]}")
                            self.raw_data[key] = ""
                            errors.append(f"{cmd}: privilege denied")
                        else:
                            self.raw_data[key] = out
                    except Exception as exc:
                        self.raw_data[key] = ""
                        errors.append(f"{cmd}: {exc}")
        except NetmikoAuthenticationException:
            print("[-] Authentication failed. Please check username and password.")
            sys.exit(1)
        except NetmikoTimeoutException:
            print(f"[-] Connection timed out to {self.ip}. Check network connectivity and firewall rules.")
            sys.exit(1)
        except Exception as e:
            print(f"[-] Connection error: {e}")
            sys.exit(1)

        if errors:
            print(f"\n[!] {len(errors)} command error(s):")
            for err in errors:
                print(f"    {err}")

        self.raw_data["_priv_level"] = priv_level

    def _parse_data(self):
        """Parses the raw command outputs into structured data."""
        print("\n[*] Parsing collected data...")
        self.parsed_data = {
            "switch_info": self._parse_version(self.raw_data.get("version", "")),
            "cpu": self._parse_cpu(self.raw_data.get("cpu_sorted", "")),
            "memory": self._parse_memory(self.raw_data.get("memory_sorted", "") + self.raw_data.get("memory_stats", "")),
            "interfaces": self._parse_interfaces(self.raw_data.get("interfaces", "")),
            "stp": self._parse_stp_summary(self.raw_data.get("stp_summary", "") + self.raw_data.get("stp_detail", "")),
            "mac": self._parse_mac_count(self.raw_data.get("mac_count", "")),
            "log_issues": self._parse_log_issues(self.raw_data.get("logging", "")),
            "environment": self._parse_environment(self.raw_data.get("environment", "")),
        }

    def _analyze_data(self):
        """Analyzes parsed data to find potential issues."""
        print("[*] Analyzing for performance issues...")
        findings = []
        cpu = self.parsed_data["cpu"]
        mem = self.parsed_data["memory"]
        ifaces = self.parsed_data["interfaces"]
        stp = self.parsed_data["stp"]
        mac = self.parsed_data["mac"]
        logs = self.parsed_data["log_issues"]
        env = self.parsed_data["environment"]

        def finding(sev, area, title, detail, recommendation):
            return {"sev": sev, "area": area, "title": title, "detail": detail, "rec": recommendation}

        # CPU
        if cpu["five_min"] >= 90:
            findings.append(finding("critical", "CPU", f"CPU utilization critical: {cpu['five_min']}% (5-min avg)", "Sustained CPU above 90% causes packet drops, slow CLI, and protocol timeouts.", "Identify top process. Common causes: broadcast storm, routing instability, ACLs, frequent SNMP polling."))
        elif cpu["five_min"] >= 70:
            findings.append(finding("high", "CPU", f"CPU utilization high: {cpu['five_min']}% (5-min avg)", "CPU above 70% for extended periods risks protocol adjacency drops.", "Profile top processes. Check for STP TCN storms or excessive ARP/broadcast traffic."))

        # Memory
        pct = mem.get("processor", {}).get("pct", 0)
        if pct >= 85:
            findings.append(finding("critical", "Memory", f"Processor memory critical: {pct}% used", "Memory above 85% risks IOS crashes and unpredictable behavior.", "Check for memory leaks with 'show processes memory sorted'. Consider a software upgrade or DRAM increase."))

        # Interfaces
        half_duplex_up = [name for name, iface in ifaces.items() if iface["link"] == "up" and "half" in iface["duplex"].lower()]
        if half_duplex_up:
            findings.append(finding("high", "Interfaces", f"Half-duplex on {len(half_duplex_up)} active port(s)", f"Ports in half-duplex: {', '.join(half_duplex_up[:5])}. This causes collisions and severe performance degradation.", "Set explicit 'duplex full' and 'speed' on both ends of the link. Never use 'auto' on trunks."))

        high_error_ifaces = [(n, i["input_errors"] + i["crc"] + i["output_errors"]) for n, i in ifaces.items() if (i["input_errors"] + i["crc"] + i["output_errors"]) > 1000]
        if high_error_ifaces:
            top = sorted(high_error_ifaces, key=lambda x: x[1], reverse=True)[:5]
            findings.append(finding("high", "Interfaces", f"{len(high_error_ifaces)} port(s) with >1000 errors", f"High error counts indicate Layer 1 issues. Top offenders: {'; '.join(f'{n} ({e} err)' for n, e in top)}", "Check cabling, SFP modules, and duplex settings. Use 'show int ... counters errors' to investigate."))

        # Spanning Tree
        if stp["tcn_events"] > 5:
            findings.append(finding("high", "Spanning Tree", f"High TCN activity: {stp['tcn_events']} events", "Excessive TCNs flush the MAC table, causing temporary flooding and high CPU.", "Enable 'spanning-tree portfast' on all access ports and 'bpduguard enable' to prevent TCNs from endpoints."))
        if not stp["bpdu_guard"]:
            findings.append(finding("high", "Spanning Tree", "BPDU Guard not enabled globally", "A rogue switch can trigger a topology change and disrupt the network.", "Apply globally: 'spanning-tree portfast bpduguard default'."))

        # MAC Table
        if mac["max"] > 0 and (mac["total"] / mac["max"] * 100) >= 80:
            fill_pct = round(mac["total"] / mac["max"] * 100, 1)
            findings.append(finding("critical", "MAC Table", f"CAM table {fill_pct}% full", "When the CAM table is full, the switch floods unknown unicast traffic, acting like a hub.", "Investigate source of MACs. Enable 'port-security' to limit MACs per port."))

        # Environment
        for psu in env.get("power", []):
            if "ok" not in psu["status"].lower() and "normal" not in psu["status"].lower():
                findings.append(finding("critical", "Environment", f"Power Supply Fault: {psu['name']} status is {psu['status']}", "A failing PSU can lead to an unexpected switch shutdown. Redundancy is lost.", "Inspect the physical PSU immediately. Check power cables and replace the faulty unit if necessary."))
        for fan in env.get("fans", []):
            if "ok" not in fan["status"].lower() and "normal" not in fan["status"].lower():
                findings.append(finding("high", "Environment", f"Fan Fault: {fan['name']} status is {fan['status']}", "A fan failure can cause overheating, leading to performance issues or hardware damage.", "Check for obstructions. Replace the faulty fan module. Monitor temperature with 'show env temp'."))

        self.findings = findings

    def _generate_report(self):
        """Generates a self-contained HTML report."""
        print("[*] Generating HTML report...")

        SEV_STYLE = {"critical": ("#dc2626", "CRITICAL"), "high": ("#ea580c", "HIGH"), "warning": ("#d97706", "WARNING"), "info": ("#2563eb", "INFO")}
        SEV_ORDER = {"critical": 0, "high": 1, "warning": 2, "info": 3}

        def e(v, fb="—"): return html_mod.escape(str(v) if v is not None else fb)
        def badge(sev):
            color, label = SEV_STYLE.get(sev, ("#6b7280", sev.upper()))
            return f'<span style="display:inline-block;padding:2px 10px;border-radius:999px;font-size:.68rem;font-weight:700;color:#fff;background:{color}">{label}</span>'

        # Score
        c = {"critical": 0, "high": 0, "warning": 0, "info": 0}
        for f in self.findings: c[f["sev"]] = c.get(f["sev"], 0) + 1
        score = max(0, 100 - c["critical"] * 20 - c["high"] * 10 - c["warning"] * 4 - c["info"] * 1)
        score_color = "#16a34a" if score >= 80 else "#d97706" if score >= 60 else "#dc2626"
        score_label = "Healthy" if score >= 80 else "Needs Attention" if score >= 60 else "Critical"

        # Data shortcuts
        info = self.parsed_data["switch_info"]
        cpu = self.parsed_data["cpu"]
        mem = self.parsed_data["memory"]
        ifaces = self.parsed_data["interfaces"]
        stp = self.parsed_data["stp"]
        mac = self.parsed_data["mac"]
        env = self.parsed_data["environment"]

        # Finding cards
        cards = "".join(
            f"""<div class="fcard {f['sev']}">
              <div class="fhead">{badge(f['sev'])} <span class="ftitle">{e(f['title'])}</span></div>
              <div class="fbody"><p><strong>Detail:</strong> {e(f['detail'])}</p><p class="rec"><strong>Recommendation:</strong> {e(f['rec'])}</p></div>
            </div>"""
            for f in sorted(self.findings, key=lambda x: SEV_ORDER.get(x["sev"], 9))
        )

        # CPU process table
        cpu_rows = "".join(f"<tr><td>{e(p['pid'])}</td><td>{e(p['name'])}</td><td>{p['five_sec']}%</td><td>{p['one_min']}%</td><td>{p['five_min']}%</td></tr>" for p in cpu["processes"])

        # Interface table
        iface_rows = "".join(
            f"""<tr><td>{e(name)}</td>
                   <td style='color:{"#4ade80" if iface["link"] == "up" else "#f87171"}'>{e(iface['link'])}</td>
                   <td>{e(iface['description'][:30])}</td>
                   <td style='color:{"#f87171" if "half" in iface["duplex"].lower() else "#94a3b8"}'>{e(iface['duplex'])}</td>
                   <td>{e(iface['speed'])}</td>
                   <td style='color:{"#dc2626" if (iface["input_errors"] + iface["crc"]) > 1000 else "#d97706" if (iface["input_errors"] + iface["crc"]) > 10 else "#94a3b8"}'>{iface['input_errors']:,}</td>
                   <td style='color:{"#dc2626" if iface["crc"] > 100 else "#94a3b8"}'>{iface['crc']:,}</td>
                   <td>{iface['drops']:,}</td>
                   <td>{iface['resets']:,}</td></tr>"""
            for name, iface in sorted(ifaces.items(), key=lambda kv: kv[1]["input_errors"] + kv[1]["crc"], reverse=True)[:40]
        )

        # Environment status
        power_html = "".join(f"""<div class="metric"><label>{e(psu['name'])}</label><span style='color:{"#4ade80" if "ok" in psu["status"].lower() or "normal" in psu["status"].lower() else "#dc2626"};font-weight:700;'>{e(psu['status'])}</span></div>""" for psu in env.get("power", []))
        if not power_html: power_html = '<div class="metric"><label>Power Supplies</label><span class="muted">No data</span></div>'
        fan_html = "".join(f"""<div class="metric"><label>{e(fan['name'])}</label><span style='color:{"#4ade80" if "ok" in fan["status"].lower() or "normal" in fan["status"].lower() else "#dc2626"};font-weight:700;'>{e(fan['status'])}</span></div>""" for fan in env.get("fans", []))
        if not fan_html: fan_html = '<div class="metric"><label>Fans</label><span class="muted">No data</span></div>'

        html_template = f"""
<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8"><title>Switch Analytics - {e(info.get("hostname"))}</title><style>
body{{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;background:#0f172a;color:#e2e8f0;padding:28px;line-height:1.5}}
h1{{font-size:1.75rem;font-weight:800;color:#f1f5f9}} h2{{font-size:1.1rem;font-weight:700;color:#cbd5e1;margin:32px 0 14px;padding-bottom:6px;border-bottom:1px solid #334155}}
.header{{display:flex;align-items:center;justify-content:space-between;padding:24px 28px;background:#1e293b;border:1px solid #334155;border-radius:14px;margin-bottom:26px}}
.header-meta{{font-size:.78rem;color:#94a3b8;margin-top:4px}}
.score-row{{display:flex;align-items:center;gap:24px;background:#1e293b;border:1px solid #334155;border-radius:14px;padding:22px 28px;margin-bottom:26px}}
.score-num{{font-size:4rem;font-weight:900;line-height:1}}
.grid3{{display:grid;grid-template-columns:repeat(auto-fit, minmax(300px, 1fr));gap:18px;margin-bottom:26px}}
.card{{background:#1e293b;border:1px solid #334155;border-radius:12px;padding:20px 22px}}
.card h3{{font-size:.88rem;font-weight:700;color:#94a3b8;text-transform:uppercase;letter-spacing:.06em;margin-bottom:14px}}
.metric{{display:flex;justify-content:space-between;align-items:center;padding:7px 0;border-bottom:1px solid #2d3748;font-size:.84rem}} .metric:last-child{{border:none}}
.fcard{{background:#1e293b;border-left:4px solid #334155;border-radius:10px;padding:16px 18px;margin-bottom:10px}}
.fcard.critical{{border-left-color:#dc2626}} .fcard.high{{border-left-color:#ea580c}}
.fhead{{display:flex;align-items:center;gap:6px;margin-bottom:10px}} .ftitle{{font-weight:700;font-size:.92rem;color:#f1f5f9}}
.fbody p{{font-size:.82rem;color:#94a3b8;margin-bottom:5px}} .rec{{color:#86efac!important}}
.tw{{background:#1e293b;border:1px solid #334155;border-radius:12px;overflow:auto;margin-bottom:26px}}
table{{width:100%;border-collapse:collapse;font-size:.8rem}} th,td{{padding:9px 12px;text-align:left;border-bottom:1px solid #334155;white-space:nowrap}}
th{{background:#2d3748;color:#94a3b8;font-weight:700;font-size:.7rem;text-transform:uppercase}}
.muted{{color:#64748b!important;font-style:italic}}
</style></head><body>
<div class="header"><div><h1>Cisco Switch Performance Analytics</h1>
<div class="header-meta">{e(info.get("hostname"))} | {e(self.ip)} | Model: {e(info.get("model"))} | IOS: {e(info.get("ios_version"))}<br>Uptime: {e(info.get("uptime"))} | Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</div>
</div><div style="font-size:2.4rem">⚙️</div></div>
<div class="score-row"><div class="score-num" style="color:{score_color}">{score}</div>
<div><div style="font-size:1.15rem;font-weight:700;color:#f1f5f9">Switch Health Score <span style="font-size:.85rem;color:#94a3b8">/100</span></div>
<div style="color:{score_color};font-weight:600;margin-top:3px">{score_label}</div>
<div style="font-size:.82rem;color:#94a3b8;margin-top:4px">{c['critical']} Critical · {c['high']} High · {c['warning']} Warning · {c['info']} Info</div></div></div>
<div class="grid3">
<div class="card"><h3>CPU & Memory</h3>
 <div class="metric"><label>CPU 5min</label><span style="font-weight:700;color:{'#dc2626' if cpu['five_min'] >= 80 else '#d97706' if cpu['five_min'] >= 50 else '#e2e8f0'}">{cpu['five_min']}%</span></div>
 <div class="metric"><label>Memory Used</label><span style="font-weight:700;color:{'#dc2626' if mem.get('processor',{{}}).get('pct',0) >= 85 else '#d97706' if mem.get('processor',{{}}).get('pct',0) >= 70 else '#e2e8f0'}">{mem.get('processor',{{}}).get('pct',0)}%</span></div>
</div>
<div class="card"><h3>Spanning Tree & MAC</h3>
 <div class="metric"><label>STP Mode</label><span>{e(stp['mode'])}</span></div>
 <div class="metric"><label>BPDU Guard</label><span style="color:{'#4ade80' if stp['bpdu_guard'] else '#f87171'}">{'Enabled' if stp['bpdu_guard'] else 'DISABLED'}</span></div>
 <div class="metric"><label>CAM Table Fill</label><span style="font-weight:700;color:{'#dc2626' if (mac['total']/mac['max']*100 if mac['max'] else 0) >= 80 else '#e2e8f0'}">{round(mac['total']/mac['max']*100,1) if mac['max'] else 0}%</span></div>
</div>
<div class="card"><h3>Environment Status</h3>{power_html}{fan_html}</div>
</div>
<h2>Findings & Recommendations ({len(self.findings)} total)</h2>
<div>{cards if cards else '<p class="muted">No findings — switch appears healthy.</p>'}</div>
<h2>Top CPU Processes</h2><div class="tw"><table><thead><tr><th>PID</th><th>Process Name</th><th>CPU 5s</th><th>CPU 1m</th><th>CPU 5m</th></tr></thead><tbody>{cpu_rows or '<tr><td colspan=5 class=muted>No process data</td></tr>'}</tbody></table></div>
<h2>Interfaces (sorted by error count)</h2><div class="tw"><table><thead><tr><th>Interface</th><th>Status</th><th>Description</th><th>Duplex</th><th>Speed</th><th>Input Err</th><th>CRC</th><th>Drops</th><th>Resets</th></tr></thead><tbody>{iface_rows or '<tr><td colspan=9 class=muted>No interface data</td></tr>'}</tbody></table></div>
</body></html>"""

        with open(self.output_html, "w", encoding="utf-8") as fh:
            fh.write(html_template)

        print("=" * 62)
        print(f"  Report generated: {self.output_html}")
        print(f"  Score: {score}/100 — {score_label}")
        print("=" * 62)

    def run(self):
        """Executes the full analysis workflow."""
        self._collect_data()
        self._parse_data()
        self._analyze_data()
        self._generate_report()

    # ─────────────────────────────────────────────────────────────
    # Parsers (moved into class)
    # ─────────────────────────────────────────────────────────────

    def _parse_version(self, txt):
        info = {}
        patterns = {
            "ios_version": r"Cisco IOS.*?Version\s+([\S]+)",
            "hostname": r"hostname\s+(\S+)|^(\S+)\s+uptime",
            "uptime": r"uptime is (.+)",
            "model": r"cisco\s+(\S+)\s+.*?processor",
            "serial": r"Processor board ID\s+(\S+)",
        }
        for key, pattern in patterns.items():
            m = re.search(pattern, txt, re.IGNORECASE | re.MULTILINE)
            if m:
                info[key] = next((g for g in m.groups() if g is not None), "").strip()
        return info

    def _parse_cpu(self, txt):
        result = {"five_sec": 0, "one_min": 0, "five_min": 0, "processes": []}
        m = re.search(r"CPU utilization.*?:\s*(\d+)%/\d+%.*?(\d+)%.*?(\d+)%", txt)
        if m:
            result.update({"five_sec": int(m.group(1)), "one_min": int(m.group(2)), "five_min": int(m.group(3))})
        procs = re.findall(r"(\d+)\s+[\d\w]+\s+[\d\w]+\s+[\d\w]+\s+(\d+)%\s+(\d+)%\s+(\d+)%\s+\d+\s+(\S+.*?)$", txt, re.MULTILINE)
        for p in procs[:10]:
            result["processes"].append({"pid": p[0], "five_sec": int(p[1]), "one_min": int(p[2]), "five_min": int(p[3]), "name": p[4].strip()})
        return result

    def _parse_memory(self, txt):
        m = re.search(r"Total:\s*(\d+),\s*Used:\s*(\d+),\s*Free:\s*(\d+)", txt)
        if m:
            total, used = int(m.group(1)), int(m.group(2))
            return {"processor": {"total": total, "used": used, "pct": round(used / total * 100, 1) if total else 0}}
        return {"processor": {}}

    def _parse_interfaces(self, txt):
        ifaces = {}
        for block in re.split(r"(?=^\S+\s+is\s+)", txt, flags=re.MULTILINE):
            m_name = re.match(r"^(\S+)\s+is\s+(.+?),\s+line protocol is\s+(.+)", block)
            if not m_name: continue
            name, link, proto = m_name.groups()

            def _get(pattern, default=""): return (re.search(pattern, block, re.IGNORECASE) or [default])[0]
            def _int(pattern): return int((re.search(pattern, block) or [0, "0"])[1].replace(",", ""))

            ifaces[name] = {
                "link": link, "proto": proto,
                "description": _get(r"Description:\s*(.+)"),
                "duplex": _get(r"(\w+-duplex)"), "speed": _get(r"(\d+[MmGg]b/s)"),
                "input_errors": _int(r"(\d+)\s+input errors"), "crc": _int(r"(\d+)\s+CRC"),
                "output_errors": _int(r"(\d+)\s+output errors"),
                "drops": _int(r"(\d+)\s+input drops") + _int(r"(\d+)\s+output drops"),
                "resets": _int(r"(\d+)\s+interface resets"),
            }
        return ifaces

    def _parse_stp_summary(self, txt):
        return {
            "mode": (re.search(r"Switch is in\s+(\S+)\s+mode", txt) or ["", ""])[1],
            "tcn_events": len(re.findall(r"topology change", txt, re.IGNORECASE)),
            "bpdu_guard": bool(re.search(r"bpdu guard\s+enabled", txt, re.IGNORECASE)),
        }

    def _parse_mac_count(self, txt):
        result = {"total": 0, "max": 0}
        m_total = re.search(r"Total Mac Addresses.*?:\s*(\d+)", txt)
        if m_total: result["total"] = int(m_total.group(1))
        m_max = re.search(r"Maximum MAC Addresses.*?:\s*(\d+)", txt)
        if m_max: result["max"] = int(m_max.group(1))
        return result

    def _parse_log_issues(self, txt):
        return [{"label": m[1], "line": m[0]} for line in txt.splitlines() for m in [re.match(r".*?(%(\S+?-\d-\S+):.+)", line)] if m]

    def _parse_environment(self, txt):
        env_status = {"power": [], "fans": []}
        for line in txt.splitlines():
            psu_match = re.search(r"^(Power Supply \d+)\s+is\s+(.+)$", line.strip())
            if psu_match:
                env_status["power"].append({"name": psu_match.group(1), "status": psu_match.group(2).strip().rstrip('.')})
            fan_match = re.search(r"^(FAN \d+)\s+is\s+(.+)$", line.strip())
            if fan_match:
                env_status["fans"].append({"name": fan_match.group(1), "status": fan_match.group(2).strip().rstrip('.')})
        return env_status


def main():
    """Main function to run the analyzer."""
    parser = argparse.ArgumentParser(
        description="Cisco IOS/IOS-XE Switch Performance Analytics Tool (v2).",
        formatter_class=argparse.RawTextHelpFormatter,
        epilog="Example:\n  python cisco_switch_analyzer_v2.py 10.63.65.24 -u mark -o report.html"
    )
    parser.add_argument("ip", help="The IP address of the switch.")
    parser.add_argument("-u", "--username", required=True, help="SSH username.")
    parser.add_argument("-o", "--output", default="Cisco_Switch_Analytics.html", help="Output HTML file name.")
    args = parser.parse_args()

    print("=" * 62)
    print("  Cisco IOS/IOS-XE Switch Performance Analytics (v2)")
    print(f"  Target : {args.ip}")
    print(f"  User   : {args.username}")
    print(f"  Output : {args.output}")
    print("=" * 62)

    try:
        password = getpass.getpass(f"Password for {args.username}@{args.ip}: ")
    except Exception as error:
        print(f"ERROR: Could not read password: {error}")
        sys.exit(1)

    analyzer = CiscoSwitchAnalyzer(args.ip, args.username, password, args.output)
    analyzer.run()


if __name__ == "__main__":
    main()