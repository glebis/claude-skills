# Health Integration Reference

> Optional enrichment layer. The cognitive toolkit works fully without any health data.

---

## Apple Health (via Health MCP)

### Prerequisites
- Health MCP server running on mac-mini
- MCP tools: `mcp__health__*` available in the session

### Available Tools

| Tool | Data |
|------|------|
| `mcp__health__latest_vitals` | HRV, resting HR, blood pressure |
| `mcp__health__daily_summary` | Steps, active/resting calories |
| `mcp__health__sleep_analysis` | Sleep duration, stages, efficiency |
| `mcp__health__activity_rings` | Move, exercise, stand ring progress |

### HRV Tracking Protocol

At session start:
```
call mcp__health__latest_vitals
→ extract HRV value
→ store as hrv_pre in session frontmatter
```

At session end:
```
call mcp__health__latest_vitals
→ extract HRV value
→ store as hrv_post
→ calculate hrv_delta = hrv_post - hrv_pre
→ log in session notes
```

### Mindful Minutes

Query via `mcp__health__health_query` with category `mindful_minutes`.

- Track cumulative daily practice
- Surface streaks (consecutive days with sessions)
- Include in session close summary if streak is notable

---

## Aurora Ring

### Prerequisites
- Aurora Ring data accessible via Health MCP or dedicated integration (TBD)

### Data Points

| Metric | Range | Notes |
|--------|-------|-------|
| Readiness score | 0–100 | Composite recovery indicator |
| HRV | continuous | Higher resolution than Apple Health |
| Skin temperature delta | °C delta | Deviation from personal baseline |
| Sleep staging | light/deep/REM/awake | Nightly breakdown |

### Session Context Rules

- **Low readiness (< 60)** → suggest gentler session; prioritise grounding and somatic work over deep cognitive challenge
- **Medium readiness (60–80)** → standard session, no adjustment needed
- **High readiness (> 80)** → good time for deeper work; cognitive restructuring, schema exploration, intensive thought records

---

## Genome Vault

### Prerequisites
- Vault at `~/Brains/genome/` with gene notes
- Gene files follow the vault's standard structure

### Relevant Variants

| Gene / Variant | Research signal | Cognitive toolkit implication |
|----------------|-----------------|-------------------------------|
| COMT Val/Val | Faster catecholamine clearance | TIPP and exercise interventions may act faster; shorter warm-up needed |
| SLC6A4 Short/Short | Lower serotonin reuptake efficiency | More patience in evidence-gathering steps; avoid rushing conclusions |
| BDNF Val/Val | Strong neuroplasticity response | Techniques may consolidate faster; spaced practice especially effective |
| FKBP5 risk alleles | Prolonged cortisol after stressors | Include grounding / breathing before cognitive work |
| OPRM1 A;G | Altered reward processing | Behavioural activation scheduling may need different calibration for reinforcement value |

### Language Requirement

**CRITICAL: Never deterministic.**

Use: *"Research suggests your variant may..."*  
Never: *"Your genes mean you should..."*

All genetic context is probabilistic population-level research, not individual prescription.

### How to Pull Genome Context

1. Check if `~/Brains/genome/` exists — skip silently if not
2. Read relevant gene notes (COMT, SLC6A4, BDNF, FKBP5, OPRM1)
3. Include findings as soft context in session recommendations
4. Store in session frontmatter as:

```yaml
genetic_context:
  comt: Val/Val
  slc6a4: S/S
  bdnf: Val/Val
  fkbp5: risk
  oprm1: A/G
```

---

## Failure Modes

| Situation | Behaviour |
|-----------|-----------|
| Health MCP unreachable | Skip silently, proceed without health data |
| No genome vault at `~/Brains/genome/` | Skip silently |
| Partial health data (some metrics missing) | Use what's available, omit missing fields |
| HRV unavailable at session end | Log `hrv_post: null`, skip delta calculation |

**NEVER invent or estimate health values.** If a value is unavailable, omit it entirely — do not substitute averages, guesses, or placeholders.
