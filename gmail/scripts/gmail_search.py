#!/usr/bin/env python3
"""
Gmail Search Skill - Search and fetch emails via Gmail API.

Supports free-text queries translated to Gmail search syntax,
plus helper flags for common filters.
"""

import argparse
import base64
import json
import os
import pickle
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# Configuration
CREDENTIALS_DIR = Path.home() / ".gmail_credentials"
TOKEN_FILE = CREDENTIALS_DIR / "token.pickle"
CLIENT_SECRETS_FILE = CREDENTIALS_DIR / "credentials.json"
SCOPE_FILE = CREDENTIALS_DIR / "scope.txt"

# Available scopes
SCOPES_MAP = {
    "readonly": ["https://www.googleapis.com/auth/gmail.readonly"],
    "modify": [
        "https://www.googleapis.com/auth/gmail.readonly",
        "https://www.googleapis.com/auth/gmail.modify",
    ],
    "full": ["https://mail.google.com/"],
}

DEFAULT_SCOPE = "readonly"


def get_current_scope() -> str:
    """Get currently configured scope."""
    if SCOPE_FILE.exists():
        return SCOPE_FILE.read_text().strip()
    return DEFAULT_SCOPE


def set_scope(scope: str) -> None:
    """Set and persist scope setting."""
    if scope not in SCOPES_MAP:
        raise ValueError(f"Invalid scope: {scope}. Choose from: {list(SCOPES_MAP.keys())}")
    SCOPE_FILE.write_text(scope)
    # Remove token to force re-auth with new scope
    if TOKEN_FILE.exists():
        TOKEN_FILE.unlink()


def get_credentials() -> Optional[Credentials]:
    """Get or refresh OAuth credentials."""
    creds = None
    scope = get_current_scope()
    scopes = SCOPES_MAP[scope]

    if TOKEN_FILE.exists():
        with open(TOKEN_FILE, "rb") as token:
            creds = pickle.load(token)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not CLIENT_SECRETS_FILE.exists():
                return None
            flow = InstalledAppFlow.from_client_secrets_file(str(CLIENT_SECRETS_FILE), scopes)
            creds = flow.run_local_server(port=0)

        CREDENTIALS_DIR.mkdir(parents=True, exist_ok=True)
        with open(TOKEN_FILE, "wb") as token:
            pickle.dump(creds, token)

    return creds


def build_query(
    query: str = "",
    from_addr: str = "",
    to_addr: str = "",
    subject: str = "",
    label: str = "",
    after: str = "",
    before: str = "",
    has_attachment: bool = False,
    is_unread: bool = False,
    is_starred: bool = False,
) -> str:
    """Build Gmail search query from parameters."""
    parts = []

    if query:
        parts.append(query)
    if from_addr:
        parts.append(f"from:{from_addr}")
    if to_addr:
        parts.append(f"to:{to_addr}")
    if subject:
        parts.append(f"subject:{subject}")
    if label:
        parts.append(f"label:{label}")
    if after:
        parts.append(f"after:{after}")
    if before:
        parts.append(f"before:{before}")
    if has_attachment:
        parts.append("has:attachment")
    if is_unread:
        parts.append("is:unread")
    if is_starred:
        parts.append("is:starred")

    return " ".join(parts)


def get_message_details(service, msg_id: str, full_body: bool = False) -> dict:
    """Fetch full message details."""
    format_type = "full" if full_body else "metadata"
    metadata_headers = ["From", "To", "Subject", "Date"]

    if full_body:
        msg = service.users().messages().get(userId="me", id=msg_id, format="full").execute()
    else:
        msg = (
            service.users()
            .messages()
            .get(userId="me", id=msg_id, format="metadata", metadataHeaders=metadata_headers)
            .execute()
        )

    headers = {h["name"]: h["value"] for h in msg.get("payload", {}).get("headers", [])}

    result = {
        "id": msg_id,
        "thread_id": msg.get("threadId"),
        "from": headers.get("From", ""),
        "to": headers.get("To", ""),
        "subject": headers.get("Subject", "(no subject)"),
        "date": headers.get("Date", ""),
        "snippet": msg.get("snippet", ""),
        "labels": msg.get("labelIds", []),
    }

    # Extract body if requested
    if full_body:
        body = extract_body(msg.get("payload", {}))
        result["body"] = body

    # Check for attachments
    attachments = []
    if "payload" in msg:
        attachments = extract_attachment_info(msg["payload"])
    if attachments:
        result["attachments"] = attachments

    return result


