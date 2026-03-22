# Temple Data JSON Schema

The contract between the generation pipeline and the runtime renderer.

## Top-Level Structure

```json
{
  "version": 2,
  "mode": "single" | "merged",
  "config": { ... },
  "entities": { ... },
  "levels": [ ... ],
  "mappings": { ... },
  "secrets": [ ... ],
  "whispers": { ... },
  "fields": [ ... ],
  "confidence": { ... },
  "sources": [ ... ]          // only in merged mode
}
```

## Config

```json
{
  "config": {
    "title": "The Inner Temple",
    "intro": {
      "heading": "ENTER THE TEMPLE",
      "body": "A living map of [vault description]. Click to begin."
    },
    "palette": {
      "primary": "#e85d04",
      "accent": "#ffd60a",
      "bg": "#030108",
      "text": "#f8f8f2"
    },
    "layers": [
      {
        "name": "Surface",
        "y": 12, "h": 10,
        "color": "#e85d04", "opacity": 0.05,
        "whisperKey": "surface"
      }
    ],
    "voice": "first-person-casual" | "third-person-formal" | "mixed",
    "language": "en" | "ru" | "mixed"
  }
}
```

## Entities

Organized by type. Each entity has both canonical and poetic identities.

```json
{
  "entities": {
    "gods": [
      {
        "key": "drd2",
        "canonical": "DRD2 - Dopamine D2 Receptor",
        "poetic": "The Reward Gate",
        "type": "god",
        "desc": "Short poetic description (1-2 sentences)",
        "lore": "Longer mythological narrative (2-4 sentences)",
        "domain": "neurochemistry",
        "connects": ["comt", "dat1", "reward-deficiency"],
        "source": "single" | "a" | "b" | "shared",
        "vaultNote": "DRD2 - Dopamine D2 Receptor.md",
        "centrality": 0.89,
        "position": { "ring": 0, "angle": 0.0, "y": 10 }
      }
    ],
    "demigods": [ ... ],
    "tensions": [
      {
        "key": "building-vs-calm",
        "canonical": "Building vs Calm",
        "poetic": "Scaffolding ↔ Stillness",
        "type": "tension",
        "poles": [
          { "name": "The Architect's Drive", "entities": ["trail-lab", "motka"] },
          { "name": "The Monk's Silence", "entities": ["calm-life", "mindfulness"] }
        ],
        "desc": "The pull between productive creation and nervous system rest.",
        "connects": ["gad", "exercise"],
        "position": { "ring": 3, "angle": 1.2, "y": -2 }
      }
    ],
    "narratives": [ ... ],
    "blindSpots": [ ... ],
    "spirits": [ ... ],
    "crystals": [ ... ],
    "research": [ ... ],
    "values": [ ... ],
    "trails": [ ... ],
    "questions": [ ... ],
    "depths": [ ... ],
    "growth": []
  }
}
```

## Levels (Abstraction Hierarchy)

```json
{
  "levels": [
    {
      "id": 0,
      "name": "Entities",
      "zoomThreshold": 0,
      "description": "Individual knowledge nodes",
      "always": true
    },
    {
      "id": 1,
      "name": "Domains",
      "zoomThreshold": 80,
      "description": "Clusters of related entities",
      "confidence": 0.85,
      "clusters": [
        {
          "key": "neurochemistry",
          "canonical": "Neurochemistry",
          "poetic": "The Chemical Garden",
          "members": ["drd2", "comt", "fkbp5", "sertraline"],
          "exemplar": "drd2",
          "centroid": { "x": 5.2, "y": 8.1, "z": -3.4 },
          "color": [0.9, 0.4, 0.1],
          "desc": "The genetic and pharmacological machinery beneath mood and motivation."
        }
      ]
    },
    {
      "id": 2,
      "name": "Axes",
      "zoomThreshold": 200,
      "description": "Fundamental tensions and force fields",
      "confidence": 0.72,
      "axes": [
        {
          "key": "building-calm",
          "poleA": { "name": "Building", "domains": ["neurochemistry", "tech"], "position": { "x": -20, "y": 0, "z": 0 } },
          "poleB": { "name": "Calm", "domains": ["embodied", "therapy"], "position": { "x": 20, "y": 0, "z": 0 } },
          "desc": "The vault's central tension: productive creation vs. nervous system rest."
        }
      ]
    },
    {
      "id": 3,
      "name": "Comparison",
      "zoomThreshold": 500,
      "description": "Two-vault overlap and divergence",
      "confidence": 0.65,
      "overlap": {
        "score": 0.34,
        "sharedEntities": 18,
        "sharedDomains": 3,
        "sharedAxes": 1
      }
    }
  ]
}
```

## Mappings (Cross-Level Crosswalks)

```json
{
  "mappings": {
    "entityToDomain": {
      "drd2": "neurochemistry",
      "skateboarding": "embodied-practice"
    },
    "domainToAxis": {
      "neurochemistry": { "axis": "building-calm", "pole": "A", "weight": 0.7 },
      "embodied-practice": { "axis": "building-calm", "pole": "B", "weight": 0.8 }
    }
  }
}
```

## Secrets

```json
{
  "secrets": [
    {
      "trigger": ["drd2", "skateboarding"],
      "insight": "The same receptor that makes rewards feel faint also makes vestibular stimulation therapeutic.",
      "status": "hidden"
    }
  ]
}
```

## Whispers (Per-Layer Ambient Text)

```json
{
  "whispers": {
    "surface": ["The genome speaks in probabilities", "Every receptor is a door half-open"],
    "middle": ["Tension is not a problem to solve", "The body remembers what the mind forgets"],
    "deep": ["What you avoid shapes you more than what you pursue"]
  }
}
```

## Fields (Atmospheric Zones)

```json
{
  "fields": [
    {
      "key": "avoidance-field",
      "name": "The Avoidance Field",
      "center": [0, -5, 0],
      "radius": 15,
      "color": [0.3, 0.1, 0.4],
      "desc": "Where blind spots and safety behaviours cluster."
    }
  ]
}
```

## Confidence

```json
{
  "confidence": {
    "overall": 0.78,
    "perLevel": { "0": 1.0, "1": 0.85, "2": 0.72 },
    "lowConfidenceEntities": ["crystal-3", "narrative-7"],
    "notes": "Level 2 axes are interpretive — vault has few explicit opposing pairs."
  }
}
```

## Merged Mode Additional Fields

When `mode: "merged"`:

```json
{
  "sources": [
    { "name": "Gleb's Vault", "color": "#4ecdc4", "entityCount": 142 },
    { "name": "Partner Vault", "color": "#ff6b6b", "entityCount": 89 }
  ]
}
```

Each entity gains `"source": "a" | "b" | "shared"` and optionally `"sourceA_key"` / `"sourceB_key"` for semantic matches.
