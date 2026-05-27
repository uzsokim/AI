#!/usr/bin/env python3
"""Show Google Drive storage quota for the authenticated account."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

from google.auth.exceptions import RefreshError
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build


SCOPES = ["https://www.googleapis.com/auth/drive.metadata.readonly"]
DEFAULT_CREDENTIALS = Path("credentials.json")
DEFAULT_TOKEN = Path("token.json")


def human_size(num_bytes: int | None) -> str:
    """Convert bytes into a readable storage value."""
    if num_bytes is None:
        return "Unlimited / not reported"

    size = float(num_bytes)
    units = ["B", "KB", "MB", "GB", "TB", "PB"]
    for unit in units:
        if size < 1024 or unit == units[-1]:
            if unit == "B":
                return f"{int(size)} {unit}"
            return f"{size:.2f} {unit}"
        size /= 1024

    return f"{num_bytes} B"


def parse_int(value: str | None) -> int | None:
    if value is None:
        return None
    return int(value)


def get_credentials(credentials_path: Path, token_path: Path) -> Credentials:
    creds = None

    if token_path.exists():
        creds = Credentials.from_authorized_user_file(str(token_path), SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
            except RefreshError:
                creds = None

        if not creds or not creds.valid:
            if not credentials_path.exists():
                raise FileNotFoundError(
                    f"Missing {credentials_path}. Download OAuth client credentials "
                    "from Google Cloud Console and save them here."
                )

            flow = InstalledAppFlow.from_client_secrets_file(
                str(credentials_path),
                SCOPES,
            )
            creds = flow.run_local_server(port=0)

        token_path.write_text(creds.to_json(), encoding="utf-8")

    return creds


def get_storage_quota(credentials_path: Path, token_path: Path) -> dict[str, Any]:
    creds = get_credentials(credentials_path, token_path)
    service = build("drive", "v3", credentials=creds)
    response = (
        service.about()
        .get(fields="user(emailAddress,displayName),storageQuota")
        .execute()
    )
    return response


def print_quota(response: dict[str, Any]) -> None:
    user = response.get("user", {})
    quota = response.get("storageQuota", {})

    limit = parse_int(quota.get("limit"))
    usage = parse_int(quota.get("usage")) or 0
    usage_in_drive = parse_int(quota.get("usageInDrive")) or 0
    usage_in_trash = parse_int(quota.get("usageInDriveTrash")) or 0
    free = None if limit is None else max(limit - usage, 0)
    percent_used = None if limit in (None, 0) else usage / limit * 100

    print("Google Drive storage")
    print("====================")
    if user:
        print(f"Account: {user.get('displayName', 'Unknown')} <{user.get('emailAddress', 'unknown')}>")

    print(f"Total:        {human_size(limit)}")
    print(f"Used:         {human_size(usage)}")
    if percent_used is not None:
        print(f"Used percent: {percent_used:.1f}%")
    print(f"Free:         {human_size(free)}")
    print()
    print("Breakdown")
    print(f"Drive files:  {human_size(usage_in_drive)}")
    print(f"Trash:        {human_size(usage_in_trash)}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Check Google Drive storage space.")
    parser.add_argument(
        "--credentials",
        type=Path,
        default=DEFAULT_CREDENTIALS,
        help="Path to Google OAuth client credentials JSON.",
    )
    parser.add_argument(
        "--token",
        type=Path,
        default=DEFAULT_TOKEN,
        help="Path to read/write OAuth token JSON.",
    )
    args = parser.parse_args()

    response = get_storage_quota(args.credentials, args.token)
    print_quota(response)


if __name__ == "__main__":
    main()
