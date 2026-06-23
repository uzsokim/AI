#!/usr/bin/env python3
"""
Cisco ISE 3.0 Patch 3 — Policy Analytics Tool
Network Security Designer — Generates an HTML policy health report.

Usage:
    python ise_policy_analytics.py

Requirements:
    pip install requests
"""

import sys
import getpass
# Force UTF-8 output on Windows consoles (avoids cp1250 UnicodeEncodeError)
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import requests
import json
import re
import urllib3
from datetime import datetime
from collections import defaultdict
import html as html_mod

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ─────────────────────────────────────────────────────────────
# Configuration
# ─────────────────────────────────────────────────────────────
ISE_IP      = "10.81.145.7"
USERNAME    = "admin"
PASSWORD    = getpass.getpass(f"Password for {USERNAME}@{ISE_IP}: ")
OUTPUT_HTML = "ISE_Policy_Analytics.html"
TIMEOUT     = 30

ERS_BASE    = f"https://{ISE_IP}:9060/ers/config"
API_BASE    = f"https://{ISE_IP}/api/v1"
ADMIN_BASE  = f"https://{ISE_IP}/admin"

HEADERS_ERS = {"Content-Type": "application/json", "Accept": "application/json"}
HEADERS_API = {"Content-Type": "application/json", "Accept": "application/json"}

# Shared session (populated by ise_login())
SESSION: requests.Session = None


# ─────────────────────────────────────────────────────────────
# Authentication — Session + CSRF (ISE 3.x admin portal flow)
# ─────────────────────────────────────────────────────────────

def ise_login() -> requests.Session:
    """
    Try three auth strategies in order:
    1. ERS Basic Auth (port 9060) — fastest, requires ERS to be enabled
    2. OpenAPI Basic Auth (port 443) — requires Open API to be enabled
    3. Admin portal session (CSRF cookie flow)
    Returns a session with whatever auth method worked, or a bare session
    if all fail (script continues and produces a diagnostic report).
    """
    s = requests.Session()
    s.verify = False
    s.auth = (USERNAME, PASSWORD)  # Used by ERS and OpenAPI

    # ── Quick probe: ERS Basic Auth ──────────────────────────
    print("  [*] Testing ERS API (port 9060) with Basic Auth...")
    try:
        probe = s.get(f"{ERS_BASE}/networkdevice", headers=HEADERS_ERS,
                      params={"page": 1, "size": 1}, timeout=10)
        if probe.status_code == 200:
            print("  [+] ERS API: authenticated successfully")
            return s
        print(f"  [-] ERS API probe: HTTP {probe.status_code}")
    except Exception as e:
        print(f"  [-] ERS API probe error: {e}")

    # ── Quick probe: OpenAPI Basic Auth ──────────────────────
    print("  [*] Testing OpenAPI (port 443) with Basic Auth...")
    try:
        probe2 = s.get(f"{API_BASE}/policy/network-access/policy-set",
                       headers=HEADERS_API, timeout=10)
        if probe2.status_code == 200:
            print("  [+] OpenAPI: authenticated successfully")
            return s
        print(f"  [-] OpenAPI probe: HTTP {probe2.status_code}")
    except Exception as e:
        print(f"  [-] OpenAPI probe error: {e}")

    # ── Fallback: Admin portal session + CSRF ─────────────────
    print("  [*] Trying admin portal session (CSRF flow)...")
    try:
        r = s.get(f"{ADMIN_BASE}/login.jsp", timeout=TIMEOUT)
        m = re.search(r'name="CSRFTokenNameValue"[^>]+value=([^\s">/]+)', r.text)
        csrf = m.group(1) if m else ""
        if csrf:
            print(f"  [+] CSRF token obtained: {csrf[:28]}...")

        r2 = s.post(f"{ADMIN_BASE}/LoginAction.do",
                    data={"name": USERNAME, "password": PASSWORD,
                          "authType": "internal", "newPassword": "",
                          "destinationURL": "", "CSRFTokenNameValue": csrf},
                    headers={"Content-Type": "application/x-www-form-urlencoded"},
                    allow_redirects=True, timeout=TIMEOUT)

        if "login.jsp" not in r2.url and "logout" not in r2.url:
            print(f"  [+] Admin portal session established")
            # Keep basic auth on session too for ERS fallback
            return s

        print("  [-] Admin portal login redirected to:", r2.url)
    except Exception as e:
        print(f"  [-] Admin portal session error: {e}")

    # ── All methods failed ────────────────────────────────────
    print()
    print("  *** AUTHENTICATION FAILED — ALL METHODS ***")
    print()
    print("  To resolve, complete ALL of the following in ISE GUI")
    print(f"  (https://{ISE_IP}/admin/):")
    print()
    print("  1. Verify credentials: log in with admin / <password> manually")
    print("     to confirm they are correct.")
    print()
    print("  2. Enable ERS API:")
    print("     Administration > System > Settings > API Settings")
    print("     Toggle 'ERS (Read/Write)' to ON  -> Save")
    print()
    print("  3. Enable Open API:")
    print("     Same page: toggle 'Open API' to ON -> Save")
    print()
    print("  4. Ensure the 'admin' account has one of these roles:")
    print("     Super Admin  |  ERS Admin  |  Network Admin")
    print("     Administration > System > Admin Access > Administrators")
    print("     > Admin Users > admin > Add Role > ERS Admin / Super Admin")
    print()
    print("  Then re-run this script.")
    print()
    print("  Continuing to generate a DIAGNOSTIC report from available data...")
    print()

    return s


# ─────────────────────────────────────────────────────────────
# API Helpers
# ─────────────────────────────────────────────────────────────

def ers_list(resource):
    """Paginate through an ERS list endpoint and return all resources."""
    all_items, page, size = [], 1, 100
    while True:
        url = f"{ERS_BASE}/{resource}"
        try:
            r = SESSION.get(url, headers=HEADERS_ERS,
                            params={"page": page, "size": size}, timeout=TIMEOUT)
            r.raise_for_status()
            sr    = r.json().get("SearchResult", {})
            items = sr.get("resources", [])
            all_items.extend(items)
            if len(all_items) >= sr.get("total", 0):
                break
            page += 1
        except requests.exceptions.ConnectionError as e:
            print(f"  [!] Connection error — ERS {resource}: {e}")
            break
        except Exception as e:
            print(f"  [!] ERS list {resource}: {e}")
            break
    return all_items


def ers_detail(resource, rid):
    """Fetch a single ERS resource by ID."""
    url = f"{ERS_BASE}/{resource}/{rid}"
    try:
        r = SESSION.get(url, headers=HEADERS_ERS, timeout=TIMEOUT)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        print(f"  [!] ERS detail {resource}/{rid}: {e}")
        return {}


def openapi(path):
    """Fetch from the ISE REST/OpenAPI (port 443)."""
    url = f"{API_BASE}/{path}"
    try:
        r = SESSION.get(url, headers=HEADERS_API, timeout=TIMEOUT)
        r.raise_for_status()
        return r.json()
    except requests.exceptions.ConnectionError as e:
        print(f"  [!] Connection error — API {path}: {e}")
        return {}
    except Exception as e:
        print(f"  [!] API {path}: {e}")
        return {}


