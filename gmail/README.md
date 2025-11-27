# Gmail Search Skill

Search and fetch emails via Gmail API with flexible query options and output formats.

## Features

- Free-text search with Gmail query syntax
- Filter by sender, recipient, subject, label, date range
- Status filters: unread, starred, has-attachment
- Download attachments from messages
- List all labels
- Configurable OAuth scopes (readonly/modify/full)
- Output as Markdown (default) or JSON

## Installation

```bash
pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib
```

## Setup: Obtaining Gmail API Credentials

### 1. Create Google Cloud Project

1. Go to [console.cloud.google.com](https://console.cloud.google.com)
2. Click project dropdown (top bar) -> "New Project"
3. Name it (e.g., "Gmail Agent Skill") -> Create
4. Wait for project creation, then select it

### 2. Enable Gmail API

1. In your project, go to "APIs & Services" -> "Library"
2. Search for "Gmail API"
3. Click on it and press "Enable"

### 3. Configure OAuth Consent Screen

1. Go to "APIs & Services" -> "OAuth consent screen"
2. Choose "External" user type -> Create
3. Fill in required fields:
   - **App name:** Gmail Agent Skill
   - **User support email:** your email
   - **Developer contact email:** your email
4. Click "Save and Continue"
5. Skip "Scopes" (just click "Save and Continue")
6. On "Test users" page, click "Add Users"
7. Add your Gmail address as a test user
8. Click "Save and Continue" -> "Back to Dashboard"

### 4. Create OAuth Credentials

1. Go to "APIs & Services" -> "Credentials"
2. Click "Create Credentials" -> "OAuth client ID"
3. Application type: **Desktop app**
4. Name: "Gmail Agent Client"
5. Click "Create"

### 5. Download and Save Credentials

After creation, you'll see Client ID and Client Secret.

**Option A: Download JSON**
1. Click the download icon next to your OAuth client
2. Save as `~/.gmail_credentials/credentials.json`

**Option B: Create manually**

Create `~/.gmail_credentials/credentials.json`:

```json
{
  "installed": {
    "client_id": "YOUR_CLIENT_ID.apps.googleusercontent.com",
    "client_secret": "YOUR_CLIENT_SECRET",
    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
    "token_uri": "https://oauth2.googleapis.com/token",
    "redirect_uris": ["http://localhost"]
  }
}
```

### 6. Authenticate

```bash
python3 scripts/gmail_search.py auth
```

This opens a browser. Sign in with Google, approve access, and you're ready.

## Usage

```bash
# Check setup status
python3 scripts/gmail_search.py setup

# Search emails
python3 scripts/gmail_search.py search "meeting notes"

# Filter by sender
python3 scripts/gmail_search.py search --from "boss@company.com"

# Unread emails with attachments
python3 scripts/gmail_search.py search --unread --has-attachment

# Date range
python3 scripts/gmail_search.py search --after 2024/11/01 --before 2024/11/30

# Full body (not just snippet)
python3 scripts/gmail_search.py search "invoice" --full

# JSON output
python3 scripts/gmail_search.py search "project" --json

# Download attachments
python3 scripts/gmail_search.py download MESSAGE_ID

# List labels
python3 scripts/gmail_search.py labels
```

## Scopes

Change permission level:

```bash
python3 scripts/gmail_search.py scope --set readonly   # Read only (default)
python3 scripts/gmail_search.py scope --set modify     # Read + modify labels
python3 scripts/gmail_search.py scope --set full       # Full access
```

## Files

- `~/.gmail_credentials/credentials.json` - OAuth client credentials
- `~/.gmail_credentials/token.pickle` - Cached auth token
- `~/.gmail_credentials/scope.txt` - Current scope setting
