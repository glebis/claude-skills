#!/usr/bin/env python3
"""Zoom Meetings API client for Claude Code skill."""

import argparse
import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Optional
import requests

def get_local_timezone() -> str:
    """Get the local timezone name (e.g., 'America/Los_Angeles')."""
    try:
        # Try to read from /etc/localtime symlink (macOS/Linux)
        import subprocess
        result = subprocess.run(
            ["readlink", "/etc/localtime"],
            capture_output=True, text=True
        )
        if result.returncode == 0:
            # Path like /var/db/timezone/zoneinfo/America/Los_Angeles
            path = result.stdout.strip()
            if "zoneinfo/" in path:
                return path.split("zoneinfo/")[-1]
    except:
        pass

    try:
        # Fallback: use Python's time module
        import time as time_module
        if time_module.daylight:
            offset = -time_module.altzone
        else:
            offset = -time_module.timezone
        # Convert to hours for common timezone mapping
        hours = offset // 3600
        # Common US timezone mappings
        tz_map = {
            -8: "America/Los_Angeles",
            -7: "America/Denver",
            -6: "America/Chicago",
            -5: "America/New_York",
            0: "UTC",
            1: "Europe/London",
            2: "Europe/Berlin",
            3: "Europe/Moscow",
        }
        return tz_map.get(hours, "UTC")
    except:
        return "UTC"

CREDENTIALS_DIR = Path.home() / ".zoom_credentials"
CREDENTIALS_FILE = CREDENTIALS_DIR / "credentials.json"
TOKEN_FILE = CREDENTIALS_DIR / "token.json"
OAUTH_TOKEN_FILE = CREDENTIALS_DIR / "oauth_token.json"

BASE_URL = "https://api.zoom.us/v2"
TOKEN_URL = "https://zoom.us/oauth/token"


def load_credentials() -> Optional[dict]:
    """Load credentials from file."""
    if not CREDENTIALS_FILE.exists():
        return None
    try:
        with open(CREDENTIALS_FILE) as f:
            creds = json.load(f)
        required = ["account_id", "client_id", "client_secret"]
        if all(k in creds for k in required):
            return creds
    except (json.JSONDecodeError, IOError):
        pass
    return None


def get_access_token(creds: dict) -> Optional[str]:
    """Get access token using Server-to-Server OAuth."""
    # Check for cached token
    if TOKEN_FILE.exists():
        try:
            with open(TOKEN_FILE) as f:
                token_data = json.load(f)
            # Check if token is still valid (with 5 min buffer)
            if token_data.get("expires_at", 0) > time.time() + 300:
                return token_data.get("access_token")
        except (json.JSONDecodeError, IOError):
            pass

    # Request new token
    auth = (creds["client_id"], creds["client_secret"])
    params = {
        "grant_type": "account_credentials",
        "account_id": creds["account_id"]
    }

    try:
        resp = requests.post(TOKEN_URL, auth=auth, params=params)
        if resp.status_code != 200:
            error_detail = resp.text
            try:
                error_detail = resp.json()
            except:
                pass
            print(f"Token error ({resp.status_code}): {error_detail}", file=sys.stderr)
            return None
        data = resp.json()

        # Cache token
        token_data = {
            "access_token": data["access_token"],
            "expires_at": time.time() + data.get("expires_in", 3600)
        }
        CREDENTIALS_DIR.mkdir(parents=True, exist_ok=True)
        with open(TOKEN_FILE, "w") as f:
            json.dump(token_data, f)

        return data["access_token"]
    except requests.RequestException as e:
        print(f"Error getting access token: {e}", file=sys.stderr)
        return None


def get_oauth_token() -> Optional[str]:
    """Get OAuth access token for recordings (with refresh)."""
    if not OAUTH_TOKEN_FILE.exists():
        return None

    try:
        with open(OAUTH_TOKEN_FILE) as f:
            token_data = json.load(f)
    except (json.JSONDecodeError, IOError):
        return None

    # Check if token is still valid (with 5 min buffer)
    if token_data.get("expires_at", 0) > time.time() + 300:
        return token_data.get("access_token")

    # Refresh the token
    client_id = token_data.get("client_id")
    client_secret = token_data.get("client_secret")
    refresh_token = token_data.get("refresh_token")

    if not all([client_id, client_secret, refresh_token]):
        return None

    try:
        resp = requests.post(TOKEN_URL,
            auth=(client_id, client_secret),
            data={
                "grant_type": "refresh_token",
                "refresh_token": refresh_token
            })
        if resp.status_code != 200:
            print(f"OAuth refresh error: {resp.text}", file=sys.stderr)
            return None

        data = resp.json()
        # Update stored tokens
        token_data["access_token"] = data["access_token"]
        token_data["refresh_token"] = data.get("refresh_token", refresh_token)
        token_data["expires_at"] = time.time() + data.get("expires_in", 3600)

        with open(OAUTH_TOKEN_FILE, "w") as f:
            json.dump(token_data, f, indent=2)

        return data["access_token"]
    except requests.RequestException as e:
        print(f"OAuth refresh failed: {e}", file=sys.stderr)
        return None


