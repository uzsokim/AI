#!/usr/bin/env python3
"""
Cisco ISE — Add endpoint MAC to endpoint group.

Usage:
    python ise_add_endpoint.py
"""

import sys
import getpass
import requests
import json
import urllib3

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ── Configuration ────────────────────────────────────────────
ISE_IP         = "10.81.145.7"
USERNAME       = "admin"
PASSWORD       = getpass.getpass(f"Password for {USERNAME}@{ISE_IP}: ")
TARGET_MAC     = "00:C2:C6:CA:FA:C6"
TARGET_GROUP   = "uzsoki"
TIMEOUT        = 30

ERS_BASE       = f"https://{ISE_IP}:9060/ers/config"
HEADERS        = {"Content-Type": "application/json", "Accept": "application/json"}

# ── Session ──────────────────────────────────────────────────
session = requests.Session()
session.verify = False
session.auth   = (USERNAME, PASSWORD)


def ers_get(path, params=None):
    url = f"{ERS_BASE}{path}"
    r = session.get(url, headers=HEADERS, params=params, timeout=TIMEOUT)
    r.raise_for_status()
    return r.json()


def ers_post(path, body):
    url = f"{ERS_BASE}{path}"
    r = session.post(url, headers=HEADERS, json=body, timeout=TIMEOUT)
    r.raise_for_status()
    return r


def ers_put(path, body):
    url = f"{ERS_BASE}{path}"
    r = session.put(url, headers=HEADERS, json=body, timeout=TIMEOUT)
    r.raise_for_status()
    return r


def get_all_pages(resource):
    """Return all items from a paginated ERS list endpoint."""
    items = []
    page  = 1
    while True:
        data = ers_get(f"/{resource}", params={"page": page, "size": 100})
        resources = data.get("SearchResult", {}).get("resources", [])
        items.extend(resources)
        next_page = data.get("SearchResult", {}).get("nextPage")
        if not next_page:
            break
        page += 1
    return items


def find_endpoint_group(name):
    """Return (id, name) of the endpoint group matching name (case-insensitive)."""
    groups = get_all_pages("endpointgroup")
    for g in groups:
        if g.get("name", "").lower() == name.lower():
            return g["id"], g["name"]
    return None, None


def find_endpoint(mac):
    """Return endpoint dict if MAC already exists, else None."""
    mac_upper = mac.upper()
    try:
        data = ers_get(f"/endpoint/name/{mac_upper}")
        return data.get("ERSEndPoint")
    except requests.HTTPError as e:
        if e.response.status_code == 404:
            return None
        raise


def create_endpoint(mac, group_id):
    """Create a new endpoint with the given MAC and assign it to group_id."""
    body = {
        "ERSEndPoint": {
            "mac":             mac.upper(),
            "groupId":         group_id,
            "staticGroupAssignment": True,
        }
    }
    r = ers_post("/endpoint", body)
    location = r.headers.get("Location", "")
    new_id   = location.rstrip("/").split("/")[-1]
    return new_id


def update_endpoint_group(endpoint_id, group_id, existing):
    """Update an existing endpoint's group assignment."""
    endpoint = existing.copy()
    endpoint["groupId"]              = group_id
    endpoint["staticGroupAssignment"] = True
    body = {"ERSEndPoint": endpoint}
    ers_put(f"/endpoint/{endpoint_id}", body)


def main():
    print(f"\n[*] Connecting to ISE at {ISE_IP}...")

    # Verify ERS connectivity
    try:
        ers_get("/endpointgroup", params={"page": 1, "size": 1})
        print("[+] ERS API authenticated successfully")
    except requests.HTTPError as e:
        print(f"[-] ERS auth failed: {e.response.status_code} {e.response.text[:200]}")
        sys.exit(1)
    except Exception as e:
        print(f"[-] Connection error: {e}")
        sys.exit(1)

    # Find the endpoint group
    print(f"\n[*] Looking up endpoint group: '{TARGET_GROUP}'...")
    group_id, group_name = find_endpoint_group(TARGET_GROUP)
    if not group_id:
        print(f"[-] Endpoint group '{TARGET_GROUP}' not found.")
        print("    Available groups:")
        for g in get_all_pages("endpointgroup"):
            print(f"      {g['name']}")
        sys.exit(1)
    print(f"[+] Found group: {group_name} (id={group_id})")

    # Check if endpoint already exists
    print(f"\n[*] Checking if endpoint {TARGET_MAC} exists...")
    existing = find_endpoint(TARGET_MAC)

    if existing:
        ep_id = existing["id"]
        current_group = existing.get("groupId", "")
        if current_group == group_id:
            print(f"[=] Endpoint already in group '{TARGET_GROUP}' — nothing to do.")
            sys.exit(0)
        print(f"[*] Endpoint exists (id={ep_id}), updating group assignment...")
        update_endpoint_group(ep_id, group_id, existing)
        print(f"[+] Endpoint {TARGET_MAC} moved to group '{TARGET_GROUP}'")
    else:
        print(f"[*] Endpoint not found — creating new endpoint...")
        new_id = create_endpoint(TARGET_MAC, group_id)
        print(f"[+] Endpoint {TARGET_MAC} created and added to group '{TARGET_GROUP}' (id={new_id})")

    print("\nDone.\n")


if __name__ == "__main__":
    main()
