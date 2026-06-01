#!/usr/bin/env python3
"""
Cisco Catalyst 9800 WLC 17.9.5 — Training Material Generator
Generates 4 self-contained HTML files for Network Engineers

Usage: python generate_9800_training.py
Output: 9800_training/
"""
import os

OUTPUT_DIR = "9800_training"

# ============================================================================
# CSS
# ============================================================================
CSS = """
:root{--navy:#1b2a4a;--teal:#00bceb;--green:#6cc04a;--red:#e2231a;--orange:#ff7300;--border:#dce2ed;--light:#f4f6f9;--text:#1e2330;--muted:#6b7a99;--sw:270px}
*,*::before,*::after{box-sizing:border-box;margin:0;padding:0}
html{scroll-behavior:smooth}
body{font-family:'Segoe UI',Roboto,Arial,sans-serif;background:var(--light);color:var(--text);line-height:1.65;font-size:15px}
.header{background:var(--navy);color:#fff;height:58px;display:flex;align-items:center;padding:0 24px;gap:14px;position:sticky;top:0;z-index:200;box-shadow:0 3px 10px rgba(0,0,0,.35)}
.header .logo{font-size:22px;font-weight:900;color:var(--teal);letter-spacing:-.5px}
.header .pipe{color:rgba(255,255,255,.25)}
.header .title{font-size:16px;font-weight:600}
.header .subtitle{font-size:12px;color:rgba(255,255,255,.65)}
.header .badge{margin-left:auto;background:var(--teal);color:var(--navy);font-size:11px;font-weight:800;padding:4px 12px;border-radius:20px}
.layout{display:flex;min-height:calc(100vh - 58px)}
.sidebar{width:var(--sw);background:var(--navy);flex-shrink:0;position:sticky;top:58px;height:calc(100vh - 58px);overflow-y:auto;padding-bottom:32px}
.sidebar::-webkit-scrollbar{width:3px}.sidebar::-webkit-scrollbar-thumb{background:var(--teal)}
.sb-group{border-bottom:1px solid rgba(255,255,255,.08);padding:6px 0}
.sb-label{font-size:10px;font-weight:700;letter-spacing:1.4px;text-transform:uppercase;color:var(--teal);padding:10px 16px 4px;display:block}
.sidebar a{display:block;padding:7px 16px 7px 20px;color:rgba(255,255,255,.72);text-decoration:none;font-size:13px;border-left:3px solid transparent;transition:all .18s}
.sidebar a:hover{background:rgba(0,188,235,.12);color:var(--teal);border-left-color:var(--teal)}
.sidebar a.sub{padding-left:32px;font-size:12px}
.sidebar a.sub2{padding-left:44px;font-size:12px}
.main{flex:1;padding:32px 36px;max-width:920px}
.card{background:#fff;border-radius:8px;margin-bottom:28px;box-shadow:0 1px 5px rgba(0,0,0,.08);overflow:hidden}
.card-head{background:var(--navy);color:#fff;padding:14px 20px;display:flex;align-items:center;gap:12px}
.card-head .icon{width:34px;height:34px;background:var(--teal);border-radius:6px;display:flex;align-items:center;justify-content:center;font-size:17px;flex-shrink:0}
.card-head h2{font-size:17px;font-weight:600}
.card-head .tag-badge{margin-left:auto;font-size:11px;background:rgba(255,255,255,.15);padding:3px 10px;border-radius:20px}
.card-body{padding:22px 24px}
.nav-path{background:#eef2fc;border:1px solid #c8d2ea;border-left:4px solid var(--teal);border-radius:5px;padding:9px 14px;font-family:'Consolas','Courier New',monospace;font-size:13px;color:var(--navy);margin:12px 0}
.screenshot{background:linear-gradient(135deg,#111c2e 0%,#1b2a4a 60%,#243660 100%);border:2px dashed var(--teal);border-radius:8px;padding:36px 24px;text-align:center;margin:16px 0;position:relative;overflow:hidden}
.screenshot::before{content:'';position:absolute;top:0;left:0;right:0;height:32px;background:rgba(0,0,0,.3);border-bottom:1px solid rgba(255,255,255,.1)}
.screenshot::after{content:'⬤  ⬤  ⬤';position:absolute;top:0;left:14px;font-size:10px;color:rgba(255,255,255,.4);line-height:32px}
.ph-body{padding-top:12px}
.ph-icon{font-size:44px;opacity:.5;margin-bottom:10px}
.ph-title{font-size:14px;font-weight:600;color:var(--teal)}
.ph-path{font-size:12px;color:rgba(255,255,255,.55);margin-top:6px;font-family:monospace}
.ph-note{display:inline-block;margin-top:12px;background:rgba(0,188,235,.15);border:1px solid rgba(0,188,235,.4);border-radius:4px;padding:4px 12px;font-size:11px;color:rgba(255,255,255,.75)}
.field-table{width:100%;border-collapse:collapse;margin:14px 0;font-size:13.5px}
.field-table thead th{background:var(--navy);color:#fff;padding:9px 13px;text-align:left;font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:.5px}
.field-table td{padding:9px 13px;border-bottom:1px solid var(--border);vertical-align:top}
.field-table tr:last-child td{border-bottom:none}
.field-table tr:nth-child(even) td{background:#f7f9fc}
.field-table td.fn{font-weight:600;color:var(--navy);white-space:nowrap}
.field-table td.def{font-family:monospace;color:#7a6000;font-size:12px}
.note{border-radius:5px;padding:11px 15px;margin:12px 0;font-size:13.5px;border-left:4px solid;display:flex;gap:10px;align-items:flex-start}
.note .ni{font-size:16px;flex-shrink:0;margin-top:1px}
.note.info{background:#e8f6fd;border-color:var(--teal)}
.note.warning{background:#fff6e8;border-color:var(--orange)}
.note.danger{background:#fef0f0;border-color:var(--red)}
.note.success{background:#edf8e7;border-color:var(--green)}
.subsec{margin:18px 0 10px}
.subsec h3{font-size:15px;font-weight:700;color:var(--navy);margin-bottom:8px}
.subsec h4{font-size:12px;font-weight:700;color:var(--muted);text-transform:uppercase;letter-spacing:.8px;margin:14px 0 5px}
p{margin-bottom:10px;color:#3a3f54}
ul,ol{padding-left:20px;margin:6px 0 10px}
li{margin-bottom:4px;color:#3a3f54;font-size:14px}
code{background:#eef2f8;border:1px solid #ccd5ea;border-radius:3px;padding:1px 6px;font-family:'Consolas',monospace;font-size:12.5px;color:#1a3a6b}
.ex-card{border:1px solid var(--border);border-radius:8px;margin-bottom:24px;overflow:hidden}
.ex-header{background:var(--navy);color:#fff;padding:13px 18px;display:flex;align-items:center;gap:12px}
.ex-num{width:30px;height:30px;background:var(--teal);border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:13px;font-weight:800;color:var(--navy);flex-shrink:0}
.ex-header h3{font-size:15px;font-weight:600}
.diff{margin-left:auto;font-size:11px;padding:3px 10px;border-radius:20px;font-weight:700}
.easy{background:rgba(108,192,74,.3);color:#2a6010}
.medium{background:rgba(255,115,0,.25);color:#7a3800}
.hard{background:rgba(226,35,26,.25);color:#7a1010}
.ex-body{padding:18px 20px}
.scenario{background:#f0f4ff;border-left:4px solid #5b80e8;border-radius:4px;padding:12px 14px;font-size:14px;margin-bottom:16px}
.scenario strong{color:#2a44a0}
.steps{counter-reset:sc;list-style:none;padding:0}
.steps li{counter-increment:sc;display:flex;gap:12px;margin-bottom:10px;font-size:14px;align-items:flex-start}
.steps li::before{content:counter(sc);min-width:24px;height:24px;background:var(--navy);color:var(--teal);border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:11px;font-weight:800;flex-shrink:0;margin-top:2px}
.expected{background:#edf8e7;border:1px solid #b8e0a8;border-radius:5px;padding:12px 14px;margin-top:14px;font-size:13.5px}
.expected strong{color:#2a6a10}
.verify{background:#e8f6fd;border:1px solid #a0d8f0;border-radius:5px;padding:12px 14px;margin-top:10px;font-size:13px}
.verify strong{color:#0050a0}
.quiz-bar{background:var(--navy);border-radius:8px;padding:18px 22px;margin-bottom:24px;display:flex;align-items:center;gap:16px;flex-wrap:wrap}
.quiz-bar h2{color:#fff;font-size:16px}
#sd{margin-left:auto;color:var(--teal);font-size:22px;font-weight:800}
.btn{padding:9px 20px;border-radius:5px;border:none;cursor:pointer;font-size:14px;font-weight:600;transition:all .2s}
.btn-p{background:var(--teal);color:var(--navy)}.btn-p:hover{background:#00a8d4}
.btn-s{background:rgba(255,255,255,.15);color:#fff}.btn-s:hover{background:rgba(255,255,255,.25)}
.qcat{background:var(--navy);color:var(--teal);padding:10px 18px;border-radius:6px;font-size:13px;font-weight:700;letter-spacing:.5px;margin:20px 0 14px;display:flex;align-items:center;gap:10px}
.qcard{background:#fff;border:1px solid var(--border);border-radius:8px;margin-bottom:14px;overflow:hidden}
.qtext{padding:14px 18px;font-size:14px;font-weight:600;color:var(--navy);border-bottom:1px solid var(--border);display:flex;gap:10px}
.qnum{color:var(--teal);flex-shrink:0}
.opts{padding:10px 14px}
.opt{display:flex;align-items:flex-start;gap:10px;padding:10px 12px;border-radius:5px;margin-bottom:6px;cursor:pointer;transition:background .15s;border:2px solid transparent;font-size:14px}
.opt:hover:not(.ans) .opt:hover{background:#f0f4ff;border-color:#b0c0e8}
.opt.correct{background:#edf8e7!important;border-color:var(--green)!important}
.opt.incorrect{background:#fef0f0!important;border-color:var(--red)!important}
.opt.showcorrect{background:#edf8e7!important;border-color:var(--green)!important}
.ol{min-width:24px;height:24px;border:2px solid var(--border);border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:11px;font-weight:800;flex-shrink:0;background:#fff}
.opt.correct .ol{background:var(--green);border-color:var(--green);color:#fff}
.opt.incorrect .ol{background:var(--red);border-color:var(--red);color:#fff}
.opt.showcorrect .ol{background:var(--green);border-color:var(--green);color:#fff}
.qexp{display:none;padding:10px 14px;border-top:1px solid var(--border);font-size:13px;background:#f8f9fc;color:#444;font-style:italic}
.qexp.vis{display:block}
.pbwrap{height:8px;background:rgba(255,255,255,.15);border-radius:4px;width:200px;overflow:hidden}
#pb{height:100%;background:var(--teal);border-radius:4px;width:0;transition:width .3s}
#rp{display:none;text-align:center;background:#fff;border-radius:8px;padding:40px;margin:20px 0;box-shadow:0 2px 10px rgba(0,0,0,.1)}
#rp h2{font-size:28px;color:var(--navy);margin-bottom:10px}
.grade{font-size:72px;font-weight:900;margin:10px 0}
.pass{color:var(--green)}.fail{color:var(--red)}
.tag-overview{background:var(--navy);border-radius:8px;padding:28px;margin-bottom:28px;color:#fff;text-align:center}
.tag-overview h2{font-size:22px;margin-bottom:6px}
.tag-overview p{color:rgba(255,255,255,.75);font-size:14px;max-width:620px;margin:0 auto 24px}
.tag-trio{display:flex;gap:16px;justify-content:center;flex-wrap:wrap}
.tbox{flex:1;min-width:180px;max-width:240px;border:2px solid;border-radius:8px;padding:18px 14px;text-align:center}
.tbox.pol{border-color:var(--teal);background:rgba(0,188,235,.12)}
.tbox.sit{border-color:var(--orange);background:rgba(255,115,0,.12)}
.tbox.rf{border-color:var(--green);background:rgba(108,192,74,.12)}
.tbox .tbi{font-size:36px;margin-bottom:8px}
.tbox .tbt{font-size:14px;font-weight:700;margin-bottom:4px}
.tbox.pol .tbt{color:var(--teal)}.tbox.sit .tbt{color:#ffaa55}.tbox.rf .tbt{color:#9ce870}
.tbox .tbd{font-size:12px;color:rgba(255,255,255,.65)}
.diagram{background:#0d1929;border-radius:8px;padding:20px 24px;font-family:'Consolas',monospace;font-size:13px;color:#c8d8f0;margin:16px 0;overflow-x:auto;line-height:1.9;border:1px solid rgba(255,255,255,.1)}
.diagram .dt{color:var(--teal);font-weight:700}
.diagram .dtag{color:#ffaa55}
.diagram .dpr{color:#9ce870}
.diagram .da{color:var(--teal)}
.diagram .dv{color:#ff9f9f}
.diagram .dn{color:rgba(255,255,255,.4);font-style:italic}
.egcard{border:1px solid var(--border);border-radius:8px;margin-bottom:24px;overflow:hidden}
.eghead{background:linear-gradient(135deg,var(--navy) 0%,#243660 100%);color:#fff;padding:14px 20px;display:flex;align-items:center;gap:12px}
.egicon{width:36px;height:36px;border-radius:8px;display:flex;align-items:center;justify-content:center;font-size:18px;flex-shrink:0}
.eghead h3{font-size:16px;font-weight:600}
.mode{margin-left:auto;font-size:11px;font-weight:700;padding:3px 10px;border-radius:20px}
.mode-loc{background:rgba(0,188,235,.3);color:#00bceb}
.mode-flex{background:rgba(255,115,0,.3);color:#ff9f50}
.mode-fab{background:rgba(108,192,74,.3);color:#6cc04a}
.egbody{padding:20px 22px}
@media(max-width:900px){.sidebar{display:none}.main{padding:20px;max-width:100%}}
"""

# ============================================================================
# QUIZ JAVASCRIPT
# ============================================================================
QUIZ_JS = """
var answered=0,correct=0,total=0;
function initQuiz(){total=document.querySelectorAll('.qcard').length;upd()}
function choose(qid,ch,cc,exp){
  var card=document.getElementById('q'+qid);
  if(card.classList.contains('ans'))return;
  card.classList.add('ans');
  card.querySelectorAll('.opt').forEach(function(o){
    var l=o.getAttribute('data-c');
    if(l===ch)o.classList.add(ch===cc?'correct':'incorrect');
    if(l===cc&&ch!==cc)o.classList.add('showcorrect');
  });
  var e=document.getElementById('e'+qid);
  if(e)e.classList.add('vis');
  answered++;if(ch===cc)correct++;upd();
}
function upd(){
  document.getElementById('sd').textContent=correct+' / '+answered;
  var p=total>0?(answered/total)*100:0;
  document.getElementById('pb').style.width=p+'%';
  if(answered===total&&total>0)showR();
}
function showR(){
  var p=Math.round((correct/total)*100),pass=p>=70;
  document.getElementById('rsc').textContent=p+'%';
  document.getElementById('rsc').className='grade '+(pass?'pass':'fail');
  document.getElementById('rl').textContent=pass?'PASS — Excellent work!':'FAIL — Review the material and retry';
  document.getElementById('rd').textContent=correct+' correct out of '+total+' questions';
  document.getElementById('rp').style.display='block';
}
function resetQ(){
  answered=0;correct=0;
  document.querySelectorAll('.qcard').forEach(function(c){
    c.classList.remove('ans');
    c.querySelectorAll('.opt').forEach(function(o){o.classList.remove('correct','incorrect','showcorrect')});
    var e=c.querySelector('.qexp');if(e)e.classList.remove('vis');
  });
  document.getElementById('rp').style.display='none';upd();
  window.scrollTo({top:0,behavior:'smooth'});
}
window.onload=initQuiz;
"""

# ============================================================================
# HTML UTILITIES
# ============================================================================
def page(title, subtitle, sidebar_html, body_html, extra_js=""):
    js = f"<script>{extra_js}</script>" if extra_js else ""
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>{title} | Cisco 9800 WLC 17.9.5</title>
<style>{CSS}</style>
</head>
<body>
<header class="header">
  <span class="logo">CISCO</span><span class="pipe">|</span>
  <div><div class="title">Catalyst 9800 WLC &mdash; {title}</div>
  <div class="subtitle">{subtitle}</div></div>
  <span class="badge">IOS-XE 17.9.5</span>