# ─────────────────────────────────────────────────────────────
# Data Collection
# ─────────────────────────────────────────────────────────────

def collect_data():
    global SESSION
    SESSION = ise_login()
    data = {
        "policy_sets"       : [],
        "auth_rules"        : {},   # ps_id → list of rule dicts
        "authz_rules"       : {},   # ps_id → list of rule dicts
        "authz_profiles"    : [],
        "allowed_protocols" : [],
        "network_devices"   : [],
        "ndgs"              : [],
        "identity_groups"   : [],
        "identity_stores"   : [],
        "collection_errors" : [],
    }

    # ── Policy Sets ──────────────────────────────────────────
    print("\n[1/7] Network Access Policy Sets...")
    ps_resp = openapi("policy/network-access/policy-set")
    ps_list = ps_resp.get("response", []) if ps_resp else []
    data["policy_sets"] = ps_list if isinstance(ps_list, list) else []
    print(f"      {len(data['policy_sets'])} policy set(s) found")

    for ps in data["policy_sets"]:
        ps_id   = ps.get("id", "")
        ps_name = ps.get("name", "Unknown")

        print(f"      → '{ps_name}' auth rules...")
        auth_r = openapi(f"policy/network-access/policy-set/{ps_id}/authentication")
        data["auth_rules"][ps_id] = auth_r.get("response", []) if auth_r else []

        print(f"      → '{ps_name}' authz rules...")
        az_r = openapi(f"policy/network-access/policy-set/{ps_id}/authorization")
        data["authz_rules"][ps_id] = az_r.get("response", []) if az_r else []

    # ── Authorization Profiles ───────────────────────────────
    print("\n[2/7] Authorization Profiles...")
    ap_refs = ers_list("authorizationprofile")
    for ref in ap_refs:
        detail = ers_detail("authorizationprofile", ref.get("id", ""))
        if "AuthorizationProfile" in detail:
            data["authz_profiles"].append(detail["AuthorizationProfile"])
    print(f"      {len(data['authz_profiles'])} profile(s) found")

    # ── Allowed Protocols ────────────────────────────────────
    print("\n[3/7] Allowed Protocols...")
    prot_refs = ers_list("allowedprotocols")
    for ref in prot_refs:
        detail = ers_detail("allowedprotocols", ref.get("id", ""))
        if "AllowedProtocols" in detail:
            data["allowed_protocols"].append(detail["AllowedProtocols"])
    print(f"      {len(data['allowed_protocols'])} service(s) found")

    # ── Network Devices ──────────────────────────────────────
    print("\n[4/7] Network Devices...")
    data["network_devices"] = ers_list("networkdevice")
    print(f"      {len(data['network_devices'])} device(s) found")

    # ── Network Device Groups ────────────────────────────────
    print("\n[5/7] Network Device Groups...")
    data["ndgs"] = ers_list("networkdevicegroup")
    print(f"      {len(data['ndgs'])} NDG(s) found")

    # ── Identity Groups ──────────────────────────────────────
    print("\n[6/7] Identity Groups...")
    data["identity_groups"] = ers_list("identitygroup")
    print(f"      {len(data['identity_groups'])} group(s) found")

    # ── Identity Stores ──────────────────────────────────────
    print("\n[7/7] Identity Stores...")
    id_resp = openapi("network-access/identity-stores")
    data["identity_stores"] = id_resp.get("response", []) if id_resp else []
    print(f"      {len(data['identity_stores'])} store(s) found")

    return data


# ─────────────────────────────────────────────────────────────
# Analysis Engine
# ─────────────────────────────────────────────────────────────

def finding(severity, area, title, detail, recommendation):
    return {
        "severity"       : severity,
        "area"           : area,
        "title"          : title,
        "detail"         : detail,
        "recommendation" : recommendation,
    }


def analyze(data):
    results = []
    ps_list = data["policy_sets"]
    profile_names = {p.get("name", "") for p in data["authz_profiles"]}

    # ── Top-level: no policy sets retrieved ─────────────────
    if not ps_list:
        results.append(finding(
            "critical", "Policy Configuration",
            "No Policy Sets Retrieved",
            "Zero network-access policy sets were returned by the API. "
            "This may indicate the ISE OpenAPI is disabled, the ERS/OpenAPI "
            "admin account lacks the required role, or no policies exist.",
            "Enable the ISE REST API: Administration → System → Settings → API Settings. "
            "Assign the 'ERS-Admin' and 'Super Admin' roles to the API account."
        ))
        return results

    # ── No default policy set ────────────────────────────────
    if not any(ps.get("default", False) for ps in ps_list):
        results.append(finding(
            "high", "Policy Sets",
            "No Default (Catch-All) Policy Set",
            "ISE evaluates policy sets top-down and stops at the first match. "
            "Without a default catch-all, unmatched traffic is handled by ISE "
            "built-in defaults — behaviour that may not be audited or controlled.",
            "Create a 'Default' policy set with no conditions and configure it "
            "to reject all traffic. This makes unmatched access explicit and logged."
        ))

    for ps in ps_list:
        ps_id   = ps.get("id", "")
        ps_name = ps.get("name", "Unknown")
        ps_desc = ps.get("description", "")
        auth_rules  = data["auth_rules"].get(ps_id, [])
        authz_rules = data["authz_rules"].get(ps_id, [])

        if not ps_desc:
            results.append(finding(
                "info", f"Policy Set: {ps_name}",
                "Policy Set Has No Description",
                f"'{ps_name}' has no description, making policy intent opaque during audits.",
                "Add a description that documents: purpose, covered device types, "
                "owning team, and creation/last-reviewed date."
            ))

        _check_auth_rules(ps_name, auth_rules, results)
        _check_authz_rules(ps_name, authz_rules, profile_names, results)

    _check_authz_profiles(data["authz_profiles"], results)
    _check_protocols(data["allowed_protocols"], results)
    _check_devices(data["network_devices"], results)

    return results


# ── Authentication Rule Checks ───────────────────────────────

