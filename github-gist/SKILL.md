---
name: github-gist
description: Publish files or Obsidian notes as GitHub Gists. Use when user wants to share code/notes publicly, create quick shareable snippets, or publish markdown to GitHub. Triggers include "publish as gist", "create gist", "share on github", "make a gist from this".
---

# GitHub Gist Publisher

Publish any file as a GitHub Gist for easy sharing.

## Prerequisites

Uses `gh` CLI by default. Ensure you're authenticated:

```bash
gh auth status
# If not authenticated: gh auth login
```

Fallback: Set `GITHUB_GIST_TOKEN` env var with gist scope.

## Usage

```bash
# Publish file as secret (unlisted) gist - DEFAULT
python3 scripts/publish_gist.py /path/to/file.md

# Publish as public gist (visible in your profile)
python3 scripts/publish_gist.py /path/to/file.md --public

# Custom description
python3 scripts/publish_gist.py /path/to/file.md -d "My awesome note"

# Override filename in gist
python3 scripts/publish_gist.py /path/to/file.md -f "readme.md"

# From stdin
echo "Hello" | python3 scripts/publish_gist.py - -f "hello.txt"

# Just get URL
python3 scripts/publish_gist.py /path/to/file.md --url-only

# Create and open in browser
python3 scripts/publish_gist.py /path/to/file.md --open
```

## Options

| Flag | Description |
|------|-------------|
| `--public` | Create public gist (default is secret/unlisted) |
| `-d, --description` | Gist description |
| `-f, --filename` | Override filename |
| `--url-only` | Output only URL |
| `--open` | Open in browser |
| `--api` | Force API instead of gh CLI |

## Output

```json
{
  "url": "https://gist.github.com/user/abc123",
  "id": "abc123",
  "public": false,
  "filename": "file.md"
}
```

## Example

Session log published with this skill: https://gist.github.com/glebis/3faaae6b907123929220e81add51a567