</header>
<div class="layout">
<nav class="sidebar">{sidebar_html}</nav>
<main class="main">{body_html}</main>
</div>
{js}
</body></html>"""

def sbg(label, items):
    links = "".join(f'<a href="#{h}" class="{c}">{t}</a>' for h, t, c in items)
    return f'<div class="sb-group"><span class="sb-label">{label}</span>{links}</div>'

def navp(parts):
    return '<div class="nav-path">' + ' <span style="color:var(--teal)">›</span> '.join(parts) + '</div>'

def sc(parts, label):
    p = " › ".join(parts)
    return f"""<div class="screenshot"><div class="ph-body">
<div class="ph-icon">🖥️</div>
<div class="ph-title">{label}</div>
<div class="ph-path">{p}</div>
<div class="ph-note">📸 Screenshot from your 9800 WebUI here</div>
</div></div>"""

def nt(kind, text):
    icons = {"info": "ℹ️", "warning": "⚠️", "danger": "🚨", "success": "✅"}
    return f'<div class="note {kind}"><span class="ni">{icons[kind]}</span><span>{text}</span></div>'

def ftable(rows, has_default=True):
    hdr = "<thead><tr><th>Field / Setting</th><th>Description</th>"
    if has_default: hdr += "<th>Default</th>"
    hdr += "</tr></thead><tbody>"
    body = ""
    for r in rows:
        fn, desc = r[0], r[1]
        df = r[2] if (has_default and len(r) > 2) else None
        body += f'<tr><td class="fn">{fn}</td><td>{desc}</td>'
        if has_default:
            body += f'<td class="def">{df if df else "—"}</td>'
        body += "</tr>"
    return f'<table class="field-table">{hdr}{body}</tbody></table>'

# ============================================================================
# MENU GUIDE DATA
# ============================================================================
MENU_SECTIONS = [
    {
        "id": "dashboard",
        "icon": "📊",
        "title": "Dashboard",
        "nav": ["Dashboard"],
        "desc": "The Dashboard is the landing page after login. It provides a real-time summary of the wireless network: AP health, client counts, RF performance, and recent alarms. Widgets are customizable and auto-refresh every 30 seconds.",
        "screenshot_label": "Dashboard Overview",
        "fields": [
            ("Network Summary", "Total APs, clients, WLANs active across the controller", "Auto-populated"),
            ("AP Summary Widget", "Breakdown of APs by status: Up, Down, Discovering, Unregistered", "Live"),
            ("Client Summary Widget", "Active clients per band (2.4 / 5 / 6 GHz) and per SSID", "Live"),
            ("RF Health Score", "0–10 score based on channel utilization, noise, and interference across all radios", "Live"),
            ("Top WLANs", "Most-used SSIDs ranked by client count and traffic volume", "Live"),
            ("Events / Alarms", "Recent system events, AP join/leave events, security alerts", "Last 24 h"),
        ],
        "notes": [
            ("info", "Dashboard widgets can be rearranged by drag-and-drop. Click the gear icon to add or remove widgets."),
            ("warning", "RF Health Score below 6 indicates significant RF degradation — investigate channel utilization or interference."),
        ],
    },
    {
        "id": "mon-aps",
        "icon": "📡",
        "title": "Monitoring › Access Points",
        "nav": ["Monitoring", "Wireless", "Access Points"],
        "desc": "Displays a live table of all APs joined to the controller, including model, IP, MAC, radio status, channel, Tx power, and associated client count. Use this view to quickly identify APs in Down or Discovering state.",
        "screenshot_label": "Monitoring — Access Points Table",
        "fields": [
            ("AP Name", "Configured hostname of the AP", ""),
            ("AP Model", "Hardware model (e.g., C9130AXI, C9120AXE)", ""),
            ("IP Address", "Management IP address of the AP", ""),
            ("Status", "Up / Down / Discovering / Image Mismatch / Unregistered", ""),
            ("Radio 0 / Radio 1 / Radio 2", "Admin status, channel, Tx power, and client count per radio", ""),
            ("Site Tag", "Site Tag currently assigned to this AP", "default-site-tag"),
            ("Policy Tag", "Policy Tag currently assigned to this AP", "default-policy-tag"),
            ("RF Tag", "RF Tag currently assigned to this AP", "default-rf-tag"),
            ("Location", "Free-text location field set in AP configuration", ""),
        ],
        "notes": [
            ("info", "Click any AP name to open the AP Detail page showing radio statistics, join history, and neighbour list."),
            ("warning", "\"Image Mismatch\" means the AP image version differs from the WLC. Trigger an AP pre-download from Administration › Software Management."),
        ],
    },
    {
        "id": "mon-clients",
        "icon": "👤",
        "title": "Monitoring › Clients",
        "nav": ["Monitoring", "Wireless", "Clients"],
        "desc": "Lists all currently associated wireless clients. Each row shows the client MAC, IP, WLAN, AP, band, protocol, RSSI, SNR, and data rates. Click a MAC address to drill into per-client statistics, roaming history, and policy details.",
        "screenshot_label": "Monitoring — Clients Table",
        "fields": [
            ("Client MAC", "Client hardware MAC address (used for Radioactive Trace)", ""),
            ("IPv4 / IPv6", "IP address assigned to the client", ""),
            ("WLAN Profile", "SSID the client is associated to", ""),
            ("AP Name", "AP the client is currently connected to", ""),
            ("Band / Protocol", "2.4 / 5 / 6 GHz and 802.11 protocol (ax / ac / n)", ""),
            ("RSSI", "Received Signal Strength Indicator in dBm (target > −70 dBm)", ""),
            ("SNR", "Signal-to-Noise Ratio in dB (target > 25 dB)", ""),
            ("VLAN", "Data VLAN assigned by the Policy Profile", ""),
            ("Auth Method", "Open / PSK / 802.1X / Web Auth", ""),
            ("Policy Tag", "Policy Tag applied to this client's AP", ""),
        ],
        "notes": [
            ("info", "Use the filter bar to search by MAC, IP, SSID, or AP name. Supports partial matches."),
            ("success", "RSSI > −65 dBm and SNR > 30 dB = excellent. RSSI < −75 dBm = coverage gap — consider AP placement."),
        ],
    },
    {
        "id": "mon-rf",
        "icon": "📶",
        "title": "Monitoring › RF Statistics & CleanAir",
        "nav": ["Monitoring", "RF", "RF Statistics"],
        "desc": "Provides per-radio RF health metrics: channel utilization, noise floor, interference, and TX/RX packet statistics. The Spectrum sub-page shows CleanAir non-802.11 interferer detection (requires CleanAir-capable APs such as the C9130, C9120 series).",
        "screenshot_label": "Monitoring — RF Statistics",
        "fields": [
            ("Channel Utilization", "Percentage of time the radio channel is busy (target < 50%)", ""),
            ("Noise Floor", "Background noise level in dBm (acceptable: < −95 dBm)", ""),
            ("Interference %", "Percentage of channel time occupied by non-802.11 interference", ""),
            ("TX / RX Packets", "Cumulative unicast/multicast/broadcast packet counts", ""),
            ("Interferer Type", "(CleanAir) Type of detected interferer: Microwave, DECT, Bluetooth, Video, Jammer", ""),
            ("Interferer Severity", "(CleanAir) 1–100 scale; > 50 = significant impact expected", ""),
            ("Affected Channel", "(CleanAir) Primary channel impacted by the interferer", ""),
            ("Duty Cycle", "(CleanAir) Percentage of time the interferer is active", ""),
        ],
        "notes": [
            ("warning", "Channel utilization > 70% is a strong indicator of congestion. Reduce AP Tx power or enable 5 GHz band steering to offload clients."),
            ("info", "CleanAir data is only available if the AP model supports it and CleanAir is enabled in the RF Profile."),
        ],
    },
    {
        "id": "mon-rogues",
        "icon": "🚨",
        "title": "Monitoring › Rogues & Interferers",
        "nav": ["Monitoring", "Wireless", "Rogues"],
        "desc": "Displays rogue APs and rogue clients detected by managed APs. A rogue AP is any 802.11 device not managed by this controller. Classification (Friendly, Malicious, Unclassified) and containment are configured under Configuration › Security › Wireless Protection Policies.",
        "screenshot_label": "Monitoring — Rogues Table",
        "fields": [
            ("Rogue MAC", "MAC address of the rogue device", ""),
            ("Type", "Rogue AP or Rogue Client", ""),
            ("SSID", "SSID being broadcast by the rogue AP (if detected)", ""),
            ("Channel", "Operating channel of the rogue device", ""),
            ("RSSI", "Signal strength as seen by the closest managed AP", ""),
            ("Closest AP", "The managed AP that detected this rogue", ""),
            ("State", "Alert / Threat / Contained / Acknowledged / Friendly", "Alert"),
            ("On-Wire", "Indicates if the rogue AP is detected on the wired network (more dangerous)", ""),
        ],
        "notes": [
            ("danger", "\"On-Wire\" rogues are the highest risk — they are connected to your LAN. Investigate and physically locate immediately."),
            ("warning", "Automatic containment (Rogue Containment) transmits deauth frames and may violate local regulations. Use only after legal review."),
        ],
    },
    {
        "id": "cfg-wlans",
        "icon": "📻",
        "title": "Configuration › WLANs",
        "nav": ["Configuration", "Wireless", "WLANs"],
        "desc": "WLAN Profiles define SSIDs — the logical wireless networks. Each profile sets the SSID name, security method, 802.11 options, and advanced features. A WLAN profile alone does NOT cause the SSID to broadcast; it must be mapped in a Policy Tag and that tag assigned to APs.",
        "screenshot_label": "Configuration — WLANs List",
        "fields": [
            ("Profile Name", "Internal name for the WLAN profile (used in Policy Tag mapping)", ""),
            ("SSID", "The broadcast network name clients see. Can differ from Profile Name", ""),
            ("Status", "Enabled / Disabled — controls whether the SSID is active", "Disabled"),
            ("Broadcast SSID", "Whether the SSID is visible in client scan results", "Enabled"),
            ("Radio Policy", "Which bands the SSID is allowed on: All / 2.4 GHz / 5 GHz / 6 GHz", "All"),
            ("Security › L2", "Layer 2 security: None (open) / WPA2-PSK / WPA3-SAE / WPA2+WPA3 / 802.1X", "WPA2-PSK"),
            ("Security › L3", "Layer 3: None / Web Policy (local or external captive portal)", "None"),
            ("802.11r (FT)", "Fast BSS Transition — enables seamless roaming for voice/video clients", "Disabled"),
            ("802.11k / 11v", "Neighbor reports (11k) and BSS Transition Management (11v) for assisted roaming", "Disabled"),
            ("MFP", "Management Frame Protection — protects against deauth attacks (requires 802.11w)", "Optional"),
            ("Max Clients", "Maximum number of simultaneously associated clients per SSID per AP radio", "0 (unlimited)"),
        ],
        "notes": [
            ("danger", "A newly created WLAN will NOT broadcast until: (1) Status = Enabled, (2) WLAN is mapped in a Policy Tag, (3) the Policy Tag is assigned to at least one AP."),
            ("info", "WPA2+WPA3 transition mode allows both legacy WPA2 and newer WPA3 clients to connect to the same SSID."),
            ("warning", "WPA3-SAE requires PMF (802.11w) to be set to Required. Older clients that cannot do PMF will fail to associate."),
        ],
    },
    {
        "id": "cfg-aps",
        "icon": "🔌",
        "title": "Configuration › Access Points",
        "nav": ["Configuration", "Wireless", "Access Points"],
        "desc": "Per-AP configuration and static tag assignment. This is where you assign custom Policy, Site, and RF Tags to individual APs, change the AP name, configure the primary/secondary WLC, and set location metadata.",
        "screenshot_label": "Configuration — Access Points",
        "fields": [
            ("AP Name", "Hostname assigned to the AP (shown in monitoring views)", ""),
            ("Admin Status", "Enable / Disable the AP entirely", "Enabled"),
            ("Primary Controller", "IP or FQDN of the primary WLC the AP should join", ""),
            ("Secondary / Tertiary WLC", "Fallback controllers if the primary is unreachable", ""),
            ("Policy Tag", "Policy Tag assigned to this AP (static assignment)", "default-policy-tag"),
            ("Site Tag", "Site Tag assigned to this AP — controls Local vs FlexConnect mode", "default-site-tag"),
            ("RF Tag", "RF Tag assigned to this AP — controls radio parameters", "default-rf-tag"),
            ("Location", "Free-text location string (floor, building, rack)", ""),
            ("LED State", "Normal / Off / Flashing — can override the LED for physical identification", "Normal"),
        ],
        "notes": [
            ("info", "Changing a Tag assignment on a live AP causes it to reset its radio configuration, which briefly disconnects associated clients (~2 seconds)."),
            ("success", "Best practice: create meaningful Tag names (e.g., Tag-Site-HQ-Floor2) before deploying APs to make bulk tag assignment easier."),
        ],
    },
    {
        "id": "cfg-policy-tag",
        "icon": "🏷️",
        "title": "Configuration › Tags › Policy Tag",
        "nav": ["Configuration", "Tags & Profiles", "Tags", "Policy"],
        "desc": "The Policy Tag maps WLAN Profiles to Policy Profiles. Each AP can have one Policy Tag, and that tag can contain up to 16 WLAN-Policy pairs. This is what causes the AP to broadcast specific SSIDs with specific client policies.",
        "screenshot_label": "Configuration — Policy Tag",
        "fields": [
            ("Tag Name", "Unique name for this Policy Tag", ""),
            ("Description", "Optional free-text description", ""),
            ("WLAN Profile", "The WLAN Profile (SSID) to include in this tag", ""),
            ("Policy Profile", "The Policy Profile to apply to clients on this WLAN", ""),
            ("Mapping Table", "Up to 16 WLAN-Profile pairs per tag; order does not matter", ""),
        ],
        "notes": [
            ("danger", "All APs that are not explicitly assigned a custom tag will use <code>default-policy-tag</code>. Any WLAN added to this default tag will broadcast on ALL untagged APs simultaneously."),
            ("info", "One Policy Tag can map multiple WLANs to different Policy Profiles — this is how you serve both corporate and guest SSIDs from the same AP."),
        ],
    },
    {
        "id": "cfg-site-tag",
        "icon": "🏢",
        "title": "Configuration › Tags › Site Tag",
        "nav": ["Configuration", "Tags & Profiles", "Tags", "Site"],
        "desc": "The Site Tag controls the AP operating mode and management behavior. It references an AP Join Profile (management settings) and optionally a Flex Profile. If a Flex Profile is attached, the AP operates in FlexConnect mode. If no Flex Profile is attached, the AP operates in Local (centralized) mode.",
        "screenshot_label": "Configuration — Site Tag",
        "fields": [
            ("Tag Name", "Unique name for this Site Tag", ""),
            ("AP Join Profile", "References AP Join Profile — controls NTP, syslog, CAPWAP timers, SSH", "default-ap-join-profile"),
            ("Flex Profile", "References Flex Profile — if set, AP operates in FlexConnect mode", "None (Local mode)"),
            ("Enable Local Site", "When checked: APs are locally connected to WLC (no WAN). When unchecked: remote/branch site", "Checked"),
        ],
        "notes": [
            ("danger", "Adding or removing a Flex Profile from a Site Tag causes ALL APs using that tag to switch operating modes and briefly lose connectivity during the transition."),
            ("info", "<strong>Local Site checked + no Flex Profile</strong> = Local mode (traffic tunneled to WLC).<br><strong>Local Site unchecked + Flex Profile attached</strong> = FlexConnect remote branch."),
            ("warning", "The 'Enable Local Site' checkbox does NOT alone put the AP into FlexConnect mode — you must also attach a Flex Profile."),
        ],
    },
    {
        "id": "cfg-rf-tag",
        "icon": "📡",
        "title": "Configuration › Tags › RF Tag",
        "nav": ["Configuration", "Tags & Profiles", "Tags", "RF"],
        "desc": "The RF Tag assigns RF Profiles to each radio band. This controls the radio behavior of all APs using this tag — channel selection, transmit power, channel width, and DCA (Dynamic Channel Assignment).",
        "screenshot_label": "Configuration — RF Tag",
        "fields": [
            ("Tag Name", "Unique name for this RF Tag", ""),
            ("5 GHz Band RF Profile", "RF Profile applied to the 5 GHz radio", "default-rf-profile"),
            ("2.4 GHz Band RF Profile", "RF Profile applied to the 2.4 GHz radio", "default-rf-profile"),
            ("6 GHz Band RF Profile", "RF Profile applied to the 6 GHz radio (Wi-Fi 6E APs only)", "default-rf-profile"),
        ],
        "notes": [
            ("info", "You can use the same RF Profile across multiple bands or create band-specific profiles for fine-grained control."),
            ("warning", "Changing the RF Tag on a live AP triggers a radio reset — clients on that AP will briefly disconnect."),
        ],
    },
    {
        "id": "cfg-policy-profile",
        "icon": "📋",
        "title": "Configuration › Profiles › Policy Profile",
        "nav": ["Configuration", "Tags & Profiles", "Policy"],
        "desc": "Policy Profiles define the client data-plane behavior: VLAN assignment, switching mode (Central or Local), QoS, ACL, and advanced features like NAC, AVC, and fabric mode. This is one of the most important profiles — it directly controls where client traffic goes.",
        "screenshot_label": "Configuration — Policy Profile",
        "fields": [
            ("Profile Name", "Unique name for this Policy Profile", ""),
            ("Status", "Enabled / Disabled", "Enabled"),
            ("VLAN / VLAN Group", "Layer 2 VLAN or VLAN group assigned to clients on this SSID", ""),
            ("Switching (Central)", "Central Switching: client data tunneled via CAPWAP to the WLC (default for Local mode APs)", "Enabled"),
            ("Switching (Local)", "Local Switching: client data forwarded directly by the AP (used with FlexConnect)", "Disabled"),
            ("DHCP (Central)", "Central DHCP: DHCP requests are forwarded to the WLC and handled centrally", "Enabled"),
            ("DHCP (Local)", "Local DHCP: DHCP requests handled locally at the AP/branch (FlexConnect)", "Disabled"),
            ("IPv4 ACL", "Named ACL applied to client traffic (inbound, outbound, or both)", "None"),
            ("AAA Override", "Allows RADIUS to override VLAN, ACL, and QoS per-client via VSA attributes", "Disabled"),
            ("NAC", "Network Admission Control — redirects clients to posture assessment server", "Disabled"),
            ("AVC Profile", "Application Visibility and Control profile for per-application QoS and visibility", "None"),
            ("Rate Limit (Up/Down)", "Per-client bandwidth cap in kbps (upstream and downstream)", "0 = unlimited"),
            ("mDNS Service Policy", "Enables mDNS/Bonjour proxy for AirPlay, AirPrint discovery across VLANs", "None"),
        ],
        "notes": [
            ("danger", "Central Switching and Local Switching are mutually exclusive. Enabling Local Switching automatically disables Central Switching."),
            ("info", "AAA Override must be enabled if you want RADIUS to dynamically assign per-user VLANs or ACLs (common in 802.1X deployments)."),
            ("warning", "If DHCP Central is enabled but the WLC does not have a path to the DHCP server, clients will fail to get an IP address even if the SSID associates."),
        ],
    },
    {
        "id": "cfg-ap-join",
        "icon": "⚙️",
        "title": "Configuration › Profiles › AP Join Profile",
        "nav": ["Configuration", "Tags & Profiles", "AP Join"],
        "desc": "The AP Join Profile controls how APs behave after joining the controller — management-plane settings only. This includes NTP, syslog, SSH access, CAPWAP timers, LED behavior, and statistics reporting intervals.",
        "screenshot_label": "Configuration — AP Join Profile",
        "fields": [
            ("Profile Name", "Unique name for this AP Join Profile", "default-ap-join-profile"),
            ("NTP Server", "NTP server IP address for AP time synchronization", "Inherited from WLC"),
            ("Syslog Server", "External syslog server IP for AP log messages", ""),
            ("SSH / Telnet", "Enable SSH or Telnet access directly to the AP CLI", "SSH enabled"),
            ("CAPWAP Retransmit Timeout", "Seconds before retransmitting a CAPWAP control message", "3 s"),
            ("CAPWAP Retransmit Count", "Number of retransmit attempts before declaring WLC unreachable", "5"),
            ("Statistics Timer", "How often the AP reports RF and client statistics to the WLC", "180 s"),
            ("TCP MSS Adjust", "Maximum Segment Size adjustment for CAPWAP tunnel (prevents fragmentation)", "1250"),
            ("LED Flash", "Enable/disable AP LED flashing for physical identification", "Enabled"),
        ],
        "notes": [
            ("info", "Changes to an AP Join Profile take effect immediately on all APs referencing it via their Site Tag — no reboot required for most settings."),
        ],
    },
    {
        "id": "cfg-rf-profile",
        "icon": "📻",
        "title": "Configuration › Profiles › RF Profile",
        "nav": ["Configuration", "Tags & Profiles", "RF"],
        "desc": "RF Profiles define the radio behavior for a specific band (2.4, 5, or 6 GHz). This includes transmit power range, channel width, DCA channel list, TPC algorithm, band steering, and 802.11ax (Wi-Fi 6) settings.",
        "screenshot_label": "Configuration — RF Profile",
        "fields": [
            ("Band", "The radio band this profile applies to: 2.4 GHz / 5 GHz / 6 GHz", ""),
            ("Min / Max Tx Power", "Transmit power range in dBm. TPC operates within this range", "Min: 1 dBm, Max: 30 dBm"),
            ("Channel Width", "20 / 40 / 80 / 160 MHz. Wider = more throughput, less co-channel APs", "20 MHz (2.4), 80 MHz (5)"),
            ("DCA (Auto Channel)", "Enables Dynamic Channel Assignment — WLC automatically selects best channel", "Enabled"),
            ("DCA Channel List", "Restrict which channels DCA may use (e.g., avoid DFS channels)", "All legal channels"),
            ("TPC (Auto Power)", "Transmit Power Control — WLC auto-adjusts power to maintain coverage overlap", "Enabled"),
            ("Coverage Hole Detection", "Automatically increases AP power if coverage holes are detected", "Enabled"),
            ("Band Steering", "Encourages dual-band clients to use 5 GHz instead of 2.4 GHz", "Disabled"),
            ("802.11ax (Wi-Fi 6)", "Enable/disable BSS Coloring, OFDMA, MU-MIMO, Target Wake Time (TWT)", "Enabled on 6E APs"),
            ("BSS Color", "802.11ax BSS Coloring — reduces co-channel interference in dense deployments", "Auto"),
        ],
        "notes": [
            ("info", "DCA runs every 10 minutes by default. In high-density environments, consider setting DCA interval to 1 hour to avoid excessive channel changes."),
            ("warning", "Enabling 160 MHz channel width on 5 GHz significantly reduces the number of usable non-overlapping channels. Use only in low-density environments."),
        ],
    },
    {
        "id": "cfg-flex-profile",
        "icon": "🔄",
        "title": "Configuration › Profiles › Flex Profile",
        "nav": ["Configuration", "Tags & Profiles", "Flex"],
        "desc": "Flex Profiles configure FlexConnect-specific behavior for remote-branch APs. This includes local VLAN-to-WLAN mappings, local RADIUS for survivability, and ACL definitions that apply when the AP is in standalone mode (WAN link down).",
        "screenshot_label": "Configuration — Flex Profile",
        "fields": [
            ("Profile Name", "Unique name for this Flex Profile", ""),
            ("VLAN-SSID Mapping (Native VLAN override)", "Maps each WLAN to a local VLAN at the branch. Overrides the central Policy Profile VLAN.", ""),
            ("Local RADIUS Server", "IP of a local RADIUS server at the branch for client auth when WAN is down", ""),
            ("AAA Policy (RADIUS Fallback)", "Specifies local RADIUS group used during WLC unreachability", ""),
            ("ACL Mapping", "Named ACLs pushed to the AP for enforcement when in standalone mode", ""),
            ("Efficient Image Upgrade", "Use AP-to-AP image distribution to reduce WAN bandwidth during upgrades", "Enabled"),
        ],
        "notes": [
            ("success", "VLAN override in the Flex Profile is critical: branch APs need local VLANs (e.g., VLAN 20 at the branch) even if the central Policy Profile uses a different VLAN number."),
            ("info", "If no local RADIUS is configured, FlexConnect APs can cache up to 100 client credentials so already-authenticated clients can re-associate during a WAN outage."),
        ],
    },
    {
        "id": "cfg-aaa",
        "icon": "🔒",
        "title": "Configuration › Security › AAA",
        "nav": ["Configuration", "Security", "AAA"],
        "desc": "The AAA section configures RADIUS and TACACS+ servers, server groups, and method lists. Method lists are referenced by WLANs (for client 802.1X) and by the WLC itself (for management access). Getting AAA right is essential for enterprise wireless deployments.",
        "screenshot_label": "Configuration — AAA Servers",
        "fields": [
            ("Server Type", "RADIUS (client auth) or TACACS+ (management auth)", "RADIUS"),
            ("Server IP / Hostname", "IP address or FQDN of the AAA server", ""),
            ("Auth Port", "UDP port for authentication requests", "1812 (RADIUS)"),
            ("Acct Port", "UDP port for accounting messages", "1813 (RADIUS)"),
            ("Shared Key", "Pre-shared secret between the WLC and the RADIUS server", ""),
            ("Timeout", "Seconds to wait for a RADIUS response before retransmitting", "5 s"),
            ("Retransmit", "Number of retransmit attempts before marking server as dead", "3"),
            ("Dead Time", "Minutes a server is marked dead before attempting recovery", "5 min"),
            ("Server Group", "Named group of RADIUS servers for load-balancing or failover", ""),
            ("Method List (Auth)", "Named list: type dot1x, mac, web-auth; references server group", ""),
            ("Method List (Acct)", "Named list for accounting; references server group", ""),
        ],
        "notes": [
            ("danger", "RADIUS shared key is case-sensitive and must match exactly on both the WLC and the RADIUS server. A mismatch causes silent authentication failures with no error message to the client."),
            ("info", "For redundancy, add two RADIUS servers to a Server Group. The WLC will load-balance by default; set the second server as backup-only if preferred."),
            ("warning", "Always create and reference a named Method List in the WLAN configuration. The default method list is applied if none is specified but relying on defaults makes troubleshooting harder."),
        ],
    },
    {
        "id": "cfg-acl",
        "icon": "🛡️",
        "title": "Configuration › Security › ACL",
        "nav": ["Configuration", "Security", "ACL"],
        "desc": "Named IPv4 and IPv6 ACLs can be created here and then applied to client traffic via Policy Profiles or URL-based redirect policies. ACEs (Access Control Entries) are processed top-down; the first match wins. Always end with an explicit permit or deny rule.",
        "screenshot_label": "Configuration — ACL",
        "fields": [
            ("ACL Name", "Unique identifier for this ACL", ""),
            ("Type", "IPv4 Extended / IPv4 Standard / IPv6 / MAC", "IPv4 Extended"),
            ("ACE Sequence", "Processing order — lower number = evaluated first", "10, 20, 30…"),
            ("Action", "Permit or Deny", ""),
            ("Protocol", "IP / TCP / UDP / ICMP / any", "any"),
            ("Source IP / Mask", "Source network in IP + wildcard mask format", "any"),
            ("Destination IP / Mask", "Destination network in IP + wildcard mask format", "any"),
            ("Port (Dest)", "Destination TCP/UDP port for fine-grained control", "any"),
            ("Log", "Enable logging of ACE hits (performance impact — use sparingly)", "Disabled"),
        ],
        "notes": [
            ("warning", "If no explicit permit/deny any any is at the end, the implicit deny any any will silently drop all unmatched traffic. Always add a final permit if you only want to block specific traffic."),
            ("info", "ACLs applied in the Policy Profile are enforced in the dataplane. For FlexConnect APs in standalone mode, ACLs must also be mapped in the Flex Profile."),
        ],
    },
    {
        "id": "cfg-webauth",
        "icon": "🌐",
        "title": "Configuration › Security › Web Auth",
        "nav": ["Configuration", "Security", "Web Auth"],
        "desc": "Web Authentication enables captive portal functionality for guest networks. The WLC can serve a local login page (Local Web Auth) or redirect clients to an external portal (External Web Auth). Clients are intercepted until they successfully authenticate through the portal.",
        "screenshot_label": "Configuration — Web Auth",
        "fields": [
            ("Virtual IP", "IP address the WLC uses to intercept HTTP traffic and serve the captive portal. Must not be routable on your network.", "192.0.2.1"),
            ("Web Auth Type", "Local (WLC serves the login page) or External (redirect to external URL)", "Local"),
            ("Login Page", "Custom HTML login page upload (Local Web Auth)", "Default Cisco page"),
            ("Redirect URL (success)", "URL clients are sent to after successful authentication", ""),
            ("Redirect URL (fail)", "URL clients are sent to after failed authentication", ""),
            ("External Portal URL", "FQDN/IP of the external captive portal (External Web Auth)", ""),
            ("Timeout (session)", "Idle timeout in seconds after which clients are re-prompted", "1800 s"),
        ],
        "notes": [
            ("info", "The virtual IP (default 192.0.2.1) must NOT be routable on your network. Clients initially send HTTP traffic to any destination; the WLC intercepts and redirects to this virtual IP."),
            ("warning", "HTTPS sites will NOT be intercepted by the captive portal without certificate trust issues. Best practice: instruct guests to browse to an HTTP site first to trigger the redirect."),
        ],
    },
    {
        "id": "admin-sw",
        "icon": "⬆️",
        "title": "Administration › Software Upgrade",
        "nav": ["Administration", "Software Management", "Software Upgrade"],
        "desc": "Used to upload a new IOS-XE image to the WLC and trigger the upgrade. Always pre-download the image to APs before activating the WLC upgrade to minimize AP downtime. The WLC reboots during activation (~5–7 minutes).",
        "screenshot_label": "Administration — Software Upgrade",
        "fields": [
            ("Transfer Mode", "TFTP / SFTP / FTP / HTTP / Device (USB/flash)", "SFTP"),
            ("Server IP", "IP address of the file transfer server", ""),
            ("Username / Password", "Credentials for SFTP/FTP (SFTP recommended — encrypted)", ""),
            ("File Path", "Full path to the .bin image file on the server", ""),
            ("Image Version", "Target IOS-XE version (shown after successful download)", ""),
            ("AP Pre-download", "Downloads the new image to all joined APs before activating the WLC", "Recommended"),
            ("Activate", "Triggers WLC reload into the new image. Causes ~5–7 min outage.", ""),
        ],
        "notes": [
            ("danger", "Always pre-download to APs first. If you activate the WLC without pre-download, APs will download the image after the WLC reboots — multiplied across hundreds of APs this can take hours and cause extended downtime."),
            ("success", "Recommended upgrade sequence: (1) Download image to WLC -> (2) AP Pre-download -> (3) Wait for all APs to show Pre-downloaded -> (4) Activate during maintenance window."),
            ("warning", "SMU (Software Maintenance Update) patches can be applied without a full reboot — available under Administration › Software Management › SMU."),
        ],
    },
    {
        "id": "admin-lic",
        "icon": "📜",
        "title": "Administration › Licensing",
        "nav": ["Administration", "Licensing"],
        "desc": "The 9800 uses Cisco Smart Licensing. Two license tiers apply to wireless: Essentials (basic features) and Advantage (advanced security, mDNS, CleanAir, Flex+Bridge). The AP count license is consumption-based — one license per joined AP.",
        "screenshot_label": "Administration — Licensing",
        "fields": [
            ("License Level", "Essentials or Advantage (per AP)", "Essentials"),
            ("AP Count", "Number of APs currently consuming a license", "Live"),
            ("Smart Account", "Cisco Smart Account linked to this WLC for license management", ""),
            ("Registration Token", "Token generated from software.cisco.com to register this WLC", ""),
            ("Registration Status", "Registered / Not Registered / Out of Compliance", ""),
            ("License Enforcement", "In 17.9.x: Enforcement mode — APs may be disabled if out of compliance for >90 days", "Enforced"),
        ],
        "notes": [
            ("warning", "Cisco enforces Smart Licensing in 17.9.x. If the WLC cannot reach Cisco's license servers and no offline tokens are present, APs may enter \"Out of Compliance\" state after 90 days."),
            ("info", "For air-gapped networks, use CSSM On-Prem (Smart License Satellite) or generate offline tokens from Cisco's Smart Account portal."),
        ],
    },
    {
        "id": "ts-rat",
        "icon": "🔬",
        "title": "Troubleshooting › Radioactive Trace",
        "nav": ["Troubleshooting", "Radioactive Trace"],
        "desc": "Radioactive Trace is the primary per-device debug tool on the 9800. It captures comprehensive debug logs for a specific client MAC address or AP MAC, including 802.1X/RADIUS exchanges, DHCP transactions, policy application, CAPWAP join messages, and roaming events — without impacting other clients.",
        "screenshot_label": "Troubleshooting — Radioactive Trace",
        "fields": [
            ("MAC Address", "Client or AP MAC address to trace. Multiple MACs can be added simultaneously.", ""),
            ("Start Button", "Activates debug collection for the specified MAC(s)", ""),
            ("Stop Button", "Stops debug collection and finalizes the log file", ""),
            ("Download Log", "Downloads the trace log as a plain text file", ""),
            ("Log Retention", "Logs are retained for the session only — download before navigating away", ""),
        ],
        "notes": [
            ("success", "Radioactive Trace is the FIRST tool to use for: 802.1X failures, client not associating, DHCP failures, roaming issues, and policy/VLAN mismatches. It gives a complete timeline of events for the client."),
            ("info", "To use: Add the client MAC -> click Start -> reproduce the issue (try to connect) -> click Stop -> Download. Open the .txt log and search for: FAILED, REJECT, ERROR, TIMEOUT."),
            ("warning", "Traces older than the current WLC session are not available in the GUI. For persistent capture, configure syslog to an external server with debug-level logging for specific MAC filters."),
        ],
    },
    {
        "id": "ts-pcap",
        "icon": "📦",
        "title": "Troubleshooting › Packet Capture",
        "nav": ["Troubleshooting", "Packet Capture"],
        "desc": "Embedded Packet Capture allows you to capture raw 802.11 frames at an AP radio or Ethernet frames at a WLC interface. The resulting .pcap file can be downloaded and analyzed in Wireshark. This is essential for diagnosing EAPOL frames, DHCP exchanges, and ARP issues at the frame level.",
        "screenshot_label": "Troubleshooting — Packet Capture",
        "fields": [
            ("Capture Name", "Identifier for this capture session", ""),
            ("AP Name", "Select the AP on which to capture frames", ""),
            ("Radio Interface", "radio0 (2.4 GHz), radio1 (5 GHz), radio2 (6 GHz)", ""),
            ("Direction", "Tx only / Rx only / Both", "Both"),
            ("Duration (sec)", "Automatic stop after this many seconds", "60"),
            ("Buffer Size (MB)", "Memory buffer for captured frames", "10 MB"),
            ("Client Filter (MAC)", "Optional: capture only frames for a specific client MAC", ""),
            ("Download", "Downloads the .pcap file when capture is complete or stopped", ""),
        ],
        "notes": [
            ("info", "Wireshark filters useful for wireless analysis: <code>eapol</code> (802.1X), <code>dhcp</code>, <code>arp</code>, <code>wlan.fc.type_subtype == 0x00</code> (association requests)."),
            ("warning", "Packet capture uses AP memory as a ring buffer. If the buffer fills before the capture is downloaded, the oldest frames are overwritten. For long captures, increase buffer size or reduce duration."),
            ("success", "Use Packet Capture + Radioactive Trace together for comprehensive client troubleshooting: Radioactive Trace gives you the control-plane view (WLC side), Packet Capture gives you the frame-level view (over the air)."),
        ],
    },
]

MENU_SIDEBAR = [
    sbg("Dashboard", [("dashboard", "Dashboard", "")]),
    sbg("Monitoring", [
        ("mon-aps",     "Access Points", "sub"),
        ("mon-clients", "Clients", "sub"),
        ("mon-rf",      "RF Statistics & CleanAir", "sub"),
        ("mon-rogues",  "Rogues & Interferers", "sub"),
    ]),
    sbg("Configuration › Wireless", [
        ("cfg-wlans", "WLANs", "sub"),
        ("cfg-aps",   "Access Points", "sub"),
    ]),
    sbg("Config › Tags", [
        ("cfg-policy-tag", "Policy Tag", "sub"),
        ("cfg-site-tag",   "Site Tag", "sub"),
        ("cfg-rf-tag",     "RF Tag", "sub"),
    ]),
    sbg("Config › Profiles", [
        ("cfg-policy-profile", "Policy Profile", "sub"),
        ("cfg-ap-join",        "AP Join Profile", "sub"),
        ("cfg-rf-profile",     "RF Profile", "sub"),
        ("cfg-flex-profile",   "Flex Profile", "sub"),
    ]),
    sbg("Config › Security", [
        ("cfg-aaa",     "AAA (RADIUS/TACACS+)", "sub"),
        ("cfg-acl",     "ACL", "sub"),
        ("cfg-webauth", "Web Auth", "sub"),
    ]),
    sbg("Administration", [
        ("admin-sw",  "Software Upgrade", "sub"),
        ("admin-lic", "Licensing", "sub"),
    ]),
    sbg("Troubleshooting", [
        ("ts-rat",  "Radioactive Trace", "sub"),
        ("ts-pcap", "Packet Capture", "sub"),
    ]),
]

# ============================================================================
# EXERCISES DATA
# ============================================================================
EXERCISES = [
    {
        "id": "ex1",
        "num": 1,
        "title": "Create a Corporate WPA3 SSID with Central Switching",
        "difficulty": "easy",
        "scenario": "<strong>Scenario:</strong> Your company needs a new corporate SSID called <em>Corp-WiFi6</em> using WPA3 security. All client traffic must be centrally forwarded to the WLC and placed on VLAN 100.",
        "steps": [
            "Navigate to <strong>Configuration &rsaquo; Wireless &rsaquo; WLANs</strong> and click <strong>+ Add</strong>.",
            "Set <strong>Profile Name</strong> = <code>Corp-WiFi6</code>, <strong>SSID</strong> = <code>Corp-WiFi6</code>, <strong>Status</strong> = Enabled.",
            "Click the <strong>Security</strong> tab &rsaquo; <strong>Layer 2</strong>. Select <strong>WPA3 Personal (SAE)</strong>. Set a strong passphrase. Enable <strong>PMF</strong> = Required (mandatory for WPA3).",
            "Click <strong>Save &amp; Apply to Device</strong>.",
            "Navigate to <strong>Configuration &rsaquo; Tags &amp; Profiles &rsaquo; Policy</strong> and click <strong>+ Add</strong>.",
            "Set <strong>Profile Name</strong> = <code>Policy-Corp</code>, Status = Enabled.",
            "Under <strong>Access Policies</strong>: set <strong>VLAN</strong> = <code>100</code>. Ensure <strong>Central Switching</strong> = Enabled and <strong>Central DHCP</strong> = Enabled.",
            "Click <strong>Save &amp; Apply to Device</strong>.",
            "Navigate to <strong>Configuration &rsaquo; Tags &amp; Profiles &rsaquo; Tags &rsaquo; Policy</strong> and click <strong>+ Add</strong>.",
            "Set <strong>Tag Name</strong> = <code>Tag-Corp</code>. In the WLAN-Policy table, click <strong>+ Add</strong>: select <strong>WLAN Profile</strong> = <code>Corp-WiFi6</code>, <strong>Policy Profile</strong> = <code>Policy-Corp</code>.",
            "Click <strong>Save &amp; Apply to Device</strong>.",
            "Navigate to <strong>Configuration &rsaquo; Wireless &rsaquo; Access Points</strong>, click the target AP.",
            "Change <strong>Policy Tag</strong> = <code>Tag-Corp</code>. Click <strong>Update &amp; Apply to Device</strong>.",
        ],
        "expected": "The SSID <code>Corp-WiFi6</code> broadcasts on the target AP. Connecting clients receive an IP address on VLAN 100 via central DHCP. Verify under <strong>Monitoring &rsaquo; Wireless &rsaquo; Clients</strong> — VLAN column should show 100.",
        "verify": "CLI: <code>show wireless client summary</code> | <code>show wireless wlan summary</code>",
    },
    {
        "id": "ex2",
        "num": 2,
        "title": "Configure a FlexConnect Site Tag for a Remote Branch",
        "difficulty": "medium",
        "scenario": "<strong>Scenario:</strong> A remote branch office has 2 Cisco APs connected over a WAN link. Configure them for FlexConnect with local switching so that client traffic is handled locally — even if the WAN link to the WLC goes down.",
        "steps": [
            "Navigate to <strong>Configuration &rsaquo; Tags &amp; Profiles &rsaquo; Flex</strong> and click <strong>+ Add</strong>.",
            "Set <strong>Profile Name</strong> = <code>Flex-Branch</code>.",
            "Under <strong>VLAN</strong>, add a VLAN mapping: WLAN <code>Corp-WiFi6</code> &rarr; VLAN <code>100</code> (the local VLAN at the branch switch).",
            "Click <strong>Save &amp; Apply to Device</strong>.",
            "Navigate to <strong>Configuration &rsaquo; Tags &amp; Profiles &rsaquo; AP Join</strong> and click <strong>+ Add</strong> (or use existing).",
            "Set <strong>Profile Name</strong> = <code>APJoin-Branch</code>. Set NTP and syslog server IPs appropriate for the branch.",
            "Click <strong>Save &amp; Apply to Device</strong>.",
            "Navigate to <strong>Configuration &rsaquo; Tags &amp; Profiles &rsaquo; Tags &rsaquo; Site</strong> and click <strong>+ Add</strong>.",
            "Set <strong>Tag Name</strong> = <code>Tag-Site-Branch</code>. <strong>AP Join Profile</strong> = <code>APJoin-Branch</code>. <strong>Flex Profile</strong> = <code>Flex-Branch</code>.",
            "<strong>Uncheck</strong> &ldquo;Enable Local Site&rdquo; — this declares the APs as remote (not directly connected to the WLC).",
            "Click <strong>Save &amp; Apply to Device</strong>.",
            "Navigate to <strong>Configuration &rsaquo; Wireless &rsaquo; Access Points</strong>, select each branch AP.",
            "Change <strong>Site Tag</strong> = <code>Tag-Site-Branch</code>. Also ensure <strong>Policy Tag</strong> = <code>Tag-Corp</code> (from Exercise 1). Click <strong>Update &amp; Apply to Device</strong>.",
        ],
        "expected": "Branch APs switch to FlexConnect mode (verify under Monitoring &rsaquo; Access Points — AP Mode column shows FlexConnect). Client traffic is locally switched at the branch without traversing the WAN. If WAN fails, clients remain connected.",
        "verify": "CLI: <code>show ap config general &lt;ap-name&gt;</code> — confirm AP Mode: FlexConnect",
    },
    {
        "id": "ex3",
        "num": 3,
        "title": "Configure RADIUS 802.1X Authentication",
        "difficulty": "medium",
        "scenario": "<strong>Scenario:</strong> Security policy requires 802.1X Enterprise authentication for the corporate SSID. Configure RADIUS server at 10.1.1.100 (port 1812, secret: <em>Cisco12345!</em>) and apply it to the <em>Corp-WiFi6</em> WLAN.",
        "steps": [
            "Navigate to <strong>Configuration &rsaquo; Security &rsaquo; AAA &rsaquo; Servers / Groups &rsaquo; Servers</strong>. Click <strong>+ Add</strong>.",
            "Set <strong>Server Address</strong> = <code>10.1.1.100</code>, <strong>Auth Port</strong> = 1812, <strong>Acct Port</strong> = 1813, <strong>Key</strong> = <code>Cisco12345!</code>. Click <strong>Save</strong>.",
            "Navigate to <strong>AAA &rsaquo; Servers / Groups &rsaquo; Server Groups</strong>. Click <strong>+ Add</strong>.",
            "Set <strong>Group Name</strong> = <code>RADIUS-Corp</code>, <strong>Group Type</strong> = RADIUS. Add <code>10.1.1.100</code> to the group. Click <strong>Save</strong>.",
            "Navigate to <strong>AAA &rsaquo; Method Lists &rsaquo; Authentication</strong>. Click <strong>+ Add</strong>.",
            "Set <strong>Method List Name</strong> = <code>dot1x-corp</code>, <strong>Type</strong> = dot1x. Add <strong>Group</strong> = <code>RADIUS-Corp</code>. Click <strong>Save</strong>.",
            "Navigate to <strong>AAA &rsaquo; Method Lists &rsaquo; Accounting</strong>. Click <strong>+ Add</strong>.",
            "Set <strong>Method List Name</strong> = <code>acct-corp</code>, <strong>Type</strong> = identity. Add <code>RADIUS-Corp</code>. Click <strong>Save</strong>.",
            "Navigate to <strong>Configuration &rsaquo; Wireless &rsaquo; WLANs</strong>, edit <code>Corp-WiFi6</code>.",
            "Security tab &rsaquo; Layer 2: Change to <strong>WPA2 Enterprise (802.1X)</strong>. Set <strong>Auth Key Management</strong> = 802.1X. Set <strong>Authentication List</strong> = <code>dot1x-corp</code>.",
            "Save &amp; Apply to Device.",
            "Edit Policy Profile <code>Policy-Corp</code>: ensure <strong>AAA Override</strong> = Enabled (allows RADIUS to push dynamic VLAN/ACL).",
        ],
        "expected": "Clients connecting to Corp-WiFi6 are prompted for credentials (EAP). Successful 802.1X authentication results in association; rejected credentials result in disconnection. Verify under Monitoring &rsaquo; Clients: Auth Method = Dot1x.",
        "verify": "Troubleshooting &rsaquo; Radioactive Trace on the client MAC — look for RADIUS Access-Accept message in the log.",
    },
    {
        "id": "ex4",
        "num": 4,
        "title": "Create a Guest SSID with Local Web Authentication",
        "difficulty": "easy",
        "scenario": "<strong>Scenario:</strong> Create an open guest SSID called <em>Guest-WiFi</em> with a local captive portal. Guest clients should land on VLAN 200 and be redirected to a login page before accessing the internet.",
        "steps": [
            "Navigate to <strong>Configuration &rsaquo; Security &rsaquo; Web Auth</strong>. Confirm <strong>Virtual IP</strong> is set (default <code>192.0.2.1</code>). This IP must be non-routable on your network.",
            "Navigate to <strong>Configuration &rsaquo; Wireless &rsaquo; WLANs</strong> and click <strong>+ Add</strong>.",
            "Set <strong>Profile Name</strong> = <code>Guest-WiFi</code>, <strong>SSID</strong> = <code>Guest-WiFi</code>, Status = Enabled.",
            "Security tab &rsaquo; Layer 2: set to <strong>None</strong> (open network). Layer 3: select <strong>Web Policy</strong>. Type = <strong>Webauth</strong>. Authentication List = <code>default</code> (local user database).",
            "Click <strong>Save &amp; Apply to Device</strong>.",
            "Navigate to <strong>Configuration &rsaquo; Tags &amp; Profiles &rsaquo; Policy</strong> and click <strong>+ Add</strong>.",
            "Set <strong>Profile Name</strong> = <code>Policy-Guest</code>. VLAN = <code>200</code>. Central Switching = Enabled.",
            "Click <strong>Save &amp; Apply to Device</strong>.",
            "Navigate to <strong>Tags &amp; Profiles &rsaquo; Tags &rsaquo; Policy</strong>, edit or create a tag. Add mapping: <code>Guest-WiFi</code> &rarr; <code>Policy-Guest</code>.",
            "Assign the Policy Tag to target APs via <strong>Configuration &rsaquo; Wireless &rsaquo; Access Points</strong>.",
        ],
        "expected": "Guest clients associate to Guest-WiFi without a password and are placed on VLAN 200. On first HTTP request, they are redirected to the Cisco captive portal login page. After login, internet access is granted.",
        "verify": "Connect a test device to Guest-WiFi. Open a browser and navigate to any HTTP site — you should see the WLC login page.",
    },
    {
        "id": "ex5",
        "num": 5,
        "title": "Run a Radioactive Trace on a Failing Client",
        "difficulty": "easy",
        "scenario": "<strong>Scenario:</strong> A user reports their laptop (MAC: <code>AA:BB:CC:DD:EE:FF</code>) cannot connect to the corporate SSID. Use Radioactive Trace to capture the failure.",
        "steps": [
            "Navigate to <strong>Troubleshooting &rsaquo; Radioactive Trace</strong>.",
            "Click <strong>+ Add</strong>. Enter MAC address: <code>AA:BB:CC:DD:EE:FF</code>. Click <strong>Apply to Device</strong>.",
            "Click <strong>Start</strong> next to the MAC entry — debug collection begins.",
            "On the client device: forget the network and attempt to reconnect (or re-enable Wi-Fi).",
            "Wait 30–60 seconds to capture the full authentication sequence.",
            "Click <strong>Stop</strong> to end the trace.",
            "Click <strong>Log Download</strong> to save the trace log file (.txt).",
            "Open the log file and search for keywords: <code>FAILED</code>, <code>REJECT</code>, <code>ERROR</code>, <code>TIMEOUT</code>, <code>policy</code>.",
            "Common findings: RADIUS Access-Reject (wrong password/cert), DHCP timeout, Policy Tag missing WLAN mapping, PMF mismatch.",
        ],
        "expected": "A timestamped log file contains every control-plane event for the client MAC: probe, auth, assoc, 802.1X exchange, RADIUS response, DHCP, and policy application. The root cause of the failure is visible as an error or reject event.",
        "verify": "In the log, a successful authentication shows: <code>AUTHMGR-5-SUCCESS</code>. A RADIUS rejection shows: <code>Access-Reject</code>.",
    },
    {
        "id": "ex6",
        "num": 6,
        "title": "Perform a Packet Capture on an AP Radio",
        "difficulty": "medium",
        "scenario": "<strong>Scenario:</strong> An 802.1X client is failing silently — Radioactive Trace shows the session starting but no RADIUS response. Capture the actual EAPOL frames over the air on AP <em>AP-Floor2-01</em> to determine if EAP frames are reaching the client.",
        "steps": [
            "Navigate to <strong>Troubleshooting &rsaquo; Packet Capture</strong> and click <strong>+ Add</strong>.",
            "Set <strong>Capture Name</strong> = <code>PCAP-EAP-Debug</code>.",
            "Select <strong>AP Name</strong> = <code>AP-Floor2-01</code>.",
            "Select the radio the client is using: <strong>radio1</strong> (5 GHz) or <strong>radio0</strong> (2.4 GHz). Check Monitoring &rsaquo; Clients first to confirm the band.",
            "Set <strong>Direction</strong> = Both, <strong>Duration</strong> = 60 seconds, <strong>Buffer Size</strong> = 10 MB.",
            "Optionally set <strong>Inner MAC filter</strong> = <code>AA:BB:CC:DD:EE:FF</code> to capture only the target client's frames.",
            "Click <strong>Start</strong>. Immediately attempt to connect the client device.",
            "After 60 seconds (or click <strong>Stop</strong> early), click <strong>Download</strong> to save the .pcap file.",
            "Open in Wireshark. Apply filter: <code>eapol</code>. Analyze the EAP conversation — look for EAP-Request, EAP-Response, and whether EAP-Success or EAP-Failure is received.",
        ],
        "expected": "Wireshark shows the EAPOL 4-way handshake or EAP exchange. If EAP-Failure or no EAP-Success frame is visible, the issue is in the RADIUS exchange or the supplicant configuration. If no EAPOL frames at all are captured, the client may not be attempting 802.1X.",
        "verify": "Wireshark filter <code>eapol</code> reveals: EAP Start &rarr; EAP-Request Identity &rarr; EAP-Response Identity &rarr; EAP-Success (or EAP-Failure).",
    },
    {
        "id": "ex7",
        "num": 7,
        "title": "Create and Apply a Custom RF Profile",
        "difficulty": "medium",
        "scenario": "<strong>Scenario:</strong> The 5 GHz band on your APs is using too-wide channels, causing co-channel interference. Create an RF Profile that limits DCA to channels 36–64, uses 40 MHz width, and caps Tx Power at 17 dBm.",
        "steps": [
            "Navigate to <strong>Configuration &rsaquo; Tags &amp; Profiles &rsaquo; RF</strong> and click <strong>+ Add</strong>.",
            "Set <strong>Profile Name</strong> = <code>RF-5GHz-Corp</code>, <strong>Band</strong> = 5 GHz.",
            "Under <strong>RF Profile General</strong>: set <strong>Maximum Transmit Power</strong> = 17 dBm, <strong>Minimum Transmit Power</strong> = 5 dBm.",
            "Under <strong>DCA</strong>: ensure DCA is Enabled. Click <strong>Channel Assignment</strong> and select only channels 36, 40, 44, 48, 52, 56, 60, 64 (UNII-1 and UNII-2A). Deselect all DFS/UNII-3 channels.",
            "Set <strong>Channel Width</strong> = 40 MHz.",
            "Enable <strong>TPC</strong> (Transmit Power Control). Leave algorithm = Automatic.",
            "Click <strong>Save &amp; Apply to Device</strong>.",
            "Navigate to <strong>Configuration &rsaquo; Tags &amp; Profiles &rsaquo; Tags &rsaquo; RF</strong> and click <strong>+ Add</strong>.",
            "Set <strong>Tag Name</strong> = <code>Tag-RF-Corp</code>. Set <strong>5 GHz Band RF Profile</strong> = <code>RF-5GHz-Corp</code>.",
            "Click <strong>Save &amp; Apply to Device</strong>.",
            "Navigate to <strong>Configuration &rsaquo; Wireless &rsaquo; Access Points</strong>. Select target APs and assign <strong>RF Tag</strong> = <code>Tag-RF-Corp</code>.",
        ],
        "expected": "APs using Tag-RF-Corp now operate only on channels 36–64 with 40 MHz channel width and a maximum of 17 dBm. Verify under Monitoring &rsaquo; Access Points — Channel column shows only channels in the 36–64 range.",
        "verify": "CLI: <code>show ap dot11 5ghz summary</code> — verify channels and power levels.",
    },
    {
        "id": "ex8",
        "num": 8,
        "title": "Configure a Client ACL to Restrict Guest Traffic",
        "difficulty": "medium",
        "scenario": "<strong>Scenario:</strong> Guest clients on VLAN 200 must not be able to reach the corporate network (10.0.0.0/8). Create an ACL and apply it to the Guest Policy Profile.",
        "steps": [
            "Navigate to <strong>Configuration &rsaquo; Security &rsaquo; ACL</strong> and click <strong>+ Add</strong>.",
            "Set <strong>ACL Name</strong> = <code>ACL-Block-Corporate</code>, <strong>Type</strong> = IPv4 Extended.",
            "Click <strong>+ Add</strong> to add ACE 1: Action = <strong>Deny</strong>, Protocol = IP, Source = <code>any</code>, Destination = <code>10.0.0.0 / 0.255.255.255</code>. Sequence = 10.",
            "Click <strong>+ Add</strong> to add ACE 2: Action = <strong>Permit</strong>, Protocol = IP, Source = <code>any</code>, Destination = <code>any</code>. Sequence = 20.",
            "Click <strong>Save &amp; Apply to Device</strong>.",
            "Navigate to <strong>Configuration &rsaquo; Tags &amp; Profiles &rsaquo; Policy</strong>, edit <code>Policy-Guest</code>.",
            "Under <strong>Access Policies</strong>: set <strong>IPv4 ACL</strong> = <code>ACL-Block-Corporate</code> (apply as Egress or both directions depending on requirement).",
            "Click <strong>Save &amp; Apply to Device</strong>.",
        ],
        "expected": "Guest clients on VLAN 200 cannot ping or access any 10.0.0.0/8 address. Internet access (non-10.0.0.0/8 destinations) remains functional. Verify by trying <code>ping 10.1.1.1</code> from a guest device — should timeout.",
        "verify": "CLI: <code>show ip access-lists ACL-Block-Corporate</code> — match counters increment when guest traffic hits the deny rule.",
    },
    {
        "id": "ex9",
        "num": 9,
        "title": "Upgrade WLC Software to 17.9.5",
        "difficulty": "hard",
        "scenario": "<strong>Scenario:</strong> The WLC is running 17.9.3 and must be upgraded to 17.9.5. An SFTP server at 192.168.1.50 hosts the image. Perform the upgrade with AP pre-download to minimize downtime.",
        "steps": [
            "Download the IOS-XE 17.9.5 image from <strong>Cisco Software Download</strong> (requires valid CCO/service contract). Filename format: <code>C9800-universalk9_wlc.17.09.05.SPA.bin</code>.",
            "Place the image on your SFTP server at <code>192.168.1.50</code> in the configured SFTP directory.",
            "Navigate to <strong>Administration &rsaquo; Software Management &rsaquo; Software Upgrade</strong>.",
            "Set <strong>Transfer Mode</strong> = SFTP, <strong>Server IP</strong> = <code>192.168.1.50</code>, <strong>Username</strong> and <strong>Password</strong> for SFTP access, <strong>File Path</strong> = path to the .bin file.",
            "Click <strong>Download</strong>. Monitor the download progress bar — this may take 5–15 minutes.",
            "After successful download, verify the new version appears under <strong>Current Version</strong> on the upgrade page.",
            "<strong>Before activating the WLC:</strong> click <strong>AP Pre-download</strong>. This pushes the new image to all joined APs in the background.",
            "Monitor <strong>Monitoring &rsaquo; Wireless &rsaquo; Access Points</strong> — wait until all APs show <strong>Pre-downloaded</strong> status.",
            "Schedule or immediately click <strong>Activate</strong>. The WLC will save config and reload into the new image.",
            "WLC outage lasts approximately 5–7 minutes. APs enter standalone mode, existing client sessions on FlexConnect APs with local switching continue.",
            "After WLC comes back online, verify version: <strong>Administration &rsaquo; Software Management</strong> shows 17.9.5. Check all APs rejoin.",
        ],
        "expected": "WLC and all APs running IOS-XE 17.9.5. No permanent AP or client loss. APs that were pre-downloaded reload simultaneously with the WLC — typical downtime is 5–10 minutes total.",
        "verify": "CLI: <code>show version</code> — confirms IOS-XE 17.09.05. GUI: Administration &rsaquo; Software Management shows 17.9.5.",
    },
    {
        "id": "ex10",
        "num": 10,
        "title": "Investigate RF Interference with CleanAir",
        "difficulty": "easy",
        "scenario": "<strong>Scenario:</strong> Users on Floor 3 report intermittent Wi-Fi drops every few minutes. You suspect a non-802.11 interferer. Use CleanAir and RF statistics to identify and mitigate the issue.",
        "steps": [
            "Navigate to <strong>Monitoring &rsaquo; RF &rsaquo; RF Statistics</strong>. Filter by APs on Floor 3.",
            "Check <strong>Channel Utilization</strong>: values above 70% indicate congestion. Note which channels are most affected.",
            "Check <strong>Noise Floor</strong>: values worse than −85 dBm indicate a noise problem.",
            "Navigate to <strong>Monitoring &rsaquo; RF &rsaquo; Spectrum</strong> (CleanAir). Look for detected interferers.",
            "Note interferer <strong>Type</strong> (Microwave, DECT, Bluetooth, Video Camera, Jammer), <strong>Channel</strong>, <strong>Severity</strong>, and <strong>Duty Cycle</strong>.",
            "Identify the <strong>Closest AP</strong> to the interferer — use this to physically locate the interference source.",
            "Mitigation options: (a) Remove/relocate the interfering device. (b) Edit the RF Profile to exclude the affected channel from DCA. (c) Enable Event Driven RRM to trigger an immediate channel change when interference is detected.",
            "To exclude a channel: navigate to <strong>Configuration &rsaquo; Tags &amp; Profiles &rsaquo; RF</strong>, edit the relevant RF Profile, remove the affected channel from the DCA channel list.",
            "To enable ED-RRM: in the RF Profile, enable <strong>Event Driven RRM</strong> with sensitivity = Medium.",
        ],
        "expected": "CleanAir identifies the interferer type and affected channel. After excluding the channel from DCA or relocating the interfering device, channel utilization and noise floor return to normal levels. Client drop rate decreases.",
        "verify": "Monitoring &rsaquo; RF &rsaquo; RF Statistics — confirm Channel Utilization drops below 50% and Noise Floor improves to < −90 dBm after mitigation.",
    },
]

# ============================================================================
# QUIZ DATA
# ============================================================================
QUIZ_QUESTIONS = [
    # ── CATEGORY A: Menu Knowledge ──────────────────────────────────────────
    {
        "cat": "A",
        "q": "Where do you create a new WLAN profile (SSID) on the Cisco 9800?",
        "opts": [
            ("A", "Configuration &rsaquo; Wireless &rsaquo; WLANs"),
            ("B", "Configuration &rsaquo; Tags &amp; Profiles &rsaquo; Policy"),
            ("C", "Administration &rsaquo; Wireless &rsaquo; SSIDs"),
            ("D", "Monitoring &rsaquo; Wireless &rsaquo; WLANs"),
        ],
        "correct": "A",
        "exp": "WLAN profiles (SSIDs) are created under Configuration &rsaquo; Wireless &rsaquo; WLANs. The Policy section is for Policy Profiles, not WLAN profiles.",
    },
    {
        "cat": "A",
        "q": "Where do you statically assign Policy, Site, and RF Tags to a specific AP?",
        "opts": [
            ("A", "Monitoring &rsaquo; Access Points"),
            ("B", "Configuration &rsaquo; Wireless &rsaquo; Access Points"),
            ("C", "Configuration &rsaquo; Tags &amp; Profiles &rsaquo; Tags &rsaquo; Policy"),
            ("D", "Administration &rsaquo; AP Management"),
        ],
        "correct": "B",
        "exp": "Tag assignment to individual APs is done under Configuration &rsaquo; Wireless &rsaquo; Access Points. You click the AP name and then change each tag in the General tab.",
    },
    {
        "cat": "A",
        "q": "Where do you configure a RADIUS server on the Cisco 9800?",
        "opts": [
            ("A", "Configuration &rsaquo; Security &rsaquo; AAA &rsaquo; Servers/Groups &rsaquo; Servers"),
            ("B", "Administration &rsaquo; AAA &rsaquo; RADIUS"),
            ("C", "Configuration &rsaquo; Wireless &rsaquo; Security"),
            ("D", "Configuration &rsaquo; Tags &amp; Profiles &rsaquo; Security"),
        ],
        "correct": "A",
        "exp": "RADIUS servers are added under Configuration &rsaquo; Security &rsaquo; AAA &rsaquo; Servers/Groups &rsaquo; Servers. After adding the server, it must be placed in a Server Group and referenced in a Method List.",
    },
    {
        "cat": "A",
        "q": "Where do you run a Radioactive Trace on the 9800 WebUI?",
        "opts": [
            ("A", "Monitoring &rsaquo; Wireless &rsaquo; Clients"),
            ("B", "Administration &rsaquo; Debug"),
            ("C", "Troubleshooting &rsaquo; Radioactive Trace"),
            ("D", "Configuration &rsaquo; Diagnostic &rsaquo; Trace"),
        ],
        "correct": "C",
        "exp": "Radioactive Trace is located under Troubleshooting &rsaquo; Radioactive Trace. It is the primary per-device conditional debug tool on the 9800.",
    },
    {
        "cat": "A",
        "q": "Where do you configure a Flex Profile for FlexConnect deployments?",
        "opts": [
            ("A", "Configuration &rsaquo; Wireless &rsaquo; Mesh"),
            ("B", "Configuration &rsaquo; Tags &amp; Profiles &rsaquo; Flex"),
            ("C", "Configuration &rsaquo; Tags &amp; Profiles &rsaquo; Tags &rsaquo; Site"),
            ("D", "Configuration &rsaquo; Security &rsaquo; FlexConnect"),
        ],
        "correct": "B",
        "exp": "Flex Profiles are created under Configuration &rsaquo; Tags &amp; Profiles &rsaquo; Flex. The Site Tag then references the Flex Profile to put APs into FlexConnect mode.",
    },
    {
        "cat": "A",
        "q": "Where do you perform a software upgrade on the Cisco 9800?",
        "opts": [
            ("A", "Administration &rsaquo; Software Management &rsaquo; Software Upgrade"),
            ("B", "Administration &rsaquo; Licensing"),
            ("C", "Configuration &rsaquo; System &rsaquo; Software"),
            ("D", "Troubleshooting &rsaquo; System &rsaquo; Upgrade"),
        ],
        "correct": "A",
        "exp": "Software upgrades are performed under Administration &rsaquo; Software Management &rsaquo; Software Upgrade. Always pre-download to APs before activating.",
    },
    {
        "cat": "A",
        "q": "Where can you view non-802.11 interference detected by CleanAir?",
        "opts": [
            ("A", "Configuration &rsaquo; Tags &amp; Profiles &rsaquo; RF"),
            ("B", "Monitoring &rsaquo; RF &rsaquo; Spectrum"),
            ("C", "Monitoring &rsaquo; Wireless &rsaquo; Rogues"),
            ("D", "Troubleshooting &rsaquo; RF &rsaquo; Spectrum"),
        ],
        "correct": "B",
        "exp": "CleanAir spectrum data (non-802.11 interferer detection) is found under Monitoring &rsaquo; RF &rsaquo; Spectrum. This requires CleanAir-capable APs.",
    },
    {
        "cat": "A",
        "q": "Where do you create RF Profiles that control channel width and DCA settings?",
        "opts": [
            ("A", "Configuration &rsaquo; Tags &amp; Profiles &rsaquo; RF (under Profiles)"),
            ("B", "Configuration &rsaquo; Wireless &rsaquo; RF"),
            ("C", "Configuration &rsaquo; Tags &amp; Profiles &rsaquo; Tags &rsaquo; RF"),
            ("D", "Monitoring &rsaquo; RF &rsaquo; Profiles"),
        ],
        "correct": "A",
        "exp": "RF Profiles are created under Configuration &rsaquo; Tags &amp; Profiles &rsaquo; RF (the Profiles section, not the Tags section). RF Tags then reference these profiles.",
    },
    {
        "cat": "A",
        "q": "Where do you configure Web Authentication (captive portal) settings on the 9800?",
        "opts": [
            ("A", "Configuration &rsaquo; Wireless &rsaquo; WLANs &rsaquo; Layer 3"),
            ("B", "Configuration &rsaquo; Security &rsaquo; Web Auth"),
            ("C", "Administration &rsaquo; AAA &rsaquo; Web Auth"),
            ("D", "Configuration &rsaquo; Tags &amp; Profiles &rsaquo; Policy"),
        ],
        "correct": "B",
        "exp": "Global Web Auth parameters (virtual IP, login page) are configured under Configuration &rsaquo; Security &rsaquo; Web Auth. The WLAN Layer 3 security setting then enables Web Policy per SSID.",
    },
    {
        "cat": "A",
        "q": "Where do you view all rogue APs detected in your wireless environment?",
        "opts": [
            ("A", "Monitoring &rsaquo; Wireless &rsaquo; Rogues"),
            ("B", "Configuration &rsaquo; Security &rsaquo; Wireless Protection Policies"),
            ("C", "Troubleshooting &rsaquo; Network &rsaquo; Rogues"),
            ("D", "Administration &rsaquo; Security &rsaquo; Rogues"),
        ],
        "correct": "A",
        "exp": "Detected rogue APs and clients are listed under Monitoring &rsaquo; Wireless &rsaquo; Rogues. Rogue containment and classification rules are configured separately under Configuration &rsaquo; Security &rsaquo; Wireless Protection Policies.",
    },
    # ── CATEGORY B: Concepts ────────────────────────────────────────────────
    {
        "cat": "B",
        "q": "What is the primary function of the Site Tag on the Cisco 9800?",
        "opts": [
            ("A", "Maps SSIDs to VLANs and defines client switching mode"),
            ("B", "Controls AP operating mode (Local vs FlexConnect) and references the AP Join Profile"),
            ("C", "Assigns radio channel and transmit power settings per band"),
            ("D", "Defines which RADIUS server to use for client authentication"),
        ],
        "correct": "B",
        "exp": "The Site Tag controls AP operating mode: if a Flex Profile is attached the AP enters FlexConnect mode; without it, the AP operates in Local mode. It also references the AP Join Profile which controls management settings.",
    },
    {
        "cat": "B",
        "q": "What happens when you attach a Flex Profile to a Site Tag?",
        "opts": [
            ("A", "APs reboot into Mesh Bridge mode"),
            ("B", "APs switch to FlexConnect operating mode"),
            ("C", "APs enable local web authentication only"),
            ("D", "APs begin using local RADIUS instead of central AAA"),
        ],
        "correct": "B",
        "exp": "Attaching a Flex Profile to a Site Tag causes all APs referencing that tag to operate in FlexConnect mode. This allows local data switching at the AP/branch level.",
    },
    {
        "cat": "B",
        "q": "Which profile directly controls the VLAN that wireless clients are placed on?",
        "opts": [
            ("A", "AP Join Profile"),
            ("B", "RF Profile"),
            ("C", "Policy Profile"),
            ("D", "Flex Profile"),
        ],
        "correct": "C",
        "exp": "The Policy Profile contains the VLAN assignment for client traffic, along with the switching mode (Central/Local), ACL, and QoS settings. It is referenced by Policy Tags.",
    },
    {
        "cat": "B",
        "q": "What is the name of the default Policy Tag on the Cisco 9800?",
        "opts": [
            ("A", "global-policy-tag"),
            ("B", "default-policy-tag"),
            ("C", "system-policy-tag"),
            ("D", "base-policy-tag"),
        ],
        "correct": "B",
        "exp": "The three default tags are: default-policy-tag, default-site-tag, and default-rf-tag. Any AP not explicitly assigned a custom tag inherits these defaults.",
    },
    {
        "cat": "B",
        "q": "In a Policy Profile, what does enabling 'Central Switching' mean for client traffic?",
        "opts": [
            ("A", "The AP switches client traffic locally without involving the WLC"),
            ("B", "All client data frames are tunneled via CAPWAP to the WLC for forwarding"),
            ("C", "The WLC uses a central aggregated VLAN for all SSIDs simultaneously"),
            ("D", "Clients authenticate centrally but their data bypasses the WLC"),
        ],
        "correct": "B",
        "exp": "Central Switching means all client data frames are encapsulated in CAPWAP and sent to the WLC, which then forwards them into the wired network. This is the default mode for Local-mode APs.",
    },
    {
        "cat": "B",
        "q": "How many Policy Tags, Site Tags, and RF Tags can a single AP have assigned simultaneously?",
        "opts": [
            ("A", "Multiple of each — one per SSID"),
            ("B", "One Policy Tag, multiple Site Tags, one RF Tag"),
            ("C", "Exactly one of each tag type"),
            ("D", "One Policy Tag and one RF Tag, unlimited Site Tags"),
        ],
        "correct": "C",
        "exp": "Each AP has exactly ONE Policy Tag, ONE Site Tag, and ONE RF Tag at any given time. This is a fundamental constraint of the 9800 configuration model.",
    },
    {
        "cat": "B",
        "q": "Which 802.11 standard introduced the 6 GHz band (Wi-Fi 6E)?",
        "opts": [
            ("A", "802.11ac (Wi-Fi 5)"),
            ("B", "802.11ax limited to 5 GHz only"),
            ("C", "802.11ax extended to include 6 GHz (Wi-Fi 6E)"),
            ("D", "802.11be (Wi-Fi 7)"),
        ],
        "correct": "C",
        "exp": "Wi-Fi 6E extends 802.11ax into the 6 GHz band (5.925–7.125 GHz), providing additional spectrum free of legacy device interference. Cisco 9130AXE and 9136 series support 6 GHz.",
    },
    {
        "cat": "B",
        "q": "A FlexConnect AP loses its WAN connection to the WLC. With Local Switching configured, what happens to connected clients?",
        "opts": [
            ("A", "All clients are immediately deauthenticated"),
            ("B", "Clients remain connected; traffic is switched locally at the AP (standalone mode)"),
            ("C", "The AP reboots and clients must reconnect via 4G backup"),
            ("D", "Clients are moved to a fallback SSID with degraded connectivity"),
        ],
        "correct": "B",
        "exp": "FlexConnect APs in standalone mode (WAN down) continue to switch client traffic locally. Clients with locally switched SSIDs remain connected. New client authentication uses cached credentials or a local RADIUS server.",
    },
    {
        "cat": "B",
        "q": "The 'Enable Local Site' checkbox in a Site Tag is unchecked. What does this indicate?",
        "opts": [
            ("A", "The AP will not broadcast any SSIDs locally"),
            ("B", "The APs are at a remote/branch site — typically used with FlexConnect"),
            ("C", "The site has no physical APs — it is a virtual site"),
            ("D", "Local DHCP is disabled for this site"),
        ],
        "correct": "B",
        "exp": "Unchecking 'Enable Local Site' signals that APs are at a remote site (not directly connected to the WLC). Combined with a Flex Profile, this puts APs into FlexConnect remote-branch mode.",
    },
    {
        "cat": "B",
        "q": "What High Availability mechanism does the Cisco 9800 WLC use for controller redundancy?",
        "opts": [
            ("A", "HSRP (Hot Standby Router Protocol) in Active/Standby"),
            ("B", "Stateful Switchover (SSO) with a dedicated HA port",),
            ("C", "VRRP (Virtual Router Redundancy Protocol)"),
            ("D", "Active/Active clustering with load balancing"),
        ],
        "correct": "B",
        "exp": "The 9800 uses Stateful Switchover (SSO) for HA. The primary and secondary WLCs synchronize state over a dedicated HA port. On failover, client sessions are maintained (stateful) with minimal disruption.",
    },
    # ── CATEGORY C: Scenarios ───────────────────────────────────────────────
    {
        "cat": "C",
        "q": "An AP joins the WLC and clients associate, but they receive the wrong VLAN. What is the most likely cause?",
        "opts": [
            ("A", "The RF Tag is pointing to the wrong RF Profile"),
            ("B", "The Policy Profile has an incorrect VLAN configured"),
            ("C", "The Site Tag is missing a Flex Profile"),
            ("D", "The AP Join Profile has incorrect NTP settings"),
        ],
        "correct": "B",
        "exp": "Client VLAN assignment is controlled by the Policy Profile. If clients are landing on the wrong VLAN, the Policy Profile referenced in the Policy Tag has the wrong VLAN configured.",
    },
    {
        "cat": "C",
        "q": "You create a new WLAN and set Status = Enabled, but the SSID is not visible on any client device. What must you check first?",
        "opts": [
            ("A", "The RF Tag must explicitly reference this WLAN"),
            ("B", "The WLAN must be mapped in a Policy Tag, and that tag must be assigned to APs"),
            ("C", "The WLAN must be linked to the AP Join Profile"),
            ("D", "The Site Tag must include the WLAN name in its configuration"),
        ],
        "correct": "B",
        "exp": "A WLAN profile alone does not broadcast. It must be: (1) Enabled, (2) mapped to a Policy Profile in a Policy Tag, and (3) the Policy Tag must be assigned to APs. Missing any of these three steps causes the SSID to not broadcast.",
    },
    {
        "cat": "C",
        "q": "A branch office has 3 APs in FlexConnect mode. The WAN link fails. Which clients lose connectivity?",
        "opts": [
            ("A", "All clients — FlexConnect requires constant WLC connectivity"),
            ("B", "Only new clients trying to join; existing locally-switched clients stay connected"),
            ("C", "Only clients on central-switched SSIDs; locally-switched clients stay connected"),
            ("D", "All clients on 5 GHz; 2.4 GHz clients are unaffected"),
        ],
        "correct": "C",
        "exp": "During a WAN outage, FlexConnect APs enter standalone mode. Clients on locally-switched SSIDs remain connected. Clients on centrally-switched SSIDs lose connectivity because their data must reach the WLC.",
    },
    {
        "cat": "C",
        "q": "An AP is stuck in 'Discovering' state and never joins the WLC. What should you check FIRST?",
        "opts": [
            ("A", "Verify the RF Tag is correctly assigned to the AP"),
            ("B", "Verify CAPWAP connectivity: DNS resolution, DHCP option 43, or controller IP reachability"),
            ("C", "Verify the Policy Tag contains at least one WLAN mapping"),
            ("D", "Ensure the AP is running the same IOS-XE version as the WLC"),
        ],
        "correct": "B",
        "exp": "An AP in Discovering state has not established a CAPWAP control channel with the WLC. Check: DNS lookup for 'CISCO-CAPWAP-CONTROLLER.localdomain', DHCP option 43 (controller IP), or static controller IP configured on the AP. Tags are irrelevant if the AP cannot even reach the WLC.",
    },
    {
        "cat": "C",
        "q": "Users on Floor 5 report intermittent drops every 3–5 minutes at the same time every day. What tool do you use FIRST to investigate?",
        "opts": [
            ("A", "Radioactive Trace on affected client MACs"),
            ("B", "Monitoring &rsaquo; RF &rsaquo; Spectrum (CleanAir) to check for interference"),
            ("C", "Packet Capture on the AP radio"),
            ("D", "Monitoring &rsaquo; Wireless &rsaquo; Rogues"),
        ],
        "correct": "B",
        "exp": "Periodic, time-based interference (every few minutes) strongly suggests a non-802.11 device such as a microwave oven, DECT phone, or wireless video camera. CleanAir Spectrum analysis is the correct first step to identify the source.",
    },
    {
        "cat": "C",
        "q": "A security audit requires per-user dynamic VLAN assignment from RADIUS for 802.1X clients. Which setting must be enabled in the Policy Profile?",
        "opts": [
            ("A", "Central DHCP"),
            ("B", "AAA Override"),
            ("C", "NAC (Network Admission Control)"),
            ("D", "Web Policy"),
        ],
        "correct": "B",
        "exp": "AAA Override must be enabled in the Policy Profile to allow RADIUS to dynamically override the VLAN, ACL, or QoS policy on a per-client basis using Cisco VSA attributes (e.g., Tunnel-Private-Group-ID for VLAN).",
    },
    {
        "cat": "C",
        "q": "After upgrading the WLC from 17.9.3 to 17.9.5, several APs show 'Image Mismatch' status. What is the correct action?",
        "opts": [
            ("A", "Delete and re-add the APs from the WLC"),
            ("B", "Reset the Site Tag on the affected APs to trigger a reload"),
            ("C", "Trigger AP image pre-download and then reload the affected APs"),
            ("D", "Downgrade the WLC back to 17.9.3 to match the APs"),
        ],
        "correct": "C",
        "exp": "Image Mismatch means the AP image version does not match the WLC. Navigate to Administration &rsaquo; Software Management and trigger an AP Pre-download. APs will download the correct image and reload to resolve the mismatch.",
    },
    {
        "cat": "C",
        "q": "You need two SSIDs on the same AP: one corporate (central switching, VLAN 10) and one guest (local switching, VLAN 200). What is required?",
        "opts": [
            ("A", "Two separate WLANs with two Policy Profiles, both mapped in one Policy Tag"),
            ("B", "Two separate Policy Tags — one per SSID — both assigned to the same AP"),
            ("C", "One WLAN with dual-VLAN configuration in the Policy Profile"),
            ("D", "Two APs — one cannot serve both central and local switching simultaneously"),
        ],
        "correct": "A",
        "exp": "One Policy Tag can contain multiple WLAN-Policy mappings. Create two WLANs (Corp and Guest), two Policy Profiles (central switching VLAN 10, local switching VLAN 200), and map both in the same Policy Tag assigned to the AP.",
    },
    {
        "cat": "C",
        "q": "An 802.1X client connects but Radioactive Trace shows the RADIUS server returning an Access-Reject. The network team confirms the server is healthy. What is the most likely issue?",
        "opts": [
            ("A", "The RF Tag is missing a 5 GHz RF Profile"),
            ("B", "The RADIUS shared key on the WLC does not match the server configuration"),
            ("C", "The Site Tag has Local Site unchecked"),
            ("D", "Central DHCP is disabled in the Policy Profile"),
        ],
        "correct": "B",
        "exp": "Access-Reject (not a timeout or unreachable) means the RADIUS server received and processed the request but denied it. The most common cause when the server is known healthy is a shared-key mismatch — the RADIUS server cannot decrypt the authentication request and rejects it.",
    },
    {
        "cat": "C",
        "q": "You want to capture the actual EAPOL frames exchanged between a client and an AP. Which tool provides this?",
        "opts": [
            ("A", "Radioactive Trace — it captures EAPOL at the control-plane level"),
            ("B", "Troubleshooting &rsaquo; Packet Capture on the AP radio"),
            ("C", "Monitoring &rsaquo; Wireless &rsaquo; Clients &rsaquo; Client Detail"),
            ("D", "Administration &rsaquo; Logging with debug dot1x enabled"),
        ],
        "correct": "B",
        "exp": "Packet Capture on the AP radio captures raw 802.11 frames over the air, including EAPOL. The resulting .pcap file shows the exact EAP message exchange. Radioactive Trace shows the WLC-side control-plane view, not the raw frames.",
    },
]

# ============================================================================
# HTML BUILDERS
# ============================================================================

def build_menu_guide():
    sidebar = "".join(MENU_SIDEBAR)

    body = """<div class="card"><div class="card-head">