def api_request(method: str, endpoint: str, token: str, data: dict = None) -> dict:
    """Make authenticated API request."""
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    url = f"{BASE_URL}{endpoint}"

    try:
        if method == "GET":
            resp = requests.get(url, headers=headers, params=data)
        elif method == "POST":
            resp = requests.post(url, headers=headers, json=data)
        elif method == "PATCH":
            resp = requests.patch(url, headers=headers, json=data)
        elif method == "DELETE":
            resp = requests.delete(url, headers=headers)
            if resp.status_code == 204:
                return {"success": True}
        else:
            return {"error": f"Unknown method: {method}"}

        resp.raise_for_status()
        if resp.text:
            return resp.json()
        return {"success": True}
    except requests.RequestException as e:
        error_msg = str(e)
        if hasattr(e, 'response') and e.response is not None:
            try:
                error_data = e.response.json()
                error_msg = error_data.get("message", str(e))
            except:
                pass
        return {"error": error_msg}


def cmd_setup(args):
    """Check setup status."""
    status = {
        "credentials_dir": str(CREDENTIALS_DIR),
        "credentials_file_exists": CREDENTIALS_FILE.exists(),
        "credentials_valid": False,
        "token_cached": TOKEN_FILE.exists(),
        "authenticated": False
    }

    creds = load_credentials()
    if creds:
        status["credentials_valid"] = True
        token = get_access_token(creds)
        if token:
            status["authenticated"] = True
            # Try to get user info to verify
            result = api_request("GET", "/users/me", token)
            if "id" in result:
                status["user_email"] = result.get("email", "unknown")
                status["user_id"] = result.get("id")

    if args.json:
        print(json.dumps(status, indent=2))
    else:
        print("# Zoom Setup Status\n")
        if status["credentials_valid"] and status["authenticated"]:
            print("**Status:** Configured and authenticated")
            if "user_email" in status:
                print(f"**Account:** {status['user_email']}")
        elif status["credentials_valid"]:
            print("**Status:** Credentials found but authentication failed")
            print("\nCheck your credentials in:")
            print(f"  {CREDENTIALS_FILE}")
        else:
            print("**Status:** Not configured")
            print("\n## Setup Instructions\n")
            print("1. Create a Server-to-Server OAuth app at marketplace.zoom.us")
            print("2. Create credentials file:")
            print(f"   mkdir -p {CREDENTIALS_DIR}")
            print(f"   Create {CREDENTIALS_FILE} with:")
            print('   {"account_id": "...", "client_id": "...", "client_secret": "..."}')


def cmd_list(args):
    """List meetings."""
    creds = load_credentials()
    if not creds:
        print("Error: Not configured. Run 'setup' first.", file=sys.stderr)
        sys.exit(1)

    token = get_access_token(creds)
    if not token:
        print("Error: Authentication failed.", file=sys.stderr)
        sys.exit(1)

    params = {"page_size": args.limit}
    if args.type:
        params["type"] = args.type

    result = api_request("GET", "/users/me/meetings", token, params)

    if "error" in result:
        print(f"Error: {result['error']}", file=sys.stderr)
        sys.exit(1)

    meetings = result.get("meetings", [])

    if args.json:
        print(json.dumps(meetings, indent=2))
    else:
        if not meetings:
            print("No meetings found.")
            return

        print(f"# Zoom Meetings ({len(meetings)} found)\n")
        for m in meetings:
            print(f"## {m.get('topic', 'Untitled')}")
            print(f"**ID:** {m.get('id')}")
            if m.get("start_time"):
                start = m["start_time"].replace("T", " ").replace("Z", " UTC")
                print(f"**Start:** {start}")
            print(f"**Duration:** {m.get('duration', 0)} minutes")
            if m.get("join_url"):
                print(f"**Join URL:** {m['join_url']}")
            print()


