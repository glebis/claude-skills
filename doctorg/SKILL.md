---
name: doctorg
description: Evidence-based health research using tiered trusted sources with GRADE-inspired evidence ratings. Integrates Apple Health data for personalized context. Use when user asks health, nutrition, exercise, sleep, or wellness questions.
---

# Doctor G -- Evidence-Based Health Research

Answer health and wellness questions using only trusted, evidence-based sources with explicit evidence strength ratings.

## Usage

```bash
# Quick answer (WebSearch only, ~30s)
/doctorg Is creatine safe for daily use?

# Deep research (WebSearch + Tavily, ~90s)
/doctorg --deep Huberman vs Attia on fasted training

# Full investigation (WebSearch + Tavily + Firecrawl, ~3min)
/doctorg --full What does current evidence say about GLP-1 agonists for non-diabetic weight loss?

# Without personal health context
/doctorg --no-personal Best stretching protocol for lower back pain
```

## Depth Levels

| Level | Flag | Tools | Time | Use When |
|-------|------|-------|------|----------|
| Quick | *(default)* | WebSearch | ~30s | Simple factual questions |
| Deep | `--deep` | WebSearch + Tavily | ~90s | Competing claims, nuanced topics |
| Full | `--full` | WebSearch + Tavily + Firecrawl | ~3min | Controversial topics, need primary sources |

## How It Works

### 1. Parse Query & Detect Topic Category

Classify the question into one of:
- **Nutrition/Supplements** (examine.com gets priority)
- **Exercise/Training** (PubMed + ACSM get priority)
- **Sleep** (focus sleep-specific databases)
- **Disease/Condition** (condition-specific orgs + clinical guidelines)
- **Medication/Treatment** (FDA, EMA, Cochrane get priority)
- **Mental Health** (APA, mental health orgs)
- **General Wellness** (broad search across all tiers)

### 2. Search Evidence Sources (Tiered)

Search sources in priority order. See `references/sources.md` for complete domain list.

**Tier 1 -- Primary Research** (highest weight):
- PubMed/PMC, Cochrane Library, WHO, ClinicalTrials.gov

**Tier 2 -- Clinical/Institutional** (high weight):
- Mayo Clinic, Hopkins Medicine, Cleveland Clinic, Harvard Health
- Condition-specific: AHA, ACS, ADA, Alzheimer's Association

**Tier 3 -- Expert Analysis** (medium weight):
- Examine.com, STAT News, Health News Review
- Consensus.app, Epistemonikos

**Tier 4 -- Quality Journalism** (context/framing):
- The Atlantic, NYT, NPR, Guardian, FiveThirtyEight

#### Search Strategy by Depth

**Quick** (default):
```
WebSearch(query, allowed_domains=[Tier 1 + Tier 2 domains])
WebSearch(query + "systematic review OR meta-analysis", allowed_domains=[Tier 1])
```

**Deep** (--deep):
All Quick searches PLUS:
```
tavily-search(query, include_domains=[Tier 1-3])
WebSearch(query + "expert opinion OR position statement", allowed_domains=[Tier 2-3])
WebSearch(query + "risks OR side effects OR contraindications")
```

**Full** (--full):
All Deep searches PLUS:
```
firecrawl-research for top 2-3 most relevant results from Tier 1
WebSearch for competing/contrarian viewpoints
WebSearch(query + "retracted OR debunked OR misleading")
```

### 3. Pull Personal Health Context (unless --no-personal)

Query Apple Health database for relevant metrics:

```bash
python ~/ai_projects/claude-skills/health-data/scripts/health_query.py --format json vitals
python ~/ai_projects/claude-skills/health-data/scripts/health_query.py --format json daily
python ~/ai_projects/claude-skills/health-data/scripts/health_query.py --format json sleep --days 7
python ~/ai_projects/claude-skills/health-data/scripts/health_query.py --format json workouts --days 30
```

Select ONLY metrics relevant to the query:
- Exercise question -> recent workouts, activity, resting HR, VO2 max
- Sleep question -> sleep data, HRV
- Nutrition question -> weight trends, activity level
- Heart question -> HR, HRV, resting HR, blood pressure

### 4. Synthesize with Evidence Grading

Rate each claim using simplified GRADE scale:

| Rating | Meaning | Based On |
|--------|---------|----------|
| **Strong** | Consistent evidence from systematic reviews/meta-analyses or multiple large RCTs | Level I-II evidence |
| **Moderate** | Supported by well-designed studies but some inconsistency or limitations | Level II-III evidence |
| **Weak** | Limited evidence, small studies, or conflicting results | Level III-IV evidence |
| **Minimal** | Expert opinion, case reports, or preliminary/animal studies only | Level V evidence |
| **Contested** | Active scientific debate with credible evidence on both sides | Mixed levels |

### 5. Format Output

```markdown
# [Topic Title]

**Short answer**: [1-2 sentence direct answer]

## [Expert/Position A] (if comparing viewpoints)
- Key claim 1
- Key claim 2
- Has **evolved stance**: [if applicable]

## [Expert/Position B]
- Key claim 1
- Key claim 2

## Where They Actually Agree (if comparing)
- Agreement point 1
- Agreement point 2

## What Research Shows

| Claim | Evidence Strength |
|-------|------------------|
| Claim 1 | **Strong** |
| Claim 2 | **Weak** (reason) |
| Claim 3 | **Contested** |

## For You Specifically (if --personal context available)

[Personalized interpretation based on user's health data]

[Specific actionable recommendation]

## Sources
- [Source 1 title](url) -- Tier, year
- [Source 2 title](url) -- Tier, year

## Limitations
- [Any caveats about the evidence or this analysis]
```

**Output rules**:
- NEVER give medical diagnoses or replace professional advice
- ALWAYS include disclaimer: "This is research synthesis, not medical advice"
- When evidence is **Weak** or **Minimal**, explicitly say so
- When claims are **Contested**, present both sides fairly
- Prefer recent sources (last 5 years) over older ones
- Flag if key studies have been retracted or challenged
- Include the "For You Specifically" section only when health data adds meaningful context

### 6. Disclaimer (always append)

```
---
*Research synthesis, not medical advice. Consult a healthcare provider for personal decisions.*
```

## Examples

### Quick
```
/doctorg Is 10000 steps a day backed by science?
```

### Deep (comparing experts)
```
/doctorg --deep Huberman vs Attia on fasted training
```

### Full (controversial topic)
```
/doctorg --full Safety profile of long-term melatonin supplementation
```

## Integration with Other Skills

- **health-data**: Pulls Apple Health metrics for personalization
- **tavily-search**: Deep research at Tier 1-3 sources
- **firecrawl-research**: Full-text extraction from primary sources
- **fact-checker**: Can be chained for verification of specific claims
