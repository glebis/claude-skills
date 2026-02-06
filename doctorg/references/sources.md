# Evidence Source Registry

Tiered domains for WebSearch `allowed_domains` parameter and Tavily `include_domains`.

## Tier 1 -- Primary Research & Systematic Reviews

Highest evidence weight. Peer-reviewed, systematic.

### Databases & Aggregators
| Domain | Description |
|--------|-------------|
| `ncbi.nlm.nih.gov` | PubMed + PubMed Central (full-text) |
| `cochranelibrary.com` | Gold standard systematic reviews |
| `who.int` | WHO guidelines and position papers |
| `clinicaltrials.gov` | Clinical trial registry |
| `europepmc.org` | 41M+ life science publications, free API |
| `epistemonikos.org` | 300K+ systematic reviews aggregated |
| `medrxiv.org` | Health sciences preprints (flag as preprint) |
| `bioRxiv.org` | Biology preprints (flag as preprint) |

### WebSearch Domain List (copy-paste for Tier 1)
```
ncbi.nlm.nih.gov, cochranelibrary.com, who.int, clinicaltrials.gov, europepmc.org, epistemonikos.org
```

## Tier 2 -- Clinical & Institutional

High evidence weight. Expert institutions, clinical guidelines.

### General Medical
| Domain | Description |
|--------|-------------|
| `mayoclinic.org` | Evidence-based patient information |
| `hopkinsmedicine.org` | Johns Hopkins clinical guidance |
| `clevelandclinic.org` | Cleveland Clinic health library |
| `health.harvard.edu` | Harvard Health Publishing |
| `medlineplus.gov` | NIH consumer health information |
| `nhlbi.nih.gov` | National Heart, Lung, Blood Institute |
| `cdc.gov` | CDC guidelines and MMWR |
| `nih.gov` | NIH (general) |
| `nice.org.uk` | UK clinical guidelines (NICE CKS) |

### Condition-Specific Organizations
| Domain | Description | Topics |
|--------|-------------|--------|
| `americanheart.org` | American Heart Association | Cardiovascular |
| `cancer.org` | American Cancer Society | Oncology |
| `cancer.gov` | NCI (National Cancer Institute) | Oncology |
| `cancercare.org` | CancerCare | Oncology support |
| `diabetes.org` | American Diabetes Association | Diabetes |
| `ndep.nih.gov` | NIH Diabetes Education Program | Diabetes |
| `joslin.harvard.edu` | Joslin Diabetes Center | Diabetes |
| `alz.org` | Alzheimer's Association | Neurology |
| `alzinfo.org` | Alzheimer's Information | Neurology |
| `tchin.org` | Congenital Heart Info Network | Cardiology |
| `nimh.nih.gov` | National Institute of Mental Health | Mental health |

### Regulatory
| Domain | Description |
|--------|-------------|
| `fda.gov` | US FDA (drug safety, approvals) |
| `ema.europa.eu` | European Medicines Agency |
| `open.fda.gov` | openFDA API (adverse events, labels) |

### WebSearch Domain List (copy-paste for Tier 2)
```
mayoclinic.org, hopkinsmedicine.org, clevelandclinic.org, health.harvard.edu, medlineplus.gov, nhlbi.nih.gov, cdc.gov, nih.gov, nice.org.uk, americanheart.org, cancer.org, cancer.gov, diabetes.org, alz.org, fda.gov, ema.europa.eu, nimh.nih.gov
```

## Tier 3 -- Expert Analysis & Evidence Synthesis

Medium weight. Curated expert analysis, evidence-based summaries.