def cmd_get(args):
    """Get meeting details."""
    creds = load_credentials()
    if not creds:
        print("Error: Not configured. Run 'setup' first.", file=sys.stderr)
        sys.exit(1)

    token = get_access_token(creds)
    if not token:
        print("Error: Authentication failed.", file=sys.stderr)
        sys.exit(1)

    result = api_request("GET", f"/meetings/{args.meeting_id}", token)

    if "error" in result:
        print(f"Error: {result['error']}", file=sys.stderr)
        sys.exit(1)

    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print(f"# {result.get('topic', 'Untitled')}\n")
        print(f"**ID:** {result.get('id')}")
        print(f"**UUID:** {result.get('uuid')}")
        print(f"**Host:** {result.get('host_email')}")
        if result.get("start_time"):
            start = result["start_time"].replace("T", " ").replace("Z", " UTC")
            print(f"**Start:** {start}")
        print(f"**Duration:** {result.get('duration', 0)} minutes")
        print(f"**Timezone:** {result.get('timezone', 'UTC')}")
        if result.get("agenda"):
            print(f"**Agenda:** {result['agenda']}")
        print(f"\n**Join URL:** {result.get('join_url')}")
        print(f"**Start URL:** {result.get('start_url')}")
        if result.get("password"):
            print(f"**Password:** {result['password']}")


def cmd_create(args):
    """Create a meeting."""
    creds = load_credentials()
    if not creds:
        print("Error: Not configured. Run 'setup' first.", file=sys.stderr)
        sys.exit(1)

    token = get_access_token(creds)
    if not token:
        print("Error: Authentication failed.", file=sys.stderr)
        sys.exit(1)

    meeting_data = {
        "topic": args.topic,
        "type": 2,  # Scheduled meeting
        "duration": args.duration,
    }

    if args.start:
        meeting_data["start_time"] = args.start
        # Always set timezone when scheduling - use local timezone if not specified
        # This ensures the start time is interpreted as local time, not UTC
        meeting_data["timezone"] = args.timezone if args.timezone else get_local_timezone()
    else:
        meeting_data["type"] = 1  # Instant meeting
        if args.timezone:
            meeting_data["timezone"] = args.timezone

    if args.agenda:
        meeting_data["agenda"] = args.agenda

    if args.password:
        meeting_data["password"] = args.password

    settings = {}
    if args.waiting_room:
        settings["waiting_room"] = True
    if args.invite:
        settings["meeting_invitees"] = [{"email": email} for email in args.invite]
    if settings:
        meeting_data["settings"] = settings

    result = api_request("POST", "/users/me/meetings", token, meeting_data)

    if "error" in result:
        print(f"Error: {result['error']}", file=sys.stderr)
        sys.exit(1)

    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print("# Meeting Created\n")
        print(f"**Topic:** {result.get('topic')}")
        print(f"**ID:** {result.get('id')}")
        if result.get("start_time"):
            start = result["start_time"].replace("T", " ").replace("Z", " UTC")
            print(f"**Start:** {start}")
        print(f"**Duration:** {result.get('duration', 0)} minutes")
        print(f"\n**Join URL:** {result.get('join_url')}")
        print(f"**Start URL (host only):** {result.get('start_url')}")
        if result.get("password"):
            print(f"**Password:** {result['password']}")


def cmd_update(args):
    """Update a meeting."""
    creds = load_credentials()
    if not creds:
        print("Error: Not configured. Run 'setup' first.", file=sys.stderr)
        sys.exit(1)

    token = get_access_token(creds)
    if not token:
        print("Error: Authentication failed.", file=sys.stderr)
        sys.exit(1)

    update_data = {}
    if args.topic:
        update_data["topic"] = args.topic
    if args.start:
        update_data["start_time"] = args.start
        # Always set timezone when updating start time - use local timezone if not specified
        # This ensures the start time is interpreted as local time, not UTC
        update_data["timezone"] = args.timezone if args.timezone else get_local_timezone()
    elif args.timezone:
        update_data["timezone"] = args.timezone
    if args.duration:
        update_data["duration"] = args.duration
    if args.agenda:
        update_data["agenda"] = args.agenda

    if not update_data:
        print("Error: No fields to update specified.", file=sys.stderr)
        sys.exit(1)

    result = api_request("PATCH", f"/meetings/{args.meeting_id}", token, update_data)

    if "error" in result:
        print(f"Error: {result['error']}", file=sys.stderr)
        sys.exit(1)

    if args.json:
        print(json.dumps({"success": True, "meeting_id": args.meeting_id}, indent=2))
    else:
        print(f"Meeting {args.meeting_id} updated successfully.")