def _check_auth_rules(ps_name, rules, results):
    area = f"Policy Set: {ps_name} → Authentication"

    if not rules:
        results.append(finding(
            "warning", area,
            "No Authentication Rules Defined",
            f"'{ps_name}' has no authentication rules. ISE will fall back to "
            "the global authentication policy which may not match design intent.",
            "Define explicit authentication rules. At minimum: "
            "802.1X → AD/CA, MAB → Internal Endpoints, Default → Reject."
        ))
        return

    seen_id_sources = []

    for rule in rules:
        rule_obj   = rule.get("rule", {})
        rule_name  = rule_obj.get("name", "Unknown")
        rule_area  = f"{area} → Rule: {rule_name}"
        conditions = rule_obj.get("condition", {}) or {}
        id_source  = rule.get("identitySourceName", "")
        if_fail    = rule.get("ifAuthFail", "").upper()
        if_not_fnd = rule.get("ifUserNotFound", "").upper()
        if_proc    = rule.get("ifProcessFail", "").upper()

        # Catch-all rule risk: no condition + continue on failure
        if not conditions:
            if if_fail == "CONTINUE":
                results.append(finding(
                    "high", rule_area,
                    "Catch-All Auth Rule — ifAuthFail=CONTINUE",
                    "A rule with no conditions and ifAuthFail=CONTINUE lets failed "
                    "authentications silently reach the authorization phase.",
                    "Set ifAuthFail to REJECT. Only use CONTINUE on specific rules "
                    "where chained authentication (e.g., 802.1X then MAB fallback) "
                    "is explicitly intended."
                ))

            if if_not_fnd == "CONTINUE":
                results.append(finding(
                    "high", rule_area,
                    "Catch-All Auth Rule — ifUserNotFound=CONTINUE",
                    "Unknown users (not in any identity store) continue to authorization. "
                    "A spoofed MAC or credential can traverse the entire policy.",
                    "Set ifUserNotFound to REJECT unless this rule is a MAB rule "
                    "where 'not found' is the expected outcome for profiling."
                ))

        # Broad MAB with no scoping
        if id_source.lower().startswith("internal endpoint") and not conditions:
            results.append(finding(
                "warning", rule_area,
                "Unscoped MAB Rule (Internal Endpoints, No Conditions)",
                "MAB via Internal Endpoints with no conditions matches every request "
                "that reaches this policy set. Any MAC address is authenticated.",
                "Scope MAB rules: add a condition on NDG (e.g., 'Access Layer Switches') "
                "or use a Profiler condition (e.g., Device-Type=IP-Phone) to restrict "
                "which endpoints qualify for MAB."
            ))

        # Track duplicate identity sources
        if id_source:
            seen_id_sources.append(id_source)

    # Duplicate identity sources across rules
    dupes = {s for s in seen_id_sources if seen_id_sources.count(s) > 1}
    if dupes:
        results.append(finding(
            "info", area,
            f"Duplicate Identity Sources: {', '.join(dupes)}",
            "Multiple authentication rules reference the same identity store(s). "
            "The lower-priority rule will never be evaluated unless conditions differ.",
            "Consolidate rules that share the same identity source into a single rule "
            "with a compound condition, or verify they have distinct conditions."
        ))


# ── Authorization Rule Checks ────────────────────────────────

def _check_authz_rules(ps_name, rules, profile_names, results):
    area = f"Policy Set: {ps_name} → Authorization"

    if not rules:
        results.append(finding(
            "critical", area,
            "No Authorization Rules Defined",
            f"'{ps_name}' has no authorization rules. All authenticated sessions "
            "will receive ISE's built-in DenyAccess or an unpredictable result.",
            "Add authorization rules. Always end with a DenyAccess catch-all."
        ))
        return

    # Check last rule is deny
    last   = rules[-1]
    l_rule = last.get("rule", {})
    l_profiles = last.get("profile", [])
    l_name = l_rule.get("name", "Unknown")
    last_is_deny = any("deny" in p.lower() for p in l_profiles)

    if not last_is_deny:
        results.append(finding(
            "high", area,
            f"Last Authorization Rule '{l_name}' Is Not DenyAccess",
            "The final rule acts as a catch-all for unmatched sessions. If it is not "
            "DenyAccess, unexpected traffic receives unintended network access.",
            "Add a DenyAccess rule as the last entry in every authorization policy. "
            "This enforces least-privilege: 'if no rule explicitly grants access, deny.'"
        ))

    seen_conditions = []

    for rule in rules:
        rule_obj   = rule.get("rule", {})
        rule_name  = rule_obj.get("name", "Unknown")
        rule_area  = f"{area} → Rule: {rule_name}"
        conditions = rule_obj.get("condition", {}) or {}
        profiles   = rule.get("profile", [])
        state      = rule_obj.get("state", "enabled")
        desc       = rule_obj.get("description", "")
        profile_str = ", ".join(profiles) if profiles else "None"

        # Disabled rule still in policy
        if state == "disabled":
            results.append(finding(
                "info", rule_area,
                "Disabled Rule Still Present in Policy",
                f"Rule '{rule_name}' is disabled. Stale disabled rules clutter policy, "
                "can be accidentally re-enabled, and complicate audits.",
                "Remove disabled rules from production. Document removed rules in "
                "your change management system or IPAM/ITSM tool instead."
            ))

        # PermitAccess with no conditions — most dangerous pattern
        if any("permit" in p.lower() for p in profiles) and not conditions:
            results.append(finding(
                "critical", rule_area,
                "PermitAccess Rule With No Conditions — Unrestricted Bypass",
                f"Rule '{rule_name}' grants '{profile_str}' with zero conditions. "
                "Every session that reaches this policy set gets full access.",
                "This rule must be deleted or given specific conditions immediately. "
                "Every permit rule needs at least: identity group + endpoint compliance "
                "+ NDG/location. Follow the pattern: Who + From Where + How = What Access."
            ))

        # Missing description
        if not desc and state != "disabled":
            results.append(finding(
                "info", rule_area,
                "Authorization Rule Has No Description",
                f"'{rule_name}' has no description.",
                "Document purpose, owner, ticket reference, and review date. "
                "Descriptions are critical for SOC triage and compliance audits."
            ))

        # Duplicate conditions (shadowed rule)
        cond_key = json.dumps(conditions, sort_keys=True)
        if cond_key in seen_conditions and cond_key != "{}":
            results.append(finding(
                "warning", rule_area,
                "Shadowed Rule — Identical Conditions to Earlier Rule",
                f"'{rule_name}' has the same conditions as a rule above it. "
                "ISE stops at the first match, so this rule is never evaluated.",
                "Merge this rule with the earlier one, or differentiate their "
                "conditions. Shadowed rules are a common source of policy drift."
            ))
        seen_conditions.append(cond_key)

        # Referenced profile doesn't exist
        for p in profiles:
            builtin = {"PermitAccess", "DenyAccess", "Quarantine",
                       "Blackhole_Wireless_Access", "Non_Cisco_IBNS_Permit"}
            if p not in builtin and p not in profile_names and p:
                results.append(finding(
                    "warning", rule_area,
                    f"Referenced Authorization Profile '{p}' Not Found",
                    f"Rule '{rule_name}' references profile '{p}' which was not "
                    "retrieved from ISE. The profile may have been deleted.",
                    f"Verify '{p}' exists under Policy → Policy Elements → "
                    "Authorization → Authorization Profiles. Broken references "
                    "cause authorization failures."
                ))


# ── Authorization Profile Checks ─────────────────────────────