<div class="icon">📖</div>
<h2>Cisco 9800 WLC WebUI — Complete Menu Reference</h2>
<span class="tag-badge">IOS-XE 17.9.5</span>
</div><div class="card-body">
<p>This guide covers every major section of the Cisco Catalyst 9800 Wireless LAN Controller web interface. Each section includes the navigation path, key fields and their defaults, screenshot placeholders, and operational notes. Use the sidebar to jump directly to any menu section.</p>
</div></div>"""

    for sec in MENU_SECTIONS:
        notes_html = "".join(nt(k, t) for k, t in sec["notes"])
        table_html = ftable(sec["fields"])
        nav_html = navp(sec["nav"])
        sc_html = sc(sec["nav"], sec["screenshot_label"])

        body += f"""<div class="card" id="{sec['id']}">
<div class="card-head"><div class="icon">{sec['icon']}</div>
<h2>{sec['title']}</h2></div>
<div class="card-body">
<p>{sec['desc']}</p>
{nav_html}
{sc_html}
<div class="subsec"><h3>Key Fields &amp; Settings</h3>
{table_html}</div>
{notes_html}
</div></div>"""

    out = page("Menu Reference Guide",
               "Complete WebUI navigation reference for Network Engineers",
               sidebar, body)
    path = os.path.join(OUTPUT_DIR, "01_menu_guide.html")
    with open(path, "w", encoding="utf-8") as f:
        f.write(out)
    print(f"  [OK] {path}")


def build_exercises():
    sidebar = "".join([
        sbg("Exercises", [(f"ex{i}", f"Exercise {i}", "") for i in range(1, 11)])
    ])

    body = """<div class="card"><div class="card-head">