def cmd_delete(args):
    """Delete a meeting."""
    creds = load_credentials()
    if not creds:
        print("Error: Not configured. Run 'setup' first.", file=sys.stderr)
        sys.exit(1)

    token = get_access_token(creds)
    if not token:
        print("Error: Authentication failed.", file=sys.stderr)
        sys.exit(1)

    result = api_request("DELETE", f"/meetings/{args.meeting_id}", token)

    if "error" in result:
        print(f"Error: {result['error']}", file=sys.stderr)
        sys.exit(1)

    if args.json:
        print(json.dumps({"success": True, "meeting_id": args.meeting_id}, indent=2))
    else:
        print(f"Meeting {args.meeting_id} deleted successfully.")


def cmd_recordings(args):
    """List cloud recordings."""
    token = get_oauth_token()
    if not token:
        print("Error: OAuth not configured for recordings.", file=sys.stderr)
        print("Run the OAuth flow to authorize recording access.", file=sys.stderr)
        sys.exit(1)

    params = {"page_size": args.limit}
    if args.start:
        params["from"] = args.start
    if args.end:
        params["to"] = args.end

    result = api_request("GET", "/users/me/recordings", token, params)

    if "error" in result:
        print(f"Error: {result['error']}", file=sys.stderr)
        sys.exit(1)

    meetings = result.get("meetings", [])

    if args.json:
        print(json.dumps(meetings, indent=2))
    else:
        if not meetings:
            print("No recordings found.")
            return

        total_recordings = sum(len(m.get("recording_files", [])) for m in meetings)
        print(f"# Zoom Recordings ({len(meetings)} meetings, {total_recordings} files)\n")

        for m in meetings:
            print(f"## {m.get('topic', 'Untitled')}")
            print(f"**Meeting ID:** {m.get('id')}")
            if m.get("start_time"):
                start = m["start_time"].replace("T", " ").replace("Z", " UTC")
                print(f"**Date:** {start}")
            print(f"**Duration:** {m.get('duration', 0)} minutes")

            recording_files = m.get("recording_files", [])
            if recording_files:
                print(f"**Files ({len(recording_files)}):**")
                for rf in recording_files:
                    file_type = rf.get("file_type", "unknown")
                    file_size = rf.get("file_size", 0)
                    size_mb = file_size / (1024 * 1024) if file_size else 0
                    status = rf.get("status", "")
                    download_url = rf.get("download_url", "")
                    play_url = rf.get("play_url", "")

                    print(f"  - **{file_type}** ({size_mb:.1f} MB) - {status}")
                    if play_url:
                        print(f"    Play: {play_url}")
                    if download_url and args.show_downloads:
                        print(f"    Download: {download_url}")
            print()


def cmd_recording(args):
    """Get recordings for a specific meeting."""
    token = get_oauth_token()
    if not token:
        print("Error: OAuth not configured for recordings.", file=sys.stderr)
        print("Run the OAuth flow to authorize recording access.", file=sys.stderr)
        sys.exit(1)

    result = api_request("GET", f"/meetings/{args.meeting_id}/recordings", token)

    if "error" in result:
        print(f"Error: {result['error']}", file=sys.stderr)
        sys.exit(1)

    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print(f"# Recording: {result.get('topic', 'Untitled')}\n")
        print(f"**Meeting ID:** {result.get('id')}")
        print(f"**UUID:** {result.get('uuid')}")
        if result.get("start_time"):
            start = result["start_time"].replace("T", " ").replace("Z", " UTC")
            print(f"**Date:** {start}")
        print(f"**Duration:** {result.get('duration', 0)} minutes")
        print(f"**Total Size:** {result.get('total_size', 0) / (1024*1024):.1f} MB")

        if result.get("share_url"):
            print(f"\n**Share URL:** {result['share_url']}")
        if result.get("password"):
            print(f"**Password:** {result['password']}")

        recording_files = result.get("recording_files", [])
        if recording_files:
            print(f"\n**Files ({len(recording_files)}):**")
            for rf in recording_files:
                file_type = rf.get("file_type", "unknown")
                file_size = rf.get("file_size", 0)
                size_mb = file_size / (1024 * 1024) if file_size else 0
                status = rf.get("status", "")
                recording_type = rf.get("recording_type", "")

                print(f"\n### {file_type} ({recording_type})")
                print(f"- Size: {size_mb:.1f} MB")
                print(f"- Status: {status}")
                if rf.get("play_url"):
                    print(f"- Play: {rf['play_url']}")
                if rf.get("download_url"):
                    print(f"- Download: {rf['download_url']}")


