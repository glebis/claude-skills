# Entity Classification Guide

How to map arbitrary vault content into temple entity types. The framework is universal; the content is domain-specific.

## Classification Principles

1. **Algorithm discovers, AI names.** Use centrality metrics and cluster analysis to identify candidates. Then read the actual notes to decide what they mean.
2. **Two vocabularies.** Every entity gets a `canonical` label (neutral, portable) and a `poetic` label (mythic, evocative). The canonical name is for debugging; the poetic name is for the temple.
3. **Semantic, not structural.** A note's entity type comes from its *role in the knowledge system*, not its filename or folder. A note called "README" could be a god if everything links to it.

## Entity Type Heuristics

### Gods (3-7)
**What they are:** The foundational concepts the vault orbits around. Remove one and the graph fragments.
**Detection:** Highest degree centrality. Most backlinks. Often appear in frontmatter tags of many other notes. May have their own MoC or hub note.
**Examples across domains:**
- Pharmacogenomics vault: DRD2, FKBP5, Sertraline
- Cooking vault: Fermentation, Heat, Fat
- Software vault: Architecture, Testing, Deployment
- Philosophy vault: Consciousness, Ethics, Language

**Naming:** Gods get imposing names. "The Serotonin Gate", "The Ferment Throne", "The Test Oracle."

### Demigods (5-15)
**What they are:** High-importance concepts that serve the gods. Specific mechanisms, techniques, or frameworks.
**Detection:** High centrality but fewer cross-domain links than gods. Often connected to 1-2 gods strongly.
**Examples:** COMT (serves neurochem god), Maillard Reaction (serves Heat god), CI/CD (serves Deployment god).
**Naming:** Less imposing than gods but still mythic. "The Methylation Courier", "The Browning Ritual."

### Tensions (3-9)
**What they are:** Pairs of concepts that pull in opposite directions. The vault's unresolved dialectics.
**Detection:** Look for:
- Notes that mention both sides of a trade-off
- Clusters that rarely link to each other despite being near in centrality
- Explicit "vs" or "or" patterns in titles/content
- Contradictions between notes (one says X is good, another says X is harmful)
**Examples:** Building ↔ Calm, Tradition ↔ Innovation, Speed ↔ Quality, Solo ↔ Connection
**Naming:** Use the ↔ symbol. Both poles get names. "The Architect's Restlessness ↔ The Monk's Silence."

### Narratives (5-12)
**What they are:** Stories the vault tells about itself. Recurring themes across multiple notes. Self-referential patterns.
**Detection:** Look for:
- Phrases/metaphors that appear across 3+ unrelated notes
- Self-referential observations ("I always...", "the pattern is...")
- Historical accounts that inform current thinking
- Cluster themes that span domains
**Examples:** "Hardware vs Willpower" (genetics as destiny), "The French Training" (formative experience shaping taste), "The Partnership Breakup" (trust injury shaping decisions)
**Naming:** Quote-like or story-like. "The Story of the Slow Receptor."

### Blind Spots (3-7)
**What they are:** Things the vault talks ABOUT but doesn't ACT on. Contradictions between stated values and actual practice. Absent presences.
**Detection:** Look for:
- Notes with many outgoing links but few backlinks (written about, not integrated)
- Goals/values that appear in planning notes but never in action notes
- Topics the vault circles around but never directly addresses
- Advice given to others that isn't followed personally
**Examples:** "Teaching as Avoidance of Building", "Never tries baking" (in a cooking vault), "Writes about testing but has no tests"
**Naming:** Honest and slightly uncomfortable. "The Unfollowed Advice."

### Spirits (3-5)
**What they are:** Recurring behavioral patterns that cross domain boundaries. Not a topic but a *mode* of operating.
**Detection:** Look for:
- Patterns visible across 3+ different contexts/folders
- Behavioral verbs that recur ("collecting", "planning", "demonstrating")
- Meta-observations about one's own process
**Examples:** "The Architect Demon" (over-planning), "The Recipe Collector" (gathering without doing), "The Demo Compulsion" (needing to show)
**Naming:** Personified. "The _____ Demon/Spirit/Ghost."