<div class="icon">🧪</div>
<h2>GUI-Based Lab Exercises</h2>
<span class="tag-badge">10 Labs</span>
</div><div class="card-body">
<p>These exercises guide you through real configuration tasks on the Cisco 9800 WLC WebUI. Each lab includes a scenario, step-by-step GUI navigation instructions, expected results, and a CLI verification command. Complete them in order for a progressive learning experience — later exercises build on earlier ones.</p>
</div></div>"""

    diff_map = {"easy": ("easy", "Easy"), "medium": ("medium", "Medium"), "hard": ("hard", "Hard")}

    for ex in EXERCISES:
        dc, dl = diff_map[ex["difficulty"]]
        steps_li = "".join(f"<li>{s}</li>" for s in ex["steps"])
        body += f"""<div class="ex-card" id="{ex['id']}">
<div class="ex-header">
  <div class="ex-num">{ex['num']}</div>
  <h3>{ex['title']}</h3>
  <span class="diff {dc}">{dl}</span>
</div>
<div class="ex-body">
  <div class="scenario">{ex['scenario']}</div>
  <ol class="steps">{steps_li}</ol>
  <div class="expected"><strong>✅ Expected Result:</strong> {ex['expected']}</div>
  <div class="verify"><strong>🔍 Verification:</strong> {ex['verify']}</div>