def main():
    parser = argparse.ArgumentParser(description="Zoom Meetings CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Setup command
    setup_parser = subparsers.add_parser("setup", help="Check setup status")
    setup_parser.add_argument("--json", action="store_true", help="JSON output")
    setup_parser.set_defaults(func=cmd_setup)

    # List command
    list_parser = subparsers.add_parser("list", help="List meetings")
    list_parser.add_argument("--type", choices=["scheduled", "live", "upcoming", "previous"],
                            default="upcoming", help="Meeting type filter")
    list_parser.add_argument("--limit", type=int, default=30, help="Max results")
    list_parser.add_argument("--json", action="store_true", help="JSON output")
    list_parser.set_defaults(func=cmd_list)

    # Get command
    get_parser = subparsers.add_parser("get", help="Get meeting details")
    get_parser.add_argument("meeting_id", help="Meeting ID")
    get_parser.add_argument("--json", action="store_true", help="JSON output")
    get_parser.set_defaults(func=cmd_get)

    # Create command
    create_parser = subparsers.add_parser("create", help="Create a meeting")
    create_parser.add_argument("topic", help="Meeting topic/title")
    create_parser.add_argument("--start", help="Start time (ISO format: 2024-12-24T14:00:00)")
    create_parser.add_argument("--duration", type=int, default=60, help="Duration in minutes")
    create_parser.add_argument("--timezone", help="Timezone (e.g., America/Los_Angeles)")
    create_parser.add_argument("--agenda", help="Meeting agenda/description")
    create_parser.add_argument("--password", help="Meeting password")
    create_parser.add_argument("--waiting-room", action="store_true", help="Enable waiting room")
    create_parser.add_argument("--invite", action="append", help="Email to invite (can be used multiple times)")
    create_parser.add_argument("--json", action="store_true", help="JSON output")
    create_parser.set_defaults(func=cmd_create)

    # Update command
    update_parser = subparsers.add_parser("update", help="Update a meeting")
    update_parser.add_argument("meeting_id", help="Meeting ID")
    update_parser.add_argument("--topic", help="New topic")
    update_parser.add_argument("--start", help="New start time")
    update_parser.add_argument("--duration", type=int, help="New duration")
    update_parser.add_argument("--timezone", help="New timezone")
    update_parser.add_argument("--agenda", help="New agenda")
    update_parser.add_argument("--json", action="store_true", help="JSON output")
    update_parser.set_defaults(func=cmd_update)

    # Delete command
    delete_parser = subparsers.add_parser("delete", help="Delete a meeting")
    delete_parser.add_argument("meeting_id", help="Meeting ID")
    delete_parser.add_argument("--json", action="store_true", help="JSON output")
    delete_parser.set_defaults(func=cmd_delete)

    # Recordings command (list all)
    recordings_parser = subparsers.add_parser("recordings", help="List cloud recordings")
    recordings_parser.add_argument("--start", help="Start date (YYYY-MM-DD), default: 30 days ago")
    recordings_parser.add_argument("--end", help="End date (YYYY-MM-DD), default: today")
    recordings_parser.add_argument("--limit", type=int, default=30, help="Max results")
    recordings_parser.add_argument("--show-downloads", action="store_true", help="Show download URLs")
    recordings_parser.add_argument("--json", action="store_true", help="JSON output")
    recordings_parser.set_defaults(func=cmd_recordings)

    # Recording command (single meeting)
    recording_parser = subparsers.add_parser("recording", help="Get recording for a specific meeting")
    recording_parser.add_argument("meeting_id", help="Meeting ID")
    recording_parser.add_argument("--json", action="store_true", help="JSON output")
    recording_parser.set_defaults(func=cmd_recording)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