### Crystals (2-6)
**What they are:** Beliefs or assumptions stated as facts. High resistance to change. Often foundational but potentially limiting.
**Detection:** Declarative statements that underpin multiple notes. Assumptions that go unquestioned. Core identity claims.
**Examples:** "The Partnership Breakup" (solidified trauma-story), "Authentic only if handmade", "I'm not a real developer"
**Naming:** Mineral/gem metaphors or declarative quotes. "The Handmade Crystal."

### Research (10-30)
**What they are:** Domain concepts that are referenced and explored but not central organizing principles.
**Detection:** Medium centrality. Well-linked within their cluster but not cross-domain. Often have source citations.
**Examples:** Affordance, Polyvagal Theory, Koji, Tempering, Middleware pattern
**Naming:** Keep closer to canonical names but add one evocative modifier. "The Polyvagal Bridge", "The Koji Bloom."

### Values (3-10)
**What they are:** Prescriptive notes — rules, protocols, operating principles. Things the vault says "do this" about.
**Detection:** Imperative language. Protocol/checklist format. Often referenced in daily notes.
**Examples:** "Move First", "Season Early", "Test Before Ship", "Breathe Before Respond"
**Naming:** Imperative voice. Keep short and commanding.

### Trails (3-10)
**What they are:** Active projects, ongoing threads, journeys in progress.
**Detection:** Notes with dates, progress markers, status fields. Often in a Trails/ or Projects/ folder. Have temporal dimension.
**Examples:** "Claude Code Lab", "Sourdough Journey", "Migration to Rust"
**Naming:** Journey metaphors. "The Lab Trail", "The Sourdough Path."

### Questions (5-12)
**What they are:** Open questions the vault hasn't answered. Edges of knowledge.
**Detection:** Notes ending in `?`. Tags like `#open-question`. Notes with links to many topics but no conclusion. Empty or stub notes on important topics.
**Examples:** "Who is Gleb without Claude?", "Can I make real ramen?", "What comes after microservices?"
**Naming:** Keep as questions. May shorten or sharpen.

### Depths (5-15)
**What they are:** Notes that connect surface concepts to deeper patterns. The "why beneath the what."
**Detection:** Notes that reference psychology, identity, meaning, motivation. Notes that explain *why* a pattern exists, not just *what* it is.
**Examples:** IFS parts, shadow work, food memories, "why I code"
**Naming:** Depth metaphors. "The Root Beneath the Root."

### Whispers (5-6, one per layer)
**What they are:** Ambient text displayed at different depth levels. Sets the mood for each vertical layer.
**Detection:** Not derived from notes. Written by Claude to capture the layer's feeling.
**Format:** Array of short phrases. Example: `["The genome speaks in probabilities", "Every receptor is a door half-open"]`

### Secrets (10-20)
**What they are:** Non-obvious connections between two entities that reward discovery.
**Detection:** Surprising links between entities in different domains/types. Counter-intuitive relationships.
**Format:** `{trigger: ['key1', 'key2'], insight: 'Why this connection matters', status: 'hidden'}`

### Fields (3-5)
**What they are:** Atmospheric zones that group related entities spatially. Visual clusters with ambient effects.
**Detection:** Derived from Level 1 domains. Each field covers a spatial region of the temple.
**Format:** `{key, name, center: [x,y,z], radius, color: [r,g,b], desc}`

## Classification Workflow

1. Sort nodes by degree centrality (descending)
2. Assign top 3-7 as god candidates → read their content to confirm
3. Next tier (up to ~15) as demigod candidates → confirm by reading
4. Scan for opposing pairs in high-centrality nodes → tensions
5. Look for cross-domain recurring patterns → spirits, narratives
6. Check for stated-but-not-practiced patterns → blind spots
7. Read cluster themes → domains (Level 1)
8. Fill remaining types from scan data
9. Write whispers and secrets last (these require understanding the whole)

## Voice Calibration

Before writing any poetic names or descriptions:
1. Read 5 representative notes from the vault
2. Note: language (English/Russian/mixed?), tone (academic/casual/poetic?), person (first/third?), jargon level
3. Match temple text to this voice. A casual vault gets casual temple text. A formal vault gets formal text.