</div>
</div>"""

    out = page("Lab Exercises",
               "10 hands-on GUI-based configuration exercises",
               sidebar, body)
    path = os.path.join(OUTPUT_DIR, "02_exercises.html")
    with open(path, "w", encoding="utf-8") as f:
        f.write(out)
    print(f"  [OK] {path}")


def build_quiz():
    cats = {"A": ("Menu Knowledge", "📍"), "B": ("Concepts & Behavior", "🧠"), "C": ("Scenarios", "🎯")}
    sidebar = "".join([
        sbg("Quiz", [
            ("cat-a", "Category A: Menu Knowledge", ""),
            ("cat-b", "Category B: Concepts", ""),
            ("cat-c", "Category C: Scenarios", ""),
        ])
    ])

    bar = """<div class="quiz-bar">
<h2>🏆 Cisco 9800 WLC — Scored Quiz</h2>
<div class="pbwrap"><div id="pb"></div></div>
<div id="sd">0 / 0</div>
<button class="btn btn-s" onclick="resetQ()">↺ Reset</button>
</div>
<div id="rp">
<h2>Quiz Complete</h2>
<div id="rsc" class="grade">0%</div>
<div id="rl" style="font-size:20px;font-weight:700;margin-bottom:8px"></div>
<div id="rd" style="color:#666;margin-bottom:24px"></div>
<button class="btn btn-p" onclick="resetQ()">Retry Quiz</button>
</div>"""

    body = bar
    qnum = 0
    last_cat = None

    for q in QUIZ_QUESTIONS:
        qnum += 1
        if q["cat"] != last_cat:
            last_cat = q["cat"]
            cname, cicon = cats[q["cat"]]
            body += f'<div class="qcat" id="cat-{q["cat"].lower()}">{cicon} Category {q["cat"]}: {cname}</div>'

        opts_html = ""
        for letter, text in q["opts"]:
            opts_html += f'<div class="opt" data-c="{letter}" onclick="choose({qnum},\'{letter}\',\'{q["correct"]}\',\'exp{qnum}\')">'
            opts_html += f'<span class="ol">{letter}</span><span>{text}</span></div>'

        body += f"""<div class="qcard" id="q{qnum}">
