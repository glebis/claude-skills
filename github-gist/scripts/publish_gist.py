#!/usr/bin/env python3
"""
Publish files as GitHub Gists.

Uses gh CLI by default (recommended), falls back to API if unavailable.
"""

import argparse
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path


def gh_available() -> bool:
    """Check if gh CLI is available and authenticated."""
    try:
        result = subprocess.run(
            ["gh", "auth", "status"],
            capture_output=True,
            text=True
        )
        return result.returncode == 0
    except FileNotFoundError:
        return False


def create_gist_gh(filepath: str, description: str, public: bool, filename: str = None) -> dict:
    """Create gist using gh CLI."""
    cmd = ["gh", "gist", "create", filepath]

    if description:
        cmd.extend(["--desc", description])

    if public:
        cmd.append("--public")

    if filename:
        cmd.extend(["--filename", filename])

    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        raise Exception(f"gh error: {result.stderr}")

    gist_url = result.stdout.strip()
    gist_id = gist_url.split("/")[-1]

    return {
        "url": gist_url,
        "id": gist_id,
        "public": public,
        "filename": filename or Path(filepath).name
    }


def create_gist_api(filename: str, content: str, description: str, public: bool, token: str) -> dict:
    """Create gist via GitHub API (fallback)."""
    try:
        import requests
    except ImportError:
        raise Exception("requests package required for API fallback. Install with: pip install requests")

    url = "https://api.github.com/gists"
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json",
    }
    data = {
        "description": description,
        "public": public,
        "files": {filename: {"content": content}}
    }

    response = requests.post(url, headers=headers, json=data)

    if response.status_code == 201:
        result = response.json()
        return {
            "url": result["html_url"],
            "raw_url": result["files"][filename]["raw_url"],
            "id": result["id"],
            "public": result["public"],
            "filename": filename
        }
    else:
        raise Exception(f"GitHub API error {response.status_code}: {response.text}")


def get_api_token():
    """Get GitHub token from environment."""
    return os.environ.get("GITHUB_GIST_TOKEN") or os.environ.get("GITHUB_TOKEN")


def main():
    parser = argparse.ArgumentParser(description="Publish files as GitHub Gists")
    parser.add_argument("file", help="File to publish (use '-' for stdin)")
    parser.add_argument("--public", action="store_true", help="Create public gist (default is secret/unlisted)")
    parser.add_argument("--description", "-d", help="Gist description")
    parser.add_argument("--filename", "-f", help="Override filename in gist")
    parser.add_argument("--url-only", action="store_true", help="Output only the URL")
    parser.add_argument("--open", action="store_true", help="Open in browser after creation")
    parser.add_argument("--api", action="store_true", help="Force API usage instead of gh CLI")

    args = parser.parse_args()

    use_gh = gh_available() and not args.api

    # Handle stdin
    if args.file == "-":
        content = sys.stdin.read()
        filename = args.filename or "gist.txt"

        if use_gh:
            # gh requires a file, so create temp file
            with tempfile.NamedTemporaryFile(mode="w", suffix=f"_{filename}", delete=False) as f:
                f.write(content)
                temp_path = f.name
            filepath = temp_path
        else:
            filepath = None
    else:
        path = Path(args.file).expanduser().resolve()
        if not path.exists():
            print(json.dumps({"error": f"File not found: {args.file}"}))
            sys.exit(1)
        filepath = str(path)
        filename = args.filename or path.name
        content = path.read_text()

    description = args.description or f"Published from {filename}"

    try:
        if use_gh:
            result = create_gist_gh(
                filepath=filepath,
                description=description,
                public=args.public,
                filename=args.filename
            )
            # Clean up temp file if created
            if args.file == "-":
                os.unlink(temp_path)
        else:
            token = get_api_token()
            if not token:
                print(json.dumps({
                    "error": "No authentication available",
                    "help": "Install gh CLI and run 'gh auth login', or set GITHUB_GIST_TOKEN"
                }))
                sys.exit(1)

            result = create_gist_api(
                filename=filename,
                content=content,
                description=description,
                public=args.public,
                token=token
            )

        if args.url_only:
            print(result["url"])
        else:
            print(json.dumps(result, indent=2))

        if args.open:
            if sys.platform == "darwin":
                subprocess.run(["open", result["url"]])
            elif sys.platform == "linux":
                subprocess.run(["xdg-open", result["url"]])
            elif sys.platform == "win32":
                subprocess.run(["start", result["url"]], shell=True)

    except Exception as e:
        print(json.dumps({"error": str(e)}))
        sys.exit(1)


if __name__ == "__main__":
    main()
