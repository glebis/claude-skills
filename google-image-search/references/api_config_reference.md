# JSON Config Reference

This document describes the JSON configuration format for batch image searches.

## Config Structure

The config file is a JSON array of entry objects:

```json
[
  { /* entry 1 */ },
  { /* entry 2 */ },
  ...
]
```

## Entry Fields

### Required Fields

| Field | Type | Description |
|-------|------|-------------|
| `query` | string | The Google search query |

### Recommended Fields

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `id` | string | auto | Unique identifier, used for filenames |
| `heading` | string | query | Display heading in output |
| `description` | string | - | Context about what image to find |
| `numResults` | int | 5 | Number of results to fetch (1-10) |

### Selection Fields

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `selectionCriteria` | string | - | What makes a good image for this topic |
| `selectionCount` | int | 2 | How many top candidates to consider for LLM selection |

### Scoring Fields

| Field | Type | Description |
|-------|------|-------------|
| `requiredTerms` | string[] | Terms that MUST appear in title/URL (missing = -80 score) |
| `optionalTerms` | string[] | Bonus terms that improve score (+5 each) |
| `excludeTerms` | string[] | Terms to penalize (-50 each) |
| `preferredHosts` | string[] | Trusted domains (+25 if match) |

### API Fields

| Field | Type | Description |
|-------|------|-------------|
| `imgType` | string | Image type: clipart, face, lineart, stock, photo, animated |
| `rights` | string | License filter: cc_publicdomain, cc_attribute, cc_sharealike, cc_noncommercial, cc_nonderived |
| `safe` | string | SafeSearch: active, moderate, off (default: active) |
| `fileType` | string | File type filter: jpg, gif, png, bmp, svg, webp, ico, raw |
| `siteSearch` | string | Restrict to specific site |

## Example Config

```json
[
  {
    "id": "alterego-device",
    "heading": "AlterEgo Silent Speech Interface",
    "description": "Wearable device for silent speech recognition using sEMG signals",
    "query": "AlterEgo MIT silent speech interface wearable",
    "numResults": 5,
    "selectionCriteria": "Real photo of device being worn, not concept art",
    "selectionCount": 3,
    "requiredTerms": ["AlterEgo"],
    "optionalTerms": ["MIT", "wearable", "speech"],
    "excludeTerms": ["stock", "illustration", "concept"],
    "preferredHosts": ["mit.edu", "media.mit.edu"],
    "safe": "active"
  },
  {
    "id": "semg-electrodes",
    "heading": "Surface EMG Electrodes",
    "description": "Medical-grade surface electrodes for muscle signal detection",
    "query": "surface EMG electrodes medical grade",
    "numResults": 5,
    "selectionCriteria": "Clear photo showing electrode placement on skin",
    "requiredTerms": ["electrode"],
    "optionalTerms": ["EMG", "surface", "medical"],
    "excludeTerms": ["clipart", "diagram"]
  }
]
```

## Scoring Algorithm

Each image is scored based on config criteria:

```
Base score: 0

Required terms:
  All present: +30
  Any missing: -80

Optional terms:
  +5 per match

Exclude terms:
  -50 per match

Preferred hosts:
  Match: +25
  No match: -5

MIME type:
  JPEG/PNG: +5
  GIF: -10

Resolution:
  >= 600x400: +10
  < 300x300: -10

File size:
  < 20KB: -5
```

## LLM Selection

After scoring, top `selectionCount` candidates are sent to LLM with:
- Title
- URL
- Host
- Score
- Scoring reasons
- Selection criteria

LLM returns JSON:
```json
{
  "chosen_index": 1,
  "explanation": "Best shows actual device in use"
}
```

## Environment Variables

Required in `.env` or environment:

```
Google-Custom-Search-JSON-API-KEY=AIza...
Google-Custom-Search-CX=327...
OPENROUTER_API_KEY=sk-or-...
```

Alternative key names also supported:
- `GOOGLE_CUSTOM_SEARCH_API_KEY`
- `GOOGLE_CUSTOM_SEARCH_CX`
- `OPENROUTER-API-KEY`