def extract_body(payload: dict) -> str:
    """Extract plain text body from message payload."""
    if "body" in payload and payload["body"].get("data"):
        return base64.urlsafe_b64decode(payload["body"]["data"]).decode("utf-8", errors="replace")

    if "parts" in payload:
        for part in payload["parts"]:
            if part.get("mimeType") == "text/plain":
                if "body" in part and part["body"].get("data"):
                    return base64.urlsafe_b64decode(part["body"]["data"]).decode(
                        "utf-8", errors="replace"
                    )
            # Recurse into multipart
            if "parts" in part:
                body = extract_body(part)
                if body:
                    return body

    return ""


def extract_attachment_info(payload: dict) -> list:
    """Extract attachment metadata from message payload."""
    attachments = []

    def recurse(part):
        if part.get("filename"):
            attachments.append(
                {
                    "filename": part["filename"],
                    "mime_type": part.get("mimeType", ""),
                    "size": part.get("body", {}).get("size", 0),
                    "attachment_id": part.get("body", {}).get("attachmentId"),
                }
            )
        if "parts" in part:
            for p in part["parts"]:
                recurse(p)

    recurse(payload)
    return attachments


def download_attachment(service, msg_id: str, attachment_id: str, filename: str, output_dir: str):
    """Download a specific attachment."""
    attachment = (
        service.users()
        .messages()
        .attachments()
        .get(userId="me", messageId=msg_id, id=attachment_id)
        .execute()
    )

    file_data = base64.urlsafe_b64decode(attachment["data"])
    output_path = Path(output_dir) / filename

    # Handle duplicate filenames
    counter = 1
    while output_path.exists():
        stem = Path(filename).stem
        suffix = Path(filename).suffix
        output_path = Path(output_dir) / f"{stem}_{counter}{suffix}"
        counter += 1

    output_path.write_bytes(file_data)
    return str(output_path)


def search_messages(
    service,
    query: str,
    limit: int = 20,
    full_body: bool = False,
    include_attachments: bool = False,
) -> list:
    """Search for messages matching query."""
    results = service.users().messages().list(userId="me", q=query, maxResults=limit).execute()

    messages = results.get("messages", [])
    detailed = []

    for msg in messages:
        details = get_message_details(service, msg["id"], full_body=full_body)
        if not include_attachments and "attachments" in details:
            del details["attachments"]
        detailed.append(details)

    return detailed


def format_markdown(messages: list, full_body: bool = False) -> str:
    """Format messages as markdown."""
    if not messages:
        return "No messages found."

    lines = [f"# Gmail Search Results ({len(messages)} messages)\n"]

    for msg in messages:
        lines.append(f"## {msg['subject']}")
        lines.append(f"**From:** {msg['from']}")
        lines.append(f"**To:** {msg['to']}")
        lines.append(f"**Date:** {msg['date']}")
        lines.append(f"**ID:** `{msg['id']}`")

        if msg.get("labels"):
            lines.append(f"**Labels:** {', '.join(msg['labels'])}")

        if msg.get("attachments"):
            att_list = ", ".join(a["filename"] for a in msg["attachments"])
            lines.append(f"**Attachments:** {att_list}")

        lines.append("")

        if full_body and msg.get("body"):
            lines.append("### Body")
            lines.append(msg["body"])
        else:
            lines.append(f"> {msg['snippet']}")

        lines.append("\n---\n")

    return "\n".join(lines)