<div class="qtext"><span class="qnum">Q{qnum}.</span><span>{q['q']}</span></div>
<div class="opts">{opts_html}</div>
<div class="qexp" id="e{qnum}">💡 {q['exp']}</div>
</div>"""

    out = page("Quiz",
               "30-question scored quiz with instant feedback — pass mark 70%",
               sidebar, body, extra_js=QUIZ_JS)
    path = os.path.join(OUTPUT_DIR, "03_quiz.html")
    with open(path, "w", encoding="utf-8") as f:
        f.write(out)
    print(f"  [OK] {path}")


def build_tag_structure():
    sidebar = "".join([
        sbg("Overview", [
            ("overview", "TAG Architecture Overview", ""),
            ("three-tags", "The Three Tags", ""),
        ]),
        sbg("Deep Dive", [
            ("policy-tag", "Policy Tag", "sub"),
            ("site-tag", "Site Tag", "sub"),
            ("rf-tag", "RF Tag", "sub"),
            ("profiles", "Profiles Quick Reference", "sub"),
        ]),
        sbg("TAG Assignment", [
            ("assignment", "How Tags Are Assigned", ""),
            ("defaults-trap", "The Default Tags Trap", ""),
        ]),
        sbg("Examples", [
            ("eg1", "1 — Central Switching (Local mode)", "sub"),
            ("eg2", "2 — FlexConnect Local Switching", "sub"),
            ("eg3", "3 — Dual SSID: Corp + Guest", "sub"),
            ("eg4", "4 — Branch Failover", "sub"),
            ("eg5", "5 — FlexConnect Central Switching", "sub"),
            ("eg6", "6 — The Default Tag Trap", "sub"),
            ("eg7", "7 — Dynamic TAG via RADIUS", "sub"),
            ("eg8", "8 — SD-Access / Fabric Mode", "sub"),
        ]),
    ])

    body = f"""