| Domain | Description | Best For |
|--------|-------------|----------|
| `examine.com` | Evidence-based supplement/nutrition analysis | Supplements, nutrition |
| `statnews.com` | STAT News - medical/pharma journalism | Drug development, policy |
| `healthnewsreview.org` | Health News Review - media watchdog | Claim verification |
| `healthfeedback.org` | Scientists fact-check health claims | Viral claim debunking |
| `consumerlab.com` | Independent supplement testing | Supplement quality |
| `nutritionfacts.org` | Dr. Greger's evidence reviews | Plant-based nutrition |
| `acsm.org` | American College of Sports Medicine | Exercise science |
| `nsca.com` | National Strength & Conditioning | Training protocols |
| `sleepfoundation.org` | National Sleep Foundation | Sleep science |
| `nasm.org` | National Academy of Sports Medicine | Exercise science |

### AI-Powered Research (use as supplementary)
| Domain | Description |
|--------|-------------|
| `consensus.app` | AI consensus extraction from papers |
| `scholar.google.com` | Academic search (broad) |

### WebSearch Domain List (copy-paste for Tier 3)
```
examine.com, statnews.com, healthnewsreview.org, healthfeedback.org, acsm.org, nsca.com, sleepfoundation.org, consensus.app
```

## Tier 4 -- Quality Journalism

Lowest evidence weight. Use for context, framing, public discourse. Never cite as primary evidence.

| Domain | Description |
|--------|-------------|
| `theatlantic.com` | The Atlantic |
| `nytimes.com` | New York Times |
| `npr.org` | NPR |
| `theguardian.com` | The Guardian |
| `fivethirtyeight.com` | FiveThirtyEight (data journalism) |
| `mosaicscience.com` | Mosaic Science |
| `wired.com` | Wired (science/tech health) |
| `vox.com` | Vox (explainers) |

### WebSearch Domain List (copy-paste for Tier 4)
```
theatlantic.com, nytimes.com, npr.org, theguardian.com, fivethirtyeight.com
```

## Topic-Specific Source Priority

When the question is about a specific topic, prioritize these sources:

| Topic | Priority Sources |
|-------|-----------------|
| **Supplements/Nutrition** | examine.com, PubMed, FDA, consumerlab.com |
| **Exercise/Training** | PubMed, ACSM, NSCA, Mayo Clinic |
| **Sleep** | PubMed, sleepfoundation.org, Mayo Clinic, Harvard Health |
| **Heart/Cardiovascular** | AHA, NHLBI, PubMed, Cleveland Clinic |
| **Cancer** | NCI, ACS, Cochrane, PubMed |
| **Diabetes** | ADA, Joslin, NDEP, PubMed |
| **Mental Health** | NIMH, APA, PubMed, Mayo Clinic |
| **Medications** | FDA, EMA, PubMed, Cochrane |
| **Weight/Body Comp** | PubMed, examine.com, Harvard Health |
| **Longevity/Aging** | PubMed, NIA (nia.nih.gov), Harvard Health |

## Evidence Grading Quick Reference

| Source Type | Starting GRADE Level | Notes |
|-------------|---------------------|-------|
| Cochrane systematic review | High | Gold standard |
| PubMed meta-analysis | High | Check heterogeneity |
| Large RCT (>500 participants) | High | Check funding/bias |
| Small RCT (<100) | Moderate | Underpowered risk |
| Observational/cohort | Low-Moderate | Confounding risk |
| Expert opinion/guidelines | Moderate | Based on evidence synthesis |
| examine.com summary | Moderate | Well-referenced but secondary |
| Case report/series | Low | Anecdotal |
| Animal/in-vitro study | Very Low | Not directly applicable |
| Preprint (not peer-reviewed) | Very Low | Flag prominently |
| News article | N/A | Never grade as evidence |

## Red Flags to Watch For

When evaluating sources, flag these:
- **Industry-funded studies** without independent replication
- **Retracted papers** (check Retraction Watch)
- **Predatory journals** (check DOAJ for journal quality)
- **Supplements with proprietary blends** (can't verify doses)
- **N=1 or case report** presented as generalizable
- **Animal studies** presented as human-applicable
- **Relative risk** without absolute risk context
- **Correlation** presented as causation