def cmd_setup(args):
    """Check setup status or show instructions."""
    CREDENTIALS_DIR.mkdir(parents=True, exist_ok=True)

    status = {"configured": False, "scope": get_current_scope(), "token_valid": False}

    if not CLIENT_SECRETS_FILE.exists():
        status["error"] = "credentials.json not found"
        status["instructions"] = f"""
Gmail API not configured. To set up:

1. Save your OAuth credentials to: {CLIENT_SECRETS_FILE}

   Create a file with this structure:
   {{
     "installed": {{
       "client_id": "YOUR_CLIENT_ID",
       "client_secret": "YOUR_CLIENT_SECRET",
       "auth_uri": "https://accounts.google.com/o/oauth2/auth",
       "token_uri": "https://oauth2.googleapis.com/token",
       "redirect_uris": ["http://localhost"]
     }}
   }}

2. Run: python3 gmail_search.py auth

Current scope: {status['scope']} (change with --scope)
"""
    else:
        status["configured"] = True
        creds = get_credentials()
        if creds and creds.valid:
            status["token_valid"] = True
            status["message"] = "Gmail API configured and authenticated"
        else:
            status["message"] = "Credentials found but not authenticated. Run: python3 gmail_search.py auth"

    if args.json:
        print(json.dumps(status, indent=2))
    else:
        if status.get("instructions"):
            print(status["instructions"])
        else:
            print(f"Status: {'Ready' if status['token_valid'] else 'Needs authentication'}")
            print(f"Scope: {status['scope']}")
            if not status["token_valid"]:
                print("\nRun: python3 gmail_search.py auth")


def cmd_auth(args):
    """Authenticate with Gmail API."""
    if not CLIENT_SECRETS_FILE.exists():
        print(f"Error: {CLIENT_SECRETS_FILE} not found. Run 'setup' for instructions.")
        sys.exit(1)

    # Remove existing token to force re-auth
    if TOKEN_FILE.exists():
        TOKEN_FILE.unlink()

    creds = get_credentials()
    if creds and creds.valid:
        print("Authentication successful!")
        print(f"Scope: {get_current_scope()}")
    else:
        print("Authentication failed.")
        sys.exit(1)


def cmd_scope(args):
    """View or change scope."""
    if args.set:
        try:
            set_scope(args.set)
            print(f"Scope set to: {args.set}")
            print("Token cleared - re-authentication required.")
            print("Run: python3 gmail_search.py auth")
        except ValueError as e:
            print(f"Error: {e}")
            sys.exit(1)
    else:
        current = get_current_scope()
        print(f"Current scope: {current}")
        print(f"\nAvailable scopes:")
        for name, scopes in SCOPES_MAP.items():
            marker = " (current)" if name == current else ""
            print(f"  {name}{marker}: {scopes[0]}")


def cmd_search(args):
    """Search emails."""
    creds = get_credentials()
    if not creds:
        print("Not authenticated. Run 'setup' or 'auth' first.")
        sys.exit(1)

    service = build("gmail", "v1", credentials=creds)

    query = build_query(
        query=args.query or "",
        from_addr=args.from_addr or "",
        to_addr=args.to_addr or "",
        subject=args.subject or "",
        label=args.label or "",
        after=args.after or "",
        before=args.before or "",
        has_attachment=args.has_attachment,
        is_unread=args.unread,
        is_starred=args.starred,
    )

    if not query:
        query = "in:inbox"

    try:
        messages = search_messages(
            service,
            query=query,
            limit=args.limit,
            full_body=args.full,
            include_attachments=args.attachments,
        )

        if args.json:
            print(json.dumps(messages, indent=2))
        else:
            print(format_markdown(messages, full_body=args.full))

    except HttpError as e:
        print(f"Gmail API error: {e}")
        sys.exit(1)