<div class="tag-overview" id="overview">
  <h2>The Cisco 9800 TAG Architecture</h2>
  <p>Every AP joined to a Cisco 9800 WLC is assigned exactly <strong>three tags</strong>. Tags are pointers — they reference Profiles which contain the actual configuration. This separation makes large-scale changes efficient: update one profile and every AP using that tag inherits the change instantly.</p>
  <div class="tag-trio">
    <div class="tbox pol"><div class="tbi">🏷️</div><div class="tbt">Policy Tag</div><div class="tbd">What SSIDs the AP broadcasts<br>+ how clients are treated</div></div>
    <div class="tbox sit"><div class="tbi">🏢</div><div class="tbt">Site Tag</div><div class="tbd">How the AP operates<br>Local mode or FlexConnect</div></div>
    <div class="tbox rf"><div class="tbi">📡</div><div class="tbt">RF Tag</div><div class="tbd">Radio behavior per band<br>Channel, power, width</div></div>
  </div>
</div>

<div class="card" id="three-tags">
<div class="card-head"><div class="icon">🔑</div><h2>The Three Tags — Mental Model</h2></div>
<div class="card-body">
<p>Think of tags as <strong>personality slots</strong> on each AP. When an AP joins, the WLC checks which tags are assigned and loads the referenced configuration:</p>
<div class="diagram">
<div class="dt">AP joins WLC</div>
    │
    ├─ <span class="dtag">Policy Tag</span>  ->  <span class="dpr">Policy Profile</span>    (VLAN, switching mode, QoS, ACL)
    │                  ->  <span class="dpr">WLAN Profile(s)</span>  (which SSIDs to broadcast)
    │
    ├─ <span class="dtag">Site Tag</span>    ->  <span class="dpr">AP Join Profile</span>   (NTP, syslog, CAPWAP timers)
    │                  ->  <span class="dpr">Flex Profile</span>     (if present -> FlexConnect mode)
    │
    └─ <span class="dtag">RF Tag</span>      ->  <span class="dpr">RF Profile 2.4G</span>   (channel, power, DCA for 2.4 GHz)
                       ->  <span class="dpr">RF Profile 5G</span>    (channel, power, DCA for 5 GHz)
                       ->  <span class="dpr">RF Profile 6G</span>    (channel, power, DCA for 6 GHz)
</div>
{nt("info", "<strong>Key Rule:</strong> One AP = exactly one Policy Tag + one Site Tag + one RF Tag. You cannot assign multiple tags of the same type to a single AP.")}
{nt("success", "Tags and profiles are created independently. One profile can be referenced by many tags — change the profile once and all APs using it update immediately.")}
</div></div>

<div class="card" id="policy-tag">
<div class="card-head"><div class="icon">🏷️</div><h2>Policy Tag — Deep Dive</h2></div>
<div class="card-body">
<div class="subsec"><h3>Purpose</h3>
<p>The Policy Tag answers: <em>Which SSIDs does this AP broadcast, and what happens to clients on each SSID?</em> It is a mapping table: each row pairs a WLAN Profile (SSID definition) with a Policy Profile (client behavior).</p>
</div>
<div class="diagram">
<div class="dt">Policy Tag: Tag-HQ-Floor2</div>

  WLAN Profile        ->   Policy Profile
  ─────────────────────────────────────────
  <span class="dpr">Corp-WiFi6</span>         ->   <span class="dpr">Policy-Corp</span>     (<span class="dv">VLAN 10</span>, Central, 802.1X)
  <span class="dpr">Guest-WiFi</span>         ->   <span class="dpr">Policy-Guest</span>    (<span class="dv">VLAN 200</span>, Central, Web Auth)
  <span class="dpr">IoT-Sensors</span>        ->   <span class="dpr">Policy-IoT</span>      (<span class="dv">VLAN 300</span>, Local Switch, PSK)

<span class="dn">  ↑ up to 16 WLAN-Policy pairs per tag</span>
</div>
<div class="subsec"><h3>Key Constraints</h3></div>
<ul>
<li>Maximum <strong>16 WLAN-Policy mappings</strong> per Policy Tag</li>
<li>One AP can have only <strong>one Policy Tag</strong> — choose mappings carefully</li>
<li>The same WLAN Profile can appear in multiple Policy Tags (with different Policy Profiles) to serve different floors/sites differently</li>
<li>Removing a WLAN from a Policy Tag immediately stops that SSID on all APs with that tag — <strong>no grace period</strong></li>
</ul>
{navp(["Configuration", "Tags &amp; Profiles", "Tags", "Policy"])}
</div></div>

<div class="card" id="site-tag">
<div class="card-head"><div class="icon">🏢</div><h2>Site Tag — Deep Dive</h2></div>
<div class="card-body">
<div class="subsec"><h3>Purpose</h3>
<p>The Site Tag controls <strong>how the AP operates</strong> — its mode (Local or FlexConnect) and its management settings. It references two profiles:</p>
<ul>
<li><strong>AP Join Profile</strong> — always required. Controls NTP, syslog, CAPWAP timers, SSH access, statistics interval.</li>
<li><strong>Flex Profile</strong> — optional. <em>Its presence is what puts the AP into FlexConnect mode.</em></li>
</ul>
</div>
<div class="diagram">
<div class="dt">Site Tag Decision Logic</div>

  Site Tag has Flex Profile?
  │
  ├── <span class="dpr">NO</span>  -> AP operates in <span class="dtag">Local Mode</span>
  │           All client data tunneled via CAPWAP to WLC
  │           VLAN assignment: WLC-side (Policy Profile VLAN)
  │
  └── <span class="dpr">YES</span> -> AP operates in <span class="dtag">FlexConnect Mode</span>
              Client data can be switched locally at the AP
              VLAN assignment: Flex Profile VLAN override (branch VLAN)
              AP survives WAN outage in standalone mode
</div>
<div class="subsec"><h3>"Enable Local Site" Checkbox</h3></div>
<ul>
<li><strong>Checked (default)</strong> — APs are directly/locally connected to the WLC. Data keepalive and CAPWAP control traffic behave as if WLC is close.</li>
<li><strong>Unchecked</strong> — APs are at a remote site (branch over WAN). Combined with a Flex Profile = FlexConnect remote-branch deployment.</li>
</ul>
{nt("danger", "Adding or removing a Flex Profile from a live Site Tag causes all APs using that tag to change operating modes. This triggers a brief client disconnect (~5–10 seconds) as radios reset.")}
{navp(["Configuration", "Tags &amp; Profiles", "Tags", "Site"])}
</div></div>

<div class="card" id="rf-tag">
<div class="card-head"><div class="icon">📡</div><h2>RF Tag — Deep Dive</h2></div>
<div class="card-body">
<div class="subsec"><h3>Purpose</h3>
<p>The RF Tag controls <strong>radio behavior</strong> — channel selection, transmit power, channel width, and Wi-Fi generation settings per band. It references up to three RF Profiles: one per band (2.4 GHz, 5 GHz, 6 GHz).</p>
</div>
<div class="diagram">
<div class="dt">RF Tag: Tag-RF-Enterprise</div>

  Band     ->  RF Profile           Key Settings
  ──────────────────────────────────────────────────
  <span class="dpr">2.4 GHz</span>  ->  <span class="dpr">RF-2.4-Corp</span>     Ch 1/6/11, 20 MHz, TPC enabled
  <span class="dpr">5 GHz</span>    ->  <span class="dpr">RF-5-Corp</span>       Ch 36-64, 80 MHz, DCA, TPC
  <span class="dpr">6 GHz</span>    ->  <span class="dpr">RF-6-Corp</span>       Ch 1-93, 80/160 MHz (6E APs)

<span class="dn">  Different floor types can use different RF Tags for density tuning</span>
</div>
{nt("info", "You can use the same RF Profile for 2.4 GHz and 5 GHz, or create separate profiles for fine-grained control. A common practice is one RF Tag per 'zone type' (e.g., open office, conference room, warehouse).")}
{navp(["Configuration", "Tags &amp; Profiles", "Tags", "RF"])}
</div></div>

<div class="card" id="profiles">
<div class="card-head"><div class="icon">📋</div><h2>Profiles Quick Reference</h2></div>
<div class="card-body">
{ftable([
    ("AP Join Profile", "AP management behavior: NTP, syslog, CAPWAP timers, SSH, LED, stats interval. Referenced by Site Tag.", "default-ap-join-profile"),
    ("Policy Profile", "Client data plane: VLAN, Central/Local switching, Central/Local DHCP, ACL, QoS, AAA Override, NAC, mDNS. Referenced by Policy Tag.", "default-policy-profile"),
    ("RF Profile", "Radio behavior per band: channel, power range, channel width, DCA, TPC, BSS Color, 802.11ax. Referenced by RF Tag.", "default-rf-profile"),
    ("Flex Profile", "FlexConnect-specific: VLAN overrides per WLAN, local RADIUS, ACL for standalone mode. Referenced by Site Tag.", "—"),
    ("AP Group (legacy)", "Pre-9800 concept, replaced by tags. Still visible for migration compatibility.", "default-ap-group"),
    ("Fabric Profile", "SD-Access-specific: VNID, SGT, LISP config. Referenced by Site Tag in fabric deployments.", "—"),
], has_default=True)}
</div></div>

<div class="card" id="assignment">
<div class="card-head"><div class="icon">🎯</div><h2>TAG Assignment Methods</h2></div>
<div class="card-body">
<p>Tags can be assigned to APs using three different methods, from most specific to least specific:</p>
<div class="subsec"><h3>Method 1 — Static (per AP MAC)</h3>
<p>Navigate to <strong>Configuration &rsaquo; Wireless &rsaquo; Access Points</strong>, click the AP, and manually set each tag. This is the most explicit method and overrides everything else.</p>
{navp(["Configuration", "Wireless", "Access Points", "&lt;AP Name&gt;", "General Tab", "Tags"])}
</div>
<div class="subsec"><h3>Method 2 — Dynamic via RADIUS VSA</h3>
<p>The RADIUS server can push tag assignments in the Access-Accept message using Cisco AVPair attributes. This allows different users/devices to trigger different AP tag configurations dynamically — useful for multi-tenant or context-aware deployments.</p>
<div class="diagram">
RADIUS Access-Accept includes:
  Cisco-AVPair = <span class="dpr">"policy-tag=Tag-Corp"</span>
  Cisco-AVPair = <span class="dpr">"site-tag=Tag-Site-HQ"</span>
  Cisco-AVPair = <span class="dpr">"rf-tag=Tag-RF-High-Density"</span>
</div>
</div>
<div class="subsec"><h3>Method 3 — Filter Rules (AP Filters)</h3>
<p>Create rules based on AP name, AP model, or location to automatically assign tags when APs join. Navigate to <strong>Configuration &rsaquo; Wireless &rsaquo; Advanced &rsaquo; AP Filter</strong>.</p>
</div>
{nt("info", "Priority: Static assignment > Dynamic RADIUS > Filter rules > Default tags. Static assignment always wins.")}
</div></div>