def _check_authz_profiles(profiles, results):
    system_profiles = {"DenyAccess", "PermitAccess", "Blackhole_Wireless_Access",
                       "Non_Cisco_IBNS_Permit"}

    for p in profiles:
        name    = p.get("name", "Unknown")
        if name in system_profiles:
            continue

        area         = f"Authorization Profile: {name}"
        access_type  = p.get("accessType", "")
        dacl         = p.get("daclName", "")
        vlan_obj     = p.get("vlan", {}) or {}
        vlan         = vlan_obj.get("nameID", "")
        sess_timeout = p.get("sessionTimeout", 0) or 0
        reauth       = p.get("reauthTimeout", 0) or 0
        web_redirect = p.get("webRedirection", {}) or {}

        # No DACL on access profile
        if access_type in ("ACCESS_ACCEPT", "") and not dacl:
            results.append(finding(
                "warning", area,
                "Access Profile Has No DACL",
                f"'{name}' grants access without a Downloadable ACL. Enforcement "
                "relies solely on VLAN segmentation, which can be bypassed "
                "by a misconfigured trunk or VLAN hop.",
                "Apply a DACL for every access profile. For full access use "
                "a named permit-all DACL (e.g., 'PERMIT_ALL_TRAFFIC') — this "
                "makes intent explicit and lets you tighten it later without "
                "touching the authorization rule."
            ))

        # VLAN without DACL — relies on L2 only
        if vlan and not dacl:
            results.append(finding(
                "info", area,
                "VLAN Assignment Without DACL — L2-Only Enforcement",
                f"'{name}' assigns VLAN '{vlan}' with no DACL. If VLAN segmentation "
                "fails or is misconfigured, there is no L3/L4 backstop.",
                "Pair every VLAN assignment with a matching DACL. "
                "Defense-in-depth requires both L2 (VLAN) and L3 (ACL) controls."
            ))

        # No session timeout
        if not sess_timeout and not reauth:
            results.append(finding(
                "info", area,
                "No Session or Re-Auth Timeout",
                f"'{name}' has no session timeout or re-authentication timer. "
                "Sessions persist indefinitely regardless of posture or group changes.",
                "Set sessionTimeout (e.g., 28800 s for 8 h corporate; 3600 s for guests). "
                "Short timeouts force re-evaluation and are required by many compliance "
                "frameworks (PCI-DSS, HIPAA). Use CoA for real-time revocation."
            ))


# ── Allowed Protocol Checks ──────────────────────────────────

def _check_protocols(protocols, results):
    for prot in protocols:
        name = prot.get("name", "Unknown")
        area = f"Allowed Protocols: {name}"

        insecure_map = {
            "allowPapAscend" : "PAP/ASCII",
            "allowChap"      : "CHAP",
            "allowMsChap"    : "MS-CHAPv1",
            "allowLeap"      : "LEAP",
            "allowEapMd5"    : "EAP-MD5",
        }
        enabled_insecure = [label for key, label in insecure_map.items() if prot.get(key, False)]

        if enabled_insecure:
            results.append(finding(
                "high", area,
                f"Legacy/Insecure Protocols Enabled: {', '.join(enabled_insecure)}",
                f"'{name}' permits: {', '.join(enabled_insecure)}. These protocols "
                "transmit credentials in a form vulnerable to offline dictionary attacks, "
                "MITM, and replay. LEAP is deprecated by Cisco. "
                "PAP/ASCII sends passwords in cleartext to the RADIUS server.",
                f"Disable {', '.join(enabled_insecure)}. Use EAP-TLS for certificate-based "
                "mutual authentication, PEAP-MSCHAPv2 for password-based, or EAP-FAST "
                "for environments that cannot deploy certificates. "
                "Document any legacy exception with a risk acceptance record."
            ))

        eap_tls = prot.get("allowEapTls", False)
        peap    = prot.get("allowPeap", False)
        eap_fast = prot.get("allowEapFast", False)

        if not eap_tls and not peap and not eap_fast:
            results.append(finding(
                "warning", area,
                "No Strong EAP Method Enabled",
                f"'{name}' has no EAP-TLS, PEAP, or EAP-FAST configured. "
                "Without a strong EAP method, 802.1X deployments cannot proceed.",
                "Enable EAP-TLS as the preferred method (certificate-based, "
                "mutually authenticated). Enable PEAP-MSCHAPv2 as a fallback "
                "for devices that cannot use certificates."
            ))

        # EAP-TLS without requiring client cert check
        if eap_tls:
            require_crl = prot.get("requireMessageAuth", False)
            if not require_crl:
                results.append(finding(
                    "info", area,
                    "EAP-TLS Enabled — Verify CRL/OCSP Checking is Active",
                    f"'{name}' uses EAP-TLS. If certificate revocation checking "
                    "(CRL or OCSP) is not enabled in the CA Trust configuration, "
                    "revoked client certificates will still be accepted.",
                    "Enable CRL or OCSP checking in ISE: Administration → System → "
                    "Certificates → Certificate Authority → OCSP Client Profile. "
                    "This is required for PCI-DSS and many enterprise security policies."
                ))


# ── Network Device Checks ────────────────────────────────────

def _check_devices(devices, results):
    if not devices:
        results.append(finding(
            "warning", "Network Devices",
            "No Network Access Devices (NADs) Configured",
            "ISE has no registered network devices. Without NADs, no RADIUS "
            "authentication requests will be accepted.",
            "Add network devices under Administration → Network Resources → "
            "Network Devices. Group them into Network Device Groups (NDGs) "
            "by location, type, or function for scalable policy."
        ))
        return

    total = len(devices)

    # Check for the default 'All Device Types' group usage — flag if > 50 devices ungrouped
    if total > 50:
        results.append(finding(
            "info", "Network Devices",
            f"Large NAD Inventory ({total} devices) — Verify NDG Structure",
            f"{total} network devices registered. Large flat inventories make it "
            "hard to scope authorization rules to specific device types or locations.",
            "Organize NADs into a 3-tier NDG hierarchy: "
            "Location (Site) → Function (Wired/Wireless/VPN) → Device Type. "
            "This lets authorization rules reference 'Wired Access Switches, Building A' "
            "instead of matching all devices."
        ))


# ─────────────────────────────────────────────────────────────
# HTML Report Generator
# ─────────────────────────────────────────────────────────────

SEVERITY_ORDER = {"critical": 0, "high": 1, "warning": 2, "info": 3}

SEVERITY_STYLE = {
    "critical": ("#dc2626", "#fca5a5", "CRITICAL"),
    "high"    : ("#ea580c", "#fdba74", "HIGH"),
    "warning" : ("#d97706", "#fcd34d", "WARNING"),
    "info"    : ("#2563eb", "#93c5fd", "INFO"),
}


def badge(sev):
    color, _, label = SEVERITY_STYLE.get(sev, ("#6b7280", "#d1d5db", sev.upper()))
    return (f'<span style="display:inline-block;padding:2px 10px;border-radius:999px;'
            f'font-size:.68rem;font-weight:700;color:#fff;background:{color};'
            f'text-transform:uppercase;letter-spacing:.06em;margin-right:6px">{label}</span>')


def counts(findings):
    c = {"critical": 0, "high": 0, "warning": 0, "info": 0}
    for f in findings:
        c[f.get("severity", "info")] += 1
    return c


def score_calc(c):
    s = max(0, 100 - c["critical"] * 20 - c["high"] * 10
               - c["warning"] * 4 - c["info"] * 1)
    color = "#16a34a" if s >= 80 else "#d97706" if s >= 60 else "#dc2626"
    label = ("Healthy" if s >= 80
             else "Needs Attention" if s >= 60
             else "Critical — Immediate Action Required")
    return s, color, label