def cmd_download(args):
    """Download attachments from a message."""
    creds = get_credentials()
    if not creds:
        print("Not authenticated. Run 'setup' or 'auth' first.")
        sys.exit(1)

    service = build("gmail", "v1", credentials=creds)
    output_dir = args.output or str(Path.home() / "Downloads" / "gmail_attachments")
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    try:
        msg = (
            service.users().messages().get(userId="me", id=args.message_id, format="full").execute()
        )

        attachments = extract_attachment_info(msg.get("payload", {}))
        if not attachments:
            print("No attachments found in this message.")
            return

        downloaded = []
        for att in attachments:
            if att.get("attachment_id"):
                path = download_attachment(
                    service, args.message_id, att["attachment_id"], att["filename"], output_dir
                )
                downloaded.append({"filename": att["filename"], "path": path, "size": att["size"]})

        if args.json:
            print(json.dumps({"downloaded": downloaded}, indent=2))
        else:
            print(f"Downloaded {len(downloaded)} attachment(s) to {output_dir}:")
            for d in downloaded:
                print(f"  - {d['filename']} ({d['size']} bytes)")

    except HttpError as e:
        print(f"Gmail API error: {e}")
        sys.exit(1)


def cmd_labels(args):
    """List available labels."""
    creds = get_credentials()
    if not creds:
        print("Not authenticated. Run 'setup' or 'auth' first.")
        sys.exit(1)

    service = build("gmail", "v1", credentials=creds)

    try:
        results = service.users().labels().list(userId="me").execute()
        labels = results.get("labels", [])

        if args.json:
            print(json.dumps(labels, indent=2))
        else:
            print("# Gmail Labels\n")
            for label in sorted(labels, key=lambda x: x["name"]):
                print(f"- {label['name']} (`{label['id']}`)")

    except HttpError as e:
        print(f"Gmail API error: {e}")
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description="Gmail Search Skill")
    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # Setup command
    setup_parser = subparsers.add_parser("setup", help="Check setup status")
    setup_parser.add_argument("--json", action="store_true", help="Output as JSON")

    # Auth command
    auth_parser = subparsers.add_parser("auth", help="Authenticate with Gmail")

    # Scope command
    scope_parser = subparsers.add_parser("scope", help="View or change API scope")
    scope_parser.add_argument("--set", choices=list(SCOPES_MAP.keys()), help="Set new scope")

    # Search command
    search_parser = subparsers.add_parser("search", help="Search emails")
    search_parser.add_argument("query", nargs="?", default="", help="Search query (Gmail syntax)")
    search_parser.add_argument("--from", dest="from_addr", help="Filter by sender")
    search_parser.add_argument("--to", dest="to_addr", help="Filter by recipient")
    search_parser.add_argument("--subject", help="Filter by subject")
    search_parser.add_argument("--label", help="Filter by label")
    search_parser.add_argument("--after", help="Messages after date (YYYY/MM/DD)")
    search_parser.add_argument("--before", help="Messages before date (YYYY/MM/DD)")
    search_parser.add_argument("--has-attachment", action="store_true", help="Has attachments")
    search_parser.add_argument("--unread", action="store_true", help="Only unread")
    search_parser.add_argument("--starred", action="store_true", help="Only starred")
    search_parser.add_argument("--limit", type=int, default=20, help="Max results (default: 20)")
    search_parser.add_argument("--full", action="store_true", help="Include full body")
    search_parser.add_argument("--attachments", action="store_true", help="Include attachment info")
    search_parser.add_argument("--json", action="store_true", help="Output as JSON")

    # Download command
    download_parser = subparsers.add_parser("download", help="Download attachments")
    download_parser.add_argument("message_id", help="Message ID")
    download_parser.add_argument("--output", "-o", help="Output directory")
    download_parser.add_argument("--json", action="store_true", help="Output as JSON")

    # Labels command
    labels_parser = subparsers.add_parser("labels", help="List labels")
    labels_parser.add_argument("--json", action="store_true", help="Output as JSON")

    args = parser.parse_args()

    if args.command == "setup":
        cmd_setup(args)
    elif args.command == "auth":
        cmd_auth(args)
    elif args.command == "scope":
        cmd_scope(args)
    elif args.command == "search":
        cmd_search(args)
    elif args.command == "download":
        cmd_download(args)
    elif args.command == "labels":
        cmd_labels(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
