# Doctor G -- Implementation Instructions

## Invocation

```
/doctorg [--deep|--full] [--no-personal] <question>
```

Parse the argument to extract:
- `depth`: "quick" (default), "deep" (--deep), or "full" (--full)
- `personal`: true (default), false (--no-personal)
- `question`: everything after flags

## Step-by-Step Execution

### Step 1: Classify the Question

Determine question type to select source priorities:

**Pattern matching**:
- Contains supplement/vitamin/mineral names -> `nutrition_supplements`
- Contains exercise/training/workout/lifting -> `exercise_training`
- Contains sleep/insomnia/circadian -> `sleep`
- Contains heart/cardio/blood pressure -> `cardiovascular`
- Contains cancer/tumor/oncology -> `oncology`
- Contains diabetes/insulin/glucose/blood sugar -> `diabetes`
- Contains anxiety/depression/mental/therapy -> `mental_health`
- Contains drug/medication/prescription -> `medication`
- Contains weight/fat loss/body comp/BMI -> `body_composition`
- Contains "vs" or "versus" or "compared to" -> `expert_comparison` (add flag)
- Default -> `general_wellness`

**Expert comparison detection**:
If question contains "vs", "versus", or names two known health figures (Huberman, Attia, Rhonda Patrick, Greger, etc.), set `is_comparison = true`.

### Step 2: Build Search Queries

For each depth level, construct search queries.

**All levels -- base queries**:
```python
queries = [
    f"{question}",
    f"{question} systematic review OR meta-analysis",
]
```

**Deep -- additional queries**:
```python
queries += [
    f"{question} risks OR side effects OR limitations",
    f"{question} expert consensus OR position statement",
    f"{question} evidence strength",
]
```

**Full -- additional queries**:
```python
queries += [
    f"{question} retracted OR debunked OR criticism",
    f"{question} recent 2025 2026 update",
    f"{question} contrarian view OR counterargument",
]
```

### Step 3: Execute Searches

**Quick depth**:
1. `WebSearch(query=base_query, allowed_domains=[Tier1 + Tier2 + topic-specific Tier3])`
2. `WebSearch(query=systematic_review_query, allowed_domains=[Tier1])`

**Deep depth** (run searches in parallel where possible):
1. All Quick searches
2. `WebSearch(query=risks_query, allowed_domains=[Tier1 + Tier2])`
3. `WebSearch(query=expert_query, allowed_domains=[Tier2 + Tier3])`
4. Use `tavily-search` skill: `tavily-search "{question}" --include-domains {Tier1+Tier2+Tier3 comma-separated}`
5. If `is_comparison`: search each expert's name + topic separately

**Full depth**:
1. All Deep searches
2. `WebSearch(query=contrarian_query)` (no domain filter -- find opposing views)
3. `WebSearch(query=retraction_query, allowed_domains=[Tier1])`
4. Use `firecrawl-research` to extract full text from top 2-3 most relevant Tier 1 results
5. If comparison: `firecrawl-research` on each expert's primary source (podcast transcript, blog post, paper)

### Step 4: Pull Personal Health Context

**Skip if `--no-personal` flag set.**

Run relevant health queries based on topic:

```bash
# Always pull (baseline context)
python ~/ai_projects/claude-skills/health-data/scripts/health_query.py --format json vitals

# Topic-specific
# exercise/training:
python ~/ai_projects/claude-skills/health-data/scripts/health_query.py --format json workouts --days 30
python ~/ai_projects/claude-skills/health-data/scripts/health_query.py --format json activity --days 7

# sleep:
python ~/ai_projects/claude-skills/health-data/scripts/health_query.py --format json sleep --days 14

# body composition/nutrition:
python ~/ai_projects/claude-skills/health-data/scripts/health_query.py --format json weekly --weeks 4

# cardiovascular:
python ~/ai_projects/claude-skills/health-data/scripts/health_query.py --format json vitals
# + custom query for BP if available:
python ~/ai_projects/claude-skills/health-data/scripts/health_query.py --format json query "SELECT AVG(value), unit FROM health_records WHERE record_type LIKE '%BloodPressure%' AND start_date >= date('now', '-30 days')"
```

**Health context formatting**:
Extract only the relevant numbers. Don't dump raw JSON into the response.
Example: "Based on your recent data: resting HR 62 bpm, HRV 45ms, avg 9,200 steps/day, 4 strength workouts/week"

### Step 5: Synthesize Evidence

**Evidence grading rules**:
1. Start with study design level (see sources.md grading table)
2. Upgrade if: large effect size, dose-response, multiple independent replications
3. Downgrade if: industry funding without replication, small sample, high heterogeneity, indirect evidence
4. **Strong**: 2+ systematic reviews/meta-analyses agree, or 3+ large RCTs consistent
5. **Moderate**: 1 systematic review or 2+ well-designed studies, some limitations
6. **Weak**: Limited studies, small samples, or conflicting results
7. **Minimal**: Expert opinion only, animal studies, case reports
8. **Contested**: Credible evidence on both sides, active scientific debate

**For expert comparisons**:
1. State each expert's position clearly with their key claims
2. Find where they actually agree (usually more than expected)
3. Show what research supports/contradicts each position
4. Avoid declaring a "winner" -- let evidence speak

### Step 6: Format Output

Follow the template in SKILL.md exactly. Key formatting rules:

1. **Short answer first** -- 1-2 sentences, direct
2. **Evidence table** -- every major claim gets a strength rating
3. **Personal section** -- only if health data adds meaningful context
4. **Sources** -- list with tier label and year
5. **Disclaimer** -- always append

**Table formatting**:
```markdown
| Claim | Evidence Strength |
|-------|------------------|
| Creatine improves strength output | **Strong** |
| Creatine causes hair loss | **Weak** (single small study, not replicated) |
| 5g/day is optimal dose | **Strong** |
| Loading phase is necessary | **Weak** (not needed, just takes longer to saturate) |
```

**Personal section example**:
```markdown
## For You Specifically

Your recent data shows 4 strength sessions/week with avg resting HR of 62.
Given your training volume, 5g creatine monohydrate daily would be well-supported.
Your HRV of 45ms suggests good recovery capacity.

**One consideration**: Your sleep data shows avg 6.2h -- optimizing sleep to 7+ hours
would likely provide more performance benefit than any supplement.
```

### Error Handling

**Database not found** (health.db):
- Skip personal context section
- Note: "Personal health data unavailable -- using general recommendations"

**No relevant search results from Tier 1**:
- Expand to Tier 2-3
- Note: "Limited primary research found -- evidence grading reflects available sources"

**Question outside health domain**:
- Politely redirect: "This skill focuses on evidence-based health questions. For [topic], try [alternative]."

**Highly personalized medical question** (e.g., "should I take this medication"):
- Provide evidence but emphasize: "This specific decision requires your healthcare provider who knows your full history"

## Performance Notes

- Quick depth should return in <30s (2 WebSearch calls)
- Deep depth: ~60-90s (5-6 search calls + tavily)
- Full depth: ~2-3min (8+ searches + firecrawl)
- Health data queries: ~2-3s each (local SQLite)
- Parallelize independent search calls where possible
