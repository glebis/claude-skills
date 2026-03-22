# Dual-Graph Merge Algorithm

How to build a common map between two vaults.

## Overview

The merged temple uses a **shared scaffold with divergence offsets** (not split-hemisphere, not pure overlay).

- Shared domains/axes occupy canonical center positions
- Vault A entities appear as color-coded satellites biased left
- Vault B entities appear as color-coded satellites biased right
- Overlap entities sit at center, scaled larger
- Divergence leans outward

## Merge Pipeline

### 1. Independent Classification

Run the full classification pipeline (Steps 1-4 of SKILL.md) for each vault independently. This produces two scene packages with their own entities, levels, and mappings.

### 2. Entity Matching

Three match types:

**Exact match**: Same canonical key exists in both vaults (e.g., both have `anxiety-management`).
- Confidence: 1.0
- These become shared entities immediately.

**Semantic match**: Different keys, same concept. Claude identifies these by reading entity descriptions and connections.
- Example: Vault A has `stress-response`, Vault B has `cortisol-regulation`
- Confidence: 0.5-0.9 (Claude assigns based on semantic overlap)
- Present matches to user for confirmation before generating the merged temple.

**Unique**: Only exists in one vault.
- Source: `"a"` or `"b"`
- These become divergence entities.

### 3. Domain Alignment

After entity matching, align Level 1 domains:

1. For each domain in Vault A, count how many of its members have matches in Vault B
2. If > 50% members match, find the Vault B domain with the most matched members → these are **aligned domains**
3. Aligned domains merge into a single shared domain with members from both vaults
4. Unaligned domains remain vault-specific

### 4. Axis Reconciliation (Level 2)

Compare tension axes across vaults:
- If both vaults have a tension with matching poles → shared axis
- If poles partially overlap → note the divergence in axis description
- If entirely different axes → vault-specific axes

### 5. Layout Generation

**Shared entities**: Position at the canonical center. Scale 1.2x normal. Dual-glow effect (both vault colors).

**Vault A unique**: Offset by -8 on X axis from their natural ring position. Tinted with Vault A color.

**Vault B unique**: Offset by +8 on X axis. Tinted with Vault B color.

**Connections**:
- Within-vault connections: colored by vault (A = blue tint, B = green tint)
- Cross-vault connections (through shared entities): gold/amber

### 6. Merged Scene Package

Additional fields in `temple-data.json`:

```json
{
  "mode": "merged",
  "sources": [
    { "name": "Vault A Name", "color": "#4ecdc4", "entityCount": 45 },
    { "name": "Vault B Name", "color": "#ff6b6b", "entityCount": 62 }
  ],
  "overlap": {
    "score": 0.34,
    "sharedEntities": 18,
    "sharedDomains": 3,
    "sharedAxes": 1
  },
  "entities": [
    { "key": "...", "source": "shared", "sourceA_key": "...", "sourceB_key": "...", ... },
    { "key": "...", "source": "a", ... },
    { "key": "...", "source": "b", ... }
  ]
}
```

### 7. Template Behavior in Merged Mode

The template detects `mode: "merged"` and activates:
- Split-color rendering (left/right have different ambient tones)
- Toggle button: All / Vault A only / Vault B only / Shared only
- Shared nodes get dual-glow effect
- HUD displays overlap score
- Audio: stereo/dialogic treatment — Vault A motifs in left channel, Vault B in right, shared entities in center

## Confidence Thresholds

- **Don't generate Level 3** if overlap score < 0.1 (vaults have almost nothing in common)
- **Flag low-confidence matches** (< 0.6) for user review
- **Minimum shared entities**: 5 — below this, merged view adds noise not insight

## User Confirmation

Before generating the merged temple, present to the user:
1. List of exact matches (auto-approved)
2. List of semantic matches with confidence scores (needs approval)
3. Proposed domain alignments
4. Overall overlap score

Only proceed after user confirms the match list.