<div class="card" id="defaults-trap">
<div class="card-head"><div class="icon">⚠️</div><h2>The Default Tags Trap</h2></div>
<div class="card-body">
<p>The 9800 ships with three default tags pre-configured. Any AP that joins without an explicit tag assignment uses these defaults. This is convenient in a lab but <strong>dangerous in production</strong>.</p>
<div class="diagram">
<span class="dn">DANGER SCENARIO:</span>

  Engineer adds WLAN "Corp-WiFi6" to default-policy-tag
  to test on one AP.

  Result: <span class="dv">EVERY AP</span> in the network (200+ APs) that hasn't been
  explicitly tagged now broadcasts "Corp-WiFi6"
  — including APs in the parking lot, reception,
  conference rooms, and all branches.

  <span class="dn">This is not a hypothetical — it has happened in production networks.</span>
</div>
{nt("danger", "<strong>Production Best Practice:</strong> Immediately after deployment, assign custom tags to all APs. Never use default-policy-tag for production SSIDs. Use default tags only as a safety net for untagged/new APs with no SSIDs (empty WLAN list).")}
{nt("success", "Recommended approach: Create a 'quarantine' Policy Tag with no WLANs mapped. Assign this to unmanaged APs so they join but broadcast nothing until explicitly configured.")}
</div></div>

<!-- ═════════════════════ EXAMPLES ═════════════════════ -->

<div class="egcard" id="eg1">
<div class="eghead">
  <div class="egicon" style="background:rgba(0,188,235,.2)">🏢</div>
  <h3>Example 1 — Corporate SSID with Central Switching (Local-Mode AP)</h3>
  <span class="mode mode-loc">Local Mode</span>
</div>
<div class="egbody">
<p><strong>Use case:</strong> HQ building with direct layer-2 connectivity between APs and the WLC (same campus). All client traffic must reach the WLC for security inspection and centralized routing.</p>
<div class="diagram">
<div class="dt">Traffic Flow — Central Switching</div>

  [Client] ──802.11──&gt; [AP]
                         │
                         │ CAPWAP tunnel (UDP 5247)
                         ▼
                       [WLC]
                         │
                         │ VLAN 10 (Corp)
                         ▼
                      [Core Switch] ──&gt; Internet / DC

<span class="dn">  Client data rides inside CAPWAP all the way to the WLC</span>
</div>
<p><strong>Required configuration:</strong></p>
{ftable([
    ("WLAN Profile", "Corp-WiFi6 | Security: WPA3-SAE | Status: Enabled", ""),
    ("Policy Profile", "Policy-Corp | VLAN: 10 | Central Switching: ON | Central DHCP: ON", ""),
    ("Policy Tag", "Tag-Corp | Mapping: Corp-WiFi6 -> Policy-Corp", ""),
    ("Site Tag", "Tag-Site-HQ | AP Join Profile: APJoin-HQ | Flex Profile: NONE | Local Site: ✓", ""),
    ("RF Tag", "Tag-RF-HQ | 5G Profile: RF-5G-Corp | 2.4G Profile: RF-2.4-Corp", ""),
], has_default=False)}
{nt("success", "Best for: HQ, campus, data center floors — anywhere APs have low-latency, high-bandwidth connectivity to the WLC.")}
</div></div>

<div class="egcard" id="eg2">
<div class="eghead">
  <div class="egicon" style="background:rgba(255,115,0,.2)">🏭</div>
  <h3>Example 2 — FlexConnect Local Switching for a Remote Branch</h3>
  <span class="mode mode-flex">FlexConnect</span>
</div>
<div class="egbody">
<p><strong>Use case:</strong> Remote branch office connected to HQ via WAN (MPLS or SD-WAN). Client traffic should NOT traverse the WAN — it must be switched locally at the branch to keep latency low and WAN bandwidth free.</p>
<div class="diagram">
<div class="dt">Traffic Flow — FlexConnect Local Switching</div>

  Branch Site                    HQ / WLC
  ─────────────────              ────────────────
  [Client] ──802.11──&gt; [AP]      [WLC]
                         │  ◄──── CAPWAP Control only ───►
                         │        (no data traffic on WAN)
                         │
                    [Branch Switch]
                         │
                    VLAN 100 (local)
                         │
                    [Branch Router] ──&gt; Internet (local breakout)

<span class="dn">  Only CAPWAP control packets cross the WAN — data stays local</span>
</div>
<p><strong>Required configuration:</strong></p>
{ftable([
    ("WLAN Profile", "Corp-WiFi6 | WPA2-PSK or 802.1X", ""),
    ("Flex Profile", "Flex-Branch | VLAN override: Corp-WiFi6 -> VLAN 100 (branch local VLAN)", ""),
    ("Policy Profile", "Policy-Corp | Central Switching: OFF | Local Switching: ON | Local DHCP: ON", ""),
    ("Site Tag", "Tag-Site-Branch | AP Join Profile: APJoin-Branch | Flex Profile: Flex-Branch | Local Site: ✗", ""),
], has_default=False)}
{nt("success", "WAN failover: if the WAN link fails, connected clients remain on the network. The AP enters standalone mode and continues local switching. New client auth uses cached credentials (up to 100 MACs) or local RADIUS.")}
{nt("warning", "The VLAN number in the Flex Profile VLAN override does NOT need to match the WLC-side VLAN. Branch VLAN 100 is completely independent of the central VLAN 10 at HQ.")}
</div></div>

<div class="egcard" id="eg3">
<div class="eghead">
  <div class="egicon" style="background:rgba(108,192,74,.2)">🔀</div>
  <h3>Example 3 — Dual SSID: Corporate (Central) + Guest (Local) on Same AP</h3>
  <span class="mode mode-loc">Mixed Mode</span>
</div>
<div class="egbody">
<p><strong>Use case:</strong> A single AP must serve two SSIDs simultaneously — one corporate SSID with central switching to VLAN 10 for secure access, and one guest SSID with local switching directly to VLAN 200 at the AP for internet breakout.</p>
<div class="diagram">
<div class="dt">Same AP — Two Traffic Paths</div>

                [AP]
               /    \
   Corp-WiFi6 /      \ Guest-WiFi
             /        \
    CAPWAP tunnel    Local switch
             │              │
           [WLC]      [Access Switch]
             │              │
          VLAN 10        VLAN 200
             │              │
        Corporate         Guest DMZ /
          Network          Internet

<span class="dn">  One AP, one Policy Tag, two WLAN->Policy mappings, two traffic paths</span>
</div>
{ftable([
    ("Policy Tag", "Tag-AP-Mixed", ""),
    ("Mapping 1", "Corp-WiFi6 -> Policy-Corp (VLAN 10, Central Switching, 802.1X)", ""),
    ("Mapping 2", "Guest-WiFi -> Policy-Guest (VLAN 200, Local Switching, Web Auth)", ""),
    ("Site Tag", "Tag-Site-HQ (Local mode — no Flex Profile needed for local switching on Local-mode AP)", ""),
], has_default=False)}
{nt("info", "On a Local-mode AP, local switching in the Policy Profile means the AP natively bridges traffic to the local VLAN without CAPWAP tunneling. This is different from FlexConnect local switching — it works even without a Flex Profile.")}
</div></div>

<div class="egcard" id="eg4">
<div class="eghead">
  <div class="egicon" style="background:rgba(255,115,0,.2)">🔌</div>
  <h3>Example 4 — Branch WAN Failover with Local Auth</h3>
  <span class="mode mode-flex">FlexConnect</span>
</div>
<div class="egbody">
<p><strong>Use case:</strong> A retail branch with strict uptime requirements. When the WAN fails, existing clients stay connected AND new clients must be able to authenticate (not just cached ones). A local RADIUS server at the branch handles authentication during outage.</p>
<div class="diagram">
<div class="dt">Normal Operation (WAN up)</div>

  [Client] -> [AP] -> CAPWAP Control -> [WLC] -> RADIUS 10.1.1.100
                   ↘ Local data switch (no WAN for data)

<div class="dt" style="margin-top:12px">WAN Failover (Standalone mode)</div>

  [Client] -> [AP] -> Local RADIUS 192.168.10.50 (at branch)
                   ↘ Local data switch continues uninterrupted

<span class="dn">  Clients don't notice the WAN failure — zero downtime</span>
</div>
{ftable([
    ("Flex Profile", "Flex-Retail | Local RADIUS: 192.168.10.50 (branch RADIUS) | RADIUS fallback: local", ""),
    ("Site Tag", "Tag-Site-Retail | Flex Profile: Flex-Retail | Local Site: ✗", ""),
    ("Policy Profile", "Policy-Corp | Local Switching: ON | Local DHCP: ON", ""),
], has_default=False)}
{nt("success", "Local RADIUS in the Flex Profile enables authentication of new clients during WAN outage. Without it, only the 100 cached client credentials can authenticate.")}
</div></div>

<div class="egcard" id="eg5">
<div class="eghead">
  <div class="egicon" style="background:rgba(255,115,0,.2)">🔒</div>
  <h3>Example 5 — FlexConnect Central Switching (Secure Corporate over WAN)</h3>
  <span class="mode mode-flex">FlexConnect</span>
</div>
<div class="egbody">
<p><strong>Use case:</strong> A branch where the corporate SSID must route ALL client traffic back through the HQ WLC (for firewall/IDS inspection), while a second guest SSID locally switches to the internet. Both SSIDs run on the same FlexConnect AP.</p>
<div class="diagram">
<div class="dt">FlexConnect — Mixed Central + Local Switching</div>

  Branch [AP] in FlexConnect mode
     │
     ├── Corp-WiFi6 -> CAPWAP DATA tunnel -> [WLC at HQ] -> VLAN 10 (inspected)
     │
     └── Guest-WiFi -> Local switch -> Branch VLAN 200 -> Internet (direct)

<span class="dn">  FlexConnect supports per-WLAN switching mode independently</span>
</div>
{ftable([
    ("Policy Profile Corp", "Policy-Corp-Flex | Central Switching: ON | VLAN: 10 (HQ VLAN, tunneled back)", ""),
    ("Policy Profile Guest", "Policy-Guest-Flex | Local Switching: ON | VLAN: 200 (branch local)", ""),
    ("Flex Profile", "Flex-Branch | VLAN override for Guest-WiFi only: Guest-WiFi -> VLAN 200", ""),
    ("Site Tag", "Tag-Site-Branch | Flex Profile: Flex-Branch | Local Site: ✗", ""),
], has_default=False)}
{nt("warning", "When Corp SSID uses central switching in FlexConnect mode, client traffic DOES traverse the WAN. Ensure adequate WAN bandwidth and QoS prioritization for wireless traffic (DSCP EF for voice, AF41 for video).")}
</div></div>

<div class="egcard" id="eg6">
<div class="eghead">
  <div class="egicon" style="background:rgba(226,35,26,.2)">🚨</div>
  <h3>Example 6 — The Default Tag Trap (What Goes Wrong)</h3>
  <span class="mode" style="background:rgba(226,35,26,.3);color:#e2231a">DANGER</span>
</div>
<div class="egbody">
<p><strong>Scenario:</strong> An engineer adds a new SSID to the default-policy-tag to quickly test it on one AP, not realizing the implications.</p>
<div class="diagram">
<span class="dv">Before (safe):</span>
  default-policy-tag  ->  <span class="dn">empty (no WLANs mapped)</span>
  200 APs use default-policy-tag  ->  no SSIDs broadcast  ✓

<span class="dv">Engineer adds test WLAN:</span>
  default-policy-tag  ->  TestSSID -> Policy-Test

<span class="dv">Result (unintended):</span>
  <span class="dv">ALL 200 APs</span> now broadcast "TestSSID" including:
  • Parking lot APs  • Reception APs
  • Executive floor  • Remote branches
  • Conference rooms • Server room APs

<span class="dn">  Immediate security exposure — unauthorized access point on every AP</span>
</div>
{nt("danger", "Never add production or test WLANs to the default-policy-tag unless you explicitly want ALL untagged APs to broadcast that SSID.")}
{nt("success", "Fix: Create a custom Policy Tag for testing with only the specific test APs assigned to it. Keep default-policy-tag empty (or with a dead-end Policy Profile that has no VLAN).")}
</div></div>

<div class="egcard" id="eg7">
<div class="eghead">
  <div class="egicon" style="background:rgba(0,188,235,.2)">🔄</div>
  <h3>Example 7 — Dynamic TAG Assignment via RADIUS</h3>
  <span class="mode mode-loc">Dynamic</span>
</div>
<div class="egbody">
<p><strong>Use case:</strong> A multi-tenant building where different floors are managed by different tenants. When an AP joins, the RADIUS server assigns tags based on the AP's identity, placing it in the correct tenant's configuration context automatically.</p>
<div class="diagram">
<div class="dt">Dynamic TAG Assignment Flow</div>

  AP boots and sends CAPWAP Join Request to WLC
           │
           ▼
  WLC queries RADIUS for AP identity
  (AP MAC / AP name as username)
           │
           ▼
  RADIUS returns Access-Accept with VSA:
    Cisco-AVPair = <span class="dpr">"policy-tag=Tag-Tenant-A"</span>
    Cisco-AVPair = <span class="dpr">"site-tag=Tag-Site-FloorA"</span>
    Cisco-AVPair = <span class="dpr">"rf-tag=Tag-RF-High-Density"</span>
           │
           ▼
  WLC applies tags -> AP broadcasts Tenant A SSIDs only
</div>
{ftable([
    ("RADIUS Server", "Must support Cisco-AVPair VSA (Vendor ID 9, Attribute 1)", ""),
    ("VSA format", 'policy-tag=&lt;tag-name&gt; | site-tag=&lt;tag-name&gt; | rf-tag=&lt;tag-name&gt;', ""),
    ("Fallback", "If RADIUS does not return tag VSAs, default tags are applied", ""),
], has_default=False)}
{nt("info", "Dynamic TAG assignment is especially powerful in managed service provider (MSP) environments and large campuses where manual AP tagging is impractical.")}
</div></div>

<div class="egcard" id="eg8">
<div class="eghead">
  <div class="egicon" style="background:rgba(108,192,74,.2)">🧱</div>
  <h3>Example 8 — SD-Access / Fabric Mode</h3>
  <span class="mode mode-fab">Fabric</span>
</div>
<div class="egbody">
<p><strong>Use case:</strong> Cisco SD-Access (DNA Center managed) deployment where wireless clients need VXLAN encapsulation, Scalable Group Tags (SGT), and integration with the fabric underlay/overlay.</p>
<div class="diagram">
<div class="dt">Fabric Mode Traffic Flow</div>

  [Client] ──802.11──&gt; [AP]
                         │
                         │ CAPWAP to WLC
                         ▼
                       [WLC] ──── VXLAN VNI encapsulation ────&gt;
                                  Scalable Group Tag (SGT)
                                  LISP registration
                         │
                         ▼
                  [Fabric Border / Edge Node]
                         │
                         ▼
                  [SD-Access Fabric Overlay]
</div>
{ftable([
    ("Fabric Profile", "Configures VNID, SGT, LISP. Referenced by Site Tag.", ""),
    ("Site Tag", "Tag-Site-Fabric | AP Join Profile: APJoin-Fabric | Fabric Profile attached", ""),
    ("Policy Profile", "Policy-Fabric | Fabric: Enabled | SGT: assigned per WLAN", ""),
    ("DNA Center", "Manages tag-to-fabric mapping automatically via WLC API. Manual tag config not required.", ""),
], has_default=False)}
{nt("info", "In SD-Access deployments, DNA Center (Catalyst Center) provisions the WLC automatically. Tags and profiles are pushed via RESTCONF/NETCONF — manual GUI configuration is typically not needed.")}
{nt("warning", "Fabric mode APs must be in a Site Tag that references a Fabric Profile, NOT a Flex Profile. Mixing Fabric and FlexConnect profiles in the same Site Tag is not supported.")}
</div></div>
"""

    out = page("TAG Structure",
               "Deep dive into Policy Tag, Site Tag, and RF Tag architecture with 8 real-world examples",
               sidebar, body)
    path = os.path.join(OUTPUT_DIR, "04_tag_structure.html")
    with open(path, "w", encoding="utf-8") as f:
        f.write(out)
    print(f"  [OK] {path}")


# ============================================================================
# MAIN
# ============================================================================
def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    print(f"\nCisco 9800 WLC 17.9.5 — Training Material Generator")
    print(f"Output directory: {os.path.abspath(OUTPUT_DIR)}\n")
    build_menu_guide()
    build_exercises()
    build_quiz()
    build_tag_structure()
    print(f"\nDone. Open any of the 4 HTML files in your browser:")
    for f in ["01_menu_guide.html", "02_exercises.html", "03_quiz.html", "04_tag_structure.html"]:
        print(f"  -> {OUTPUT_DIR}/{f}")


if __name__ == "__main__":
    main()