def _e(value, fallback="—"):
    """html-escape value, treating None/empty as fallback."""
    return html_mod.escape(str(value) if value is not None else fallback)


def generate_html(data, findings):
    ts      = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    c       = counts(findings)
    score, score_color, score_label = score_calc(c)
    total   = len(findings)
    sorted_f = sorted(findings, key=lambda x: SEVERITY_ORDER.get(x.get("severity"), 99))

    # ── Finding cards ─────────────────────────────────────────
    cards_html = ""
    for i, f in enumerate(sorted_f, 1):
        sev  = f.get("severity", "info")
        _, accent, _ = SEVERITY_STYLE.get(sev, ("#6b7280", "#d1d5db", "INFO"))
        area = _e(f.get("area"), "")
        titl = _e(f.get("title"), "")
        det  = _e(f.get("detail"), "")
        rec  = _e(f.get("recommendation"), "")
        cards_html += f"""
<div class="fcard {sev}" data-sev="{sev}">
  <div class="fhead">
    <span class="fnum">#{i}</span>{badge(sev)}
    <span class="ftitle">{titl}</span>
  </div>
  <div class="fbody">
    <p><strong>Area:</strong> {area}</p>
    <p><strong>Detail:</strong> {det}</p>
    <p class="rec"><strong>Recommendation:</strong> {rec}</p>
  </div>
</div>"""

    # ── Policy sets table ─────────────────────────────────────
    ps_rows = ""
    for ps in data["policy_sets"]:
        ps_id   = ps.get("id", "")
        ps_name = _e(ps.get("name"))
        ps_desc = _e(ps.get("description"))
        default = '<span style="color:#4ade80">Yes</span>' if ps.get("default") else "No"
        state   = ps.get("state") or "enabled"
        state_s = (f'<span style="color:#4ade80">{state}</span>'
                   if state == "enabled"
                   else f'<span style="color:#f87171">{state}</span>')
        a_cnt = len(data["auth_rules"].get(ps_id, []))
        z_cnt = len(data["authz_rules"].get(ps_id, []))
        ps_rows += (f"<tr><td>{ps_name}</td><td>{ps_desc}</td>"
                    f"<td>{default}</td><td>{state_s}</td>"
                    f"<td>{a_cnt}</td><td>{z_cnt}</td></tr>")
    if not ps_rows:
        ps_rows = '<tr><td colspan="6" class="muted">No policy sets retrieved</td></tr>'

    # ── Auth profiles table ───────────────────────────────────
    ap_rows = ""
    for p in data["authz_profiles"]:
        name   = _e(p.get("name"))
        atype  = _e(p.get("accessType"))
        dacl   = _e(p.get("daclName"))
        vlan_o = p.get("vlan") or {}
        vlan   = _e(vlan_o.get("nameID"))
        sto    = p.get("sessionTimeout") or "—"
        ap_rows += (f"<tr><td>{name}</td><td>{atype}</td>"
                    f"<td>{dacl}</td><td>{vlan}</td><td>{sto}</td></tr>")
    if not ap_rows:
        ap_rows = '<tr><td colspan="5" class="muted">No profiles retrieved</td></tr>'

    # ── Allowed protocols table ───────────────────────────────
    proto_rows = ""
    for prot in data["allowed_protocols"]:
        pname    = _e(prot.get("name"))
        etls     = "✔" if prot.get("allowEapTls")   else "✘"
        peap_    = "✔" if prot.get("allowPeap")      else "✘"
        efast    = "✔" if prot.get("allowEapFast")   else "✘"
        mschapv2 = "✔" if prot.get("allowMsChapV2")  else "✘"
        pap      = "✔" if prot.get("allowPapAscend") else "✘"
        leap_    = "✔" if prot.get("allowLeap")      else "✘"
        proto_rows += (f"<tr><td>{pname}</td>"
                       f"<td style='color:{'#4ade80' if etls=='✔' else '#f87171'}'>{etls}</td>"
                       f"<td style='color:{'#4ade80' if peap_=='✔' else '#f87171'}'>{peap_}</td>"
                       f"<td style='color:{'#4ade80' if efast=='✔' else '#f87171'}'>{efast}</td>"
                       f"<td style='color:{'#4ade80' if mschapv2=='✔' else '#f87171'}'>{mschapv2}</td>"
                       f"<td style='color:{'#f87171' if pap=='✔' else '#4ade80'}'>{pap}</td>"
                       f"<td style='color:{'#f87171' if leap_=='✔' else '#4ade80'}'>{leap_}</td></tr>")
    if not proto_rows:
        proto_rows = '<tr><td colspan="7" class="muted">No protocol sets retrieved</td></tr>'

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>ISE 3.0 Policy Analytics — {ISE_IP}</title>
<style>
:root{{
  --bg:#0f172a;--card:#1e293b;--border:#334155;
  --text:#e2e8f0;--muted:#94a3b8;--accent:#38bdf8;
}}
*{{box-sizing:border-box;margin:0;padding:0}}
body{{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;
     background:var(--bg);color:var(--text);padding:28px;line-height:1.5}}
