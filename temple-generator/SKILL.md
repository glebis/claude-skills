---
name: temple-generator
description: Generate a 3D interactive knowledge map (Inner Temple) from any Obsidian vault or document set. Supports multi-scale abstraction layers and dual-graph common maps between two vaults.
trigger: /temple-generate
args: vault_path [--compare vault_path_2] [--output path] [--inline]
user_invocable: true
---

# Temple Generator

Generate a 3D interactive knowledge visualization from any Obsidian vault. The output is a single HTML file (Three.js) with concentric entity rings, audio, discovery mechanics, and multi-scale semantic zoom.

## When to Use

- User wants to visualize any Obsidian vault as a 3D knowledge map
- User wants to compare two vaults/document sets visually
- User wants to regenerate the temple from scratch with fresh vault analysis

## Architecture

Two-part system:
1. **Generation pipeline** (this skill): discovers structure, names it, scores confidence, exports a scene package
2. **Runtime renderer** (template): handles navigation, transitions, audio, discovery

Pre-generate meaning. Runtime-render experience.

## Workflow

### Step 1: Scan the Vault

Run `python3 ~/.claude/skills/temple-generator/scripts/extract_entities.py <vault_path>`.

This produces `vault-scan.json` with:
- Files: path, title, tags, outgoing links, backlink counts, word count, folder, frontmatter
- Graph: adjacency list with bidirectional link counts
- Centrality: degree centrality per node
- Clusters: detected groups of tightly linked notes

### Step 2: Read the Scan + Sample Notes

1. Read `vault-scan.json`
2. Read the top ~20 nodes by centrality (first 100 lines each)
3. Read `references/classification-guide.md` for entity type heuristics
4. Read 3-5 representative notes to calibrate the vault's "voice" (formal/informal, domain jargon, language)

### Step 3: Classify Entities

Using `references/classification-guide.md`, assign each significant node to an entity type. Maintain two vocabularies:

- **canonical**: neutral labels for portability (`anxiety-management`, `fermentation-process`)
- **poetic**: mythic/art labels for the installation (`The Ferment Gate`, `The Cortisol Throne`)

Target counts per type (adjust for vault size):

| Type | Small vault (< 100) | Medium (100-500) | Large (500+) |
|------|---------------------|-------------------|--------------|
| Gods | 2-3 | 3-5 | 5-7 |
| Demigods | 3-7 | 5-12 | 8-15 |
| Tensions | 2-4 | 3-7 | 5-9 |
| Narratives | 2-5 | 5-10 | 8-12 |
| Blind spots | 1-3 | 3-5 | 4-7 |
| Spirits | 1-3 | 3-5 | 3-5 |
| Research | 5-15 | 10-25 | 15-30 |
| Values | 2-5 | 3-8 | 5-10 |
| Trails | 2-5 | 3-8 | 5-10 |
| Questions | 3-6 | 5-10 | 8-12 |
| Depths | 2-5 | 5-10 | 8-15 |
| Crystals | 1-3 | 2-5 | 3-6 |

### Step 4: Build Abstraction Levels

Levels are **confidence-gated** — only include a level if the vault supports it.

**Level 0 — Entities** (always exists): individual nodes with positions, connections, descriptions.

**Level 1 — Domains** (requires >= 3 meaningful clusters): groups of related entities. Each domain has:
- `canonical` + `poetic` name
- member entity keys
- centroid position (weighted average of member positions)
- representative exemplar (most central member)
- description (1-2 sentences in vault voice)
- confidence score (0-1)

**Level 2 — Axes** (requires >= 2 interpretable opposing pairs): fundamental tensions. Each axis has:
- two poles with names and descriptions
- member domains per pole
- axis description
- confidence score

**Level 3 — Comparison** (requires two vaults + sufficient alignment): shared/unique analysis.

Read `references/merge-algorithm.md` for dual-graph logic.

### Step 5: Generate Scene Package

Follow the schema in `references/entity-schema.md` to produce `temple-data.json`.

Include:
- `entities`: all classified nodes
- `levels`: abstraction layers with zoom thresholds
- `mappings`: entity → domain → axis crosswalks
- `comparison`: (if dual-graph) shared/unique/alignment data
- `audio`: motif hints per type and level
- `style`: poetic vocabulary, intro text, color palette, layer definitions
- `confidence`: per-abstraction and per-alignment scores

### Step 6: Generate HTML

1. Copy `~/.claude/skills/temple-generator/assets/temple-template.html` to the output location
2. If `--inline` flag: embed the JSON data as `const TEMPLE_DATA = {...};` inside the HTML
3. Otherwise: place `temple-data.json` alongside the HTML

### Step 7: Report

Show the user:
- Entity counts by type
- Abstraction levels generated (with confidence scores)
- Top 5 gods/central entities
- Detected tensions
- If dual-graph: overlap percentage and shared domains

## Dual-Graph Mode

When `--compare vault_path_2` is provided:

1. Scan both vaults independently (Step 1)
2. Classify entities for each vault (Steps 2-3)
3. Run merge algorithm from `references/merge-algorithm.md`
4. Generate merged scene package with source attribution
5. Template renders shared scaffold with divergence offsets

## Quality Guidelines

- Skip trivial notes (daily todos, admin logs, empty stubs)
- Prefer nodes that reveal the vault's actual concerns, not its filing system
- Write in the vault's own voice, calibrated from sample notes
- If a level lacks confidence, omit it rather than fabricating structure
- Each abstraction level must be backed by membership weights, exemplars, and provenance
- "The abstraction hierarchy should be semantic, not just geometric"

## Audio Guidance for Template

The template's audio system should respect hierarchical continuity across zoom levels:
- L0 (close): localized, identity-rich — entity whispers and textures
- L1 (medium): regional harmonic beds, cluster pulses
- L2 (far): sparse drones, tension-based tonal movement
- L3 (comparison): stereo/dialogic between two vault voices

Zoom should feel like changing resolution, not changing universes. Motifs relate across scales.