h1{{font-size:1.75rem;font-weight:800;color:#f1f5f9}}
h2{{font-size:1.1rem;font-weight:700;color:#cbd5e1;
   margin:36px 0 14px;padding-bottom:6px;border-bottom:1px solid var(--border)}}
h3{{font-size:.95rem;font-weight:600;color:#94a3b8;margin-bottom:10px}}
.header{{display:flex;align-items:center;justify-content:space-between;
        padding:24px 28px;background:var(--card);border:1px solid var(--border);
        border-radius:14px;margin-bottom:26px}}
.header-meta{{font-size:.78rem;color:var(--muted);margin-top:4px}}
.logo{{font-size:2.6rem;line-height:1}}
/* Score */
.score-row{{display:flex;align-items:center;gap:24px;
           background:var(--card);border:1px solid var(--border);
           border-radius:14px;padding:22px 28px;margin-bottom:26px}}
.score-num{{font-size:4rem;font-weight:900;line-height:1}}
.score-meta p{{font-size:.82rem;color:var(--muted);margin-top:3px}}
/* Stats */
.stats{{display:grid;grid-template-columns:repeat(auto-fit,minmax(130px,1fr));
       gap:14px;margin-bottom:26px}}
.stat{{background:var(--card);border:1px solid var(--border);
      border-radius:12px;padding:16px;text-align:center}}
.stat-n{{font-size:2.2rem;font-weight:800;line-height:1}}
.stat-l{{font-size:.72rem;color:var(--muted);margin-top:4px;text-transform:uppercase;letter-spacing:.05em}}
/* Findings */
.filter-bar{{display:flex;gap:8px;margin-bottom:14px;flex-wrap:wrap}}
.fb{{padding:5px 16px;border:1px solid var(--border);border-radius:999px;
    background:var(--card);color:var(--muted);cursor:pointer;
    font-size:.78rem;transition:all .15s}}
.fb:hover,.fb.active{{background:#334155;color:#f1f5f9;border-color:#475569}}
.fb.fc.active{{border-color:#dc2626;color:#f87171}}
.fb.fh.active{{border-color:#ea580c;color:#fb923c}}
.fb.fw.active{{border-color:#d97706;color:#fbbf24}}
.fb.fi.active{{border-color:#2563eb;color:#60a5fa}}
.fcard{{background:var(--card);border-left:4px solid var(--border);
       border-radius:10px;padding:16px 18px;margin-bottom:10px;
       transition:transform .1s}}
.fcard:hover{{transform:translateX(2px)}}
.fcard.critical{{border-left-color:#dc2626}}
.fcard.high{{border-left-color:#ea580c}}
.fcard.warning{{border-left-color:#d97706}}
.fcard.info{{border-left-color:#2563eb}}
.fhead{{display:flex;align-items:center;margin-bottom:10px;flex-wrap:wrap;gap:6px}}
.fnum{{font-size:.72rem;color:var(--muted);margin-right:4px}}
.ftitle{{font-weight:700;font-size:.92rem;color:#f1f5f9}}
.fbody p{{font-size:.82rem;color:var(--muted);margin-bottom:5px}}
.fbody strong{{color:#e2e8f0}}
.rec{{color:#86efac!important}}
/* Tables */
.tw{{background:var(--card);border:1px solid var(--border);
    border-radius:12px;overflow:hidden;margin-bottom:26px}}
table{{width:100%;border-collapse:collapse;font-size:.82rem}}
th,td{{padding:10px 14px;text-align:left;border-bottom:1px solid var(--border)}}
th{{background:#162032;color:var(--muted);font-weight:700;font-size:.72rem;
   text-transform:uppercase;letter-spacing:.06em}}
tr:last-child td{{border-bottom:none}}
tr:hover td{{background:rgba(255,255,255,.025)}}
.muted{{color:var(--muted)!important;font-style:italic}}
/* Best Practice Section */
.bp{{background:var(--card);border:1px solid var(--border);
    border-radius:12px;padding:20px 24px;margin-bottom:26px}}
.bp p{{font-size:.84rem;color:var(--muted);margin-bottom:14px}}
footer{{text-align:center;color:var(--muted);font-size:.72rem;
       margin-top:44px;padding-top:18px;border-top:1px solid var(--border)}}
</style>
</head>
<body>

<!-- Header -->
<div class="header">
  <div>
    <h1>ISE 3.0 Policy Analytics</h1>
    <div class="header-meta">
      Cisco Identity Services Engine 3.0 Patch 3 &nbsp;|&nbsp;
      {ISE_IP} &nbsp;|&nbsp; Generated: {ts} &nbsp;|&nbsp;
      Role: Network Security Designer
    </div>
  </div>
  <div class="logo">&#128737;</div>
</div>
{"" if not data.get("collection_errors") else
 '<div style="background:#78350f;border:1px solid #92400e;border-radius:10px;'
 'padding:14px 20px;margin-bottom:20px;font-size:.84rem;color:#fef3c7">'
 '<strong>DEMO / EXAMPLE REPORT</strong> &mdash; The ISE API was not reachable '
 'when this report was generated. The data shown is a synthetic example that '
 'illustrates common policy findings and recommendations. Once the API is '
 'enabled (see instructions above), re-run the script for a live analysis.'
 '</div>'}

<!-- Health Score -->
<div class="score-row">
  <div class="score-num" style="color:{score_color}">{score}</div>
  <div class="score-meta">
    <h3 style="font-size:1.15rem;color:#f1f5f9">Policy Health Score <span style="color:var(--muted);font-size:.85rem">/ 100</span></h3>
    <p style="color:{score_color};font-weight:600">{score_label}</p>
    <p>{c["critical"]} Critical &nbsp;·&nbsp; {c["high"]} High &nbsp;·&nbsp;
       {c["warning"]} Warning &nbsp;·&nbsp; {c["info"]} Info</p>
    <p style="margin-top:6px;font-size:.75rem">
      Score = 100 − (critical×20) − (high×10) − (warning×4) − (info×1)
    </p>
  </div>
</div>

<!-- Stats -->
<div class="stats">
  <div class="stat"><div class="stat-n" style="color:#dc2626">{c["critical"]}</div><div class="stat-l">Critical</div></div>
  <div class="stat"><div class="stat-n" style="color:#ea580c">{c["high"]}</div><div class="stat-l">High</div></div>
  <div class="stat"><div class="stat-n" style="color:#d97706">{c["warning"]}</div><div class="stat-l">Warning</div></div>
  <div class="stat"><div class="stat-n" style="color:#2563eb">{c["info"]}</div><div class="stat-l">Info</div></div>
  <div class="stat"><div class="stat-n" style="color:#38bdf8">{len(data["policy_sets"])}</div><div class="stat-l">Policy Sets</div></div>
  <div class="stat"><div class="stat-n" style="color:#94a3b8">{len(data["authz_profiles"])}</div><div class="stat-l">Authz Profiles</div></div>
  <div class="stat"><div class="stat-n" style="color:#94a3b8">{len(data["network_devices"])}</div><div class="stat-l">NADs</div></div>
  <div class="stat"><div class="stat-n" style="color:#94a3b8">{len(data["allowed_protocols"])}</div><div class="stat-l">Protocol Sets</div></div>
</div>

<!-- Policy Sets Table -->
<h2>Policy Sets</h2>
<div class="tw">
  <table>
    <thead><tr>
      <th>Policy Set</th><th>Description</th><th>Default</th>
      <th>State</th><th>Auth Rules</th><th>Authz Rules</th>
    </tr></thead>
    <tbody>{ps_rows}</tbody>
  </table>
</div>

<!-- Authorization Profiles -->
<h2>Authorization Profiles</h2>
<div class="tw">
  <table>
    <thead><tr>
      <th>Profile</th><th>Access Type</th><th>DACL</th><th>VLAN</th><th>Session Timeout (s)</th>
    </tr></thead>
    <tbody>{ap_rows}</tbody>
  </table>
</div>

<!-- Allowed Protocols -->
<h2>Allowed Protocol Sets</h2>
<div class="tw">
  <table>
    <thead><tr>
      <th>Name</th><th>EAP-TLS</th><th>PEAP</th><th>EAP-FAST</th>
      <th>MSCHAPv2</th><th>PAP ⚠</th><th>LEAP ⚠</th>
    </tr></thead>
    <tbody>{proto_rows}</tbody>
  </table>
</div>

<!-- Findings -->
<h2>Findings ({total} total)</h2>
<div class="filter-bar">
  <button class="fb fa active" onclick="filter('all')">All ({total})</button>
  <button class="fb fc" onclick="filter('critical')">Critical ({c["critical"]})</button>
  <button class="fb fh" onclick="filter('high')">High ({c["high"]})</button>
  <button class="fb fw" onclick="filter('warning')">Warning ({c["warning"]})</button>
  <button class="fb fi" onclick="filter('info')">Info ({c["info"]})</button>
</div>
<div id="fc">
{"".join(cards_html) if cards_html else '<p class="muted">No findings — policy is clean.</p>'}
</div>

<!-- Recommended Structure -->
<h2>Recommended Policy Architecture</h2>
<div class="bp">
  <p>The following represents the recommended policy structure for a secure enterprise
  ISE 3.0 deployment aligned with Cisco's SAFE and TrustSec design guides.</p>

  <h3>Policy Set Order (Top → Bottom)</h3>
  <div class="tw" style="margin-bottom:16px">
  <table>
    <thead><tr><th>#</th><th>Policy Set Name</th><th>Match Condition</th><th>Purpose</th></tr></thead>
    <tbody>
      <tr><td>1</td><td>Wired 802.1X Corporate</td><td>Wired NDG + Protocol=dot1x</td><td>Certificate-based auth for managed Windows/macOS endpoints</td></tr>
      <tr><td>2</td><td>Wireless 802.1X Corporate</td><td>SSID=Corp + Protocol=dot1x</td><td>802.1X on corporate SSID — EAP-TLS preferred</td></tr>
      <tr><td>3</td><td>Wired MAB — Approved IoT</td><td>Wired NDG + Protocol=MAB</td><td>MAC-based auth for IP phones, printers, cameras (whitelist only)</td></tr>
      <tr><td>4</td><td>Wireless Guest</td><td>SSID=Guest</td><td>CWA or sponsor portal for guests — no corporate access</td></tr>
      <tr><td>5</td><td>VPN Remote Access</td><td>NAS-IP=VPN Headend</td><td>RADIUS auth for remote access VPN with posture assessment</td></tr>
      <tr><td>6</td><td>Default — Catch-All</td><td><em>No condition (default)</em></td><td>Explicit DenyAccess for all unmatched traffic + logging</td></tr>
    </tbody>
  </table>
  </div>

  <h3>Authorization Policy Rule Order (per set)</h3>
  <div class="tw">
  <table>
    <thead><tr><th>#</th><th>Rule Name</th><th>Conditions</th><th>Profile</th></tr></thead>
    <tbody>
      <tr><td>1</td><td>Compliant Corp Device</td><td>AD-Group=Corp_Users AND Posture=Compliant AND Certificate=Corp-CA</td><td>Corp_Full_Access (VLAN 10 + PERMIT_ALL DACL + 28800s timeout)</td></tr>
      <tr><td>2</td><td>Non-Compliant Remediation</td><td>AD-Group=Corp_Users AND Posture=NonCompliant</td><td>Remediation (VLAN 99 + ACL-REMEDIATION + redirect to posture agent)</td></tr>
      <tr><td>3</td><td>Unknown Posture — Redirect</td><td>AD-Group=Corp_Users AND Posture=Unknown</td><td>Limited (VLAN 99 + redirect URL + ACL-POSTURE-REDIRECT)</td></tr>
      <tr><td>4</td><td>Cisco IP Phone</td><td>Profiled=Cisco-IP-Phone AND NDG=AccessSwitches</td><td>VoiceAccess (Voice VLAN 20 + ACL-VOICE)</td></tr>
      <tr><td>5</td><td>Approved Printer</td><td>EndpointGroup=Approved-Printers AND Profiled=Printer</td><td>PrinterAccess (VLAN 30 + ACL-PRINTER)</td></tr>
      <tr><td>6</td><td>Default Deny</td><td><em>Any</em></td><td><strong>DenyAccess</strong></td></tr>
    </tbody>
  </table>
  </div>
</div>

<!-- Key Recommendations Summary -->
<h2>Top Remediation Priorities</h2>
<div class="bp">
  <p>Address findings in this order to achieve the greatest security improvement:</p>
  <ol style="font-size:.85rem;color:var(--muted);padding-left:20px;line-height:2">
    <li><strong style="color:#dc2626">Critical:</strong> Remove or restrict any PermitAccess rules with no conditions — these create full-bypass vulnerabilities.</li>
    <li><strong style="color:#ea580c">High:</strong> Ensure every authorization policy ends with a DenyAccess catch-all rule.</li>
    <li><strong style="color:#ea580c">High:</strong> Set ifAuthFail and ifUserNotFound to REJECT on catch-all authentication rules.</li>
    <li><strong style="color:#ea580c">High:</strong> Disable legacy protocols (PAP, LEAP, EAP-MD5) and replace with EAP-TLS / PEAP-MSCHAPv2.</li>
    <li><strong style="color:#d97706">Warning:</strong> Apply DACLs to all access-granting authorization profiles for L3/L4 enforcement.</li>
    <li><strong style="color:#d97706">Warning:</strong> Add session timeouts to all authorization profiles to force periodic re-evaluation.</li>
    <li><strong style="color:#2563eb">Info:</strong> Add descriptions to all policy sets and rules for audit traceability.</li>
    <li><strong style="color:#2563eb">Info:</strong> Enable CRL/OCSP validation for EAP-TLS to handle certificate revocation.</li>
  </ol>
</div>

<footer>
  Cisco ISE 3.0 Policy Analytics &nbsp;|&nbsp; Network Security Designer Report
  &nbsp;|&nbsp; {ts} &nbsp;|&nbsp; {ISE_IP}
</footer>

<script>
function filter(sev){{
  document.querySelectorAll('.fb').forEach(b=>b.classList.remove('active'));
  const sel = sev==='all' ? '.fa'
    : sev==='critical' ? '.fc'
    : sev==='high'     ? '.fh'
    : sev==='warning'  ? '.fw' : '.fi';
  document.querySelector(sel).classList.add('active');
  document.querySelectorAll('.fcard').forEach(c=>{{
    c.style.display = (sev==='all'||c.dataset.sev===sev) ? 'block' : 'none';
  }});
}}
</script>
</body>
</html>"""


# ─────────────────────────────────────────────────────────────
# Demo / Example Data (used when live API is unreachable)
# Mirrors a realistic problematic ISE lab configuration so the
# report still demonstrates the full analysis engine.
# ─────────────────────────────────────────────────────────────

def demo_data():
    """Return a synthetic ISE data dict that contains common policy mistakes."""
    return {
        "policy_sets": [
            {"id": "ps-1", "name": "Wired 802.1X",
             "description": "", "state": "enabled", "default": False,
             "condition": {"conditionType": "ConditionAttributeList"}},
            {"id": "ps-2", "name": "MAB Fallback",
             "description": "MAB for printers and phones",
             "state": "enabled", "default": False,
             "condition": {"conditionType": "ConditionAttributeList"}},
            {"id": "ps-3", "name": "Default",
             "description": "Catch-all", "state": "enabled", "default": True,
             "condition": {}},
        ],
        "auth_rules": {
            "ps-1": [
                {"rule": {"name": "AD 802.1X", "condition": {
                    "conditionType": "ConditionAttributeList",
                    "attributeName": "AuthenticationMethod",
                    "attributeValue": "MSCHAPV2"}},
                 "identitySourceName": "AD1",
                 "ifAuthFail": "CONTINUE",
                 "ifUserNotFound": "REJECT",
                 "ifProcessFail": "DROP"},
                {"rule": {"name": "Default", "condition": {}},
                 "identitySourceName": "AD1",
                 "ifAuthFail": "CONTINUE",
                 "ifUserNotFound": "CONTINUE",
                 "ifProcessFail": "CONTINUE"},
            ],
            "ps-2": [
                {"rule": {"name": "MAB Any", "condition": {}},
                 "identitySourceName": "Internal Endpoints",
                 "ifAuthFail": "CONTINUE",
                 "ifUserNotFound": "CONTINUE",
                 "ifProcessFail": "CONTINUE"},
            ],
            "ps-3": [
                {"rule": {"name": "Catch-All", "condition": {}},
                 "identitySourceName": "Internal Users",
                 "ifAuthFail": "CONTINUE",
                 "ifUserNotFound": "CONTINUE",
                 "ifProcessFail": "CONTINUE"},
            ],
        },
        "authz_rules": {
            "ps-1": [
                {"rule": {"name": "IT Admins Full",
                          "description": "IT staff full access",
                          "state": "enabled",
                          "condition": {"conditionType": "ConditionAttributeList",
                                        "attributeName": "IdentityGroup",
                                        "attributeValue": "IT-Admins"}},
                 "profile": ["Corp_Full_Access"]},
                {"rule": {"name": "Corp Users",
                          "description": "",
                          "state": "enabled",
                          "condition": {"conditionType": "ConditionAttributeList",
                                        "attributeName": "IdentityGroup",
                                        "attributeValue": "Domain Users"}},
                 "profile": ["PermitAccess"]},
                {"rule": {"name": "Old_Test_Rule",
                          "description": "TEMP - remove after test",
                          "state": "disabled",
                          "condition": {"conditionType": "ConditionAttributeList",
                                        "attributeName": "IdentityGroup",
                                        "attributeValue": "TestGroup"}},
                 "profile": ["PermitAccess"]},
                {"rule": {"name": "Bypass Rule",
                          "description": "",
                          "state": "enabled",
                          "condition": {}},
                 "profile": ["PermitAccess"]},
                {"rule": {"name": "Default",
                          "description": "",
                          "state": "enabled",
                          "condition": {}},
                 "profile": ["PermitAccess"]},
            ],
            "ps-2": [
                {"rule": {"name": "Approved Endpoints",
                          "description": "",
                          "state": "enabled",
                          "condition": {"conditionType": "ConditionAttributeList",
                                        "attributeName": "EndpointGroup",
                                        "attributeValue": "Approved-Endpoints"}},
                 "profile": ["Limited_Access"]},
                {"rule": {"name": "Default",
                          "description": "",
                          "state": "enabled",
                          "condition": {}},
                 "profile": ["PermitAccess"]},
            ],
            "ps-3": [
                {"rule": {"name": "Catch-All Permit",
                          "description": "",
                          "state": "enabled",
                          "condition": {}},
                 "profile": ["PermitAccess"]},
            ],
        },
        "authz_profiles": [
            {"name": "Corp_Full_Access", "accessType": "ACCESS_ACCEPT",
             "daclName": "PERMIT_ALL", "vlan": {"nameID": "CORP"},
             "sessionTimeout": 28800, "reauthTimeout": 0},
            {"name": "Limited_Access", "accessType": "ACCESS_ACCEPT",
             "daclName": "", "vlan": {"nameID": "IOT"},
             "sessionTimeout": 0, "reauthTimeout": 0},
            {"name": "Guest_Access", "accessType": "ACCESS_ACCEPT",
             "daclName": "", "vlan": {"nameID": "GUEST"},
             "sessionTimeout": 0, "reauthTimeout": 0},
            {"name": "Remediation", "accessType": "ACCESS_ACCEPT",
             "daclName": "ACL-REMEDIATION", "vlan": {"nameID": "QUARANTINE"},
             "sessionTimeout": 3600, "reauthTimeout": 0},
            {"name": "GhostProfile", "accessType": "ACCESS_ACCEPT",
             "daclName": "", "vlan": {}, "sessionTimeout": 0, "reauthTimeout": 0},
        ],
        "allowed_protocols": [
            {"name": "Default Network Access",
             "allowEapTls": True, "allowPeap": True, "allowEapFast": False,
             "allowMsChapV2": True, "allowPapAscend": True,
             "allowChap": False, "allowMsChap": False,
             "allowLeap": True, "allowEapMd5": False},
            {"name": "Legacy Devices",
             "allowEapTls": False, "allowPeap": False, "allowEapFast": False,
             "allowMsChapV2": False, "allowPapAscend": True,
             "allowChap": True, "allowMsChap": True,
             "allowLeap": True, "allowEapMd5": True},
        ],
        "network_devices": [{"id": f"nd-{i}", "name": f"Switch-{i:03d}"}
                            for i in range(1, 48)],
        "ndgs": [
            {"id": "ndg-1", "name": "All Device Types"},
            {"id": "ndg-2", "name": "Wired"},
            {"id": "ndg-3", "name": "Wireless"},
        ],
        "identity_groups": [
            {"id": "ig-1", "name": "Domain Users"},
            {"id": "ig-2", "name": "IT-Admins"},
        ],
        "identity_stores": ["AD1", "Internal Users", "Internal Endpoints"],
        "collection_errors": ["Demo mode — ISE API not reachable. "
                              "Showing synthetic example data."],
    }


# ─────────────────────────────────────────────────────────────
def main():
    demo_mode = "--demo" in sys.argv

    print("=" * 62)
    print("  Cisco ISE 3.0 Patch 3 -- Policy Analytics Tool")
    print(f"  Target  : {ISE_IP}")
    print(f"  User    : {USERNAME}")
    print(f"  Output  : {OUTPUT_HTML}")
    if demo_mode:
        print("  Mode    : DEMO (synthetic example data)")
    print("=" * 62)
    print()

    if demo_mode:
        data = demo_data()
        print("  [*] Using built-in demo data (--demo flag)")
    else:
        data = collect_data()   # ise_login() called inside

    # If no real data came back, automatically fall through to demo
    has_live_data = (data["policy_sets"] or data["authz_profiles"]
                     or data["allowed_protocols"] or data["network_devices"])

    if not has_live_data and not demo_mode:
        print()
        print("  [!] No data retrieved from ISE — switching to demo mode.")
        print("      The report will show an EXAMPLE analysis to illustrate")
        print("      findings and recommendations. Once the API is accessible,")
        print("      re-run without --demo to analyse the live policy.")
        print()
        data = demo_data()

    findings = analyze(data)
    html     = generate_html(data, findings)

    with open(OUTPUT_HTML, "w", encoding="utf-8") as fh:
        fh.write(html)

    c = counts(findings)
    score, _, label = score_calc(c)

    print("=" * 62)
    print(f"  Report  : {OUTPUT_HTML}")
    if not has_live_data and not demo_mode:
        print("  Note    : Report uses EXAMPLE data (API unreachable)")
    print(f"  Score   : {score}/100 -- {label}")
    print(f"  Issues  : {c['critical']} Critical | {c['high']} High | "
          f"{c['warning']} Warning | {c['info']} Info")
    print("=" * 62)


if __name__ == "__main__":
    main()
