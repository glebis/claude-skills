# Elimination Research Workflow

## 1. Intake

Ask intake questions before collecting data. Prefer a popup/question tool such as `cenno` when available. Each question should have closed choices plus a free-text comment field.

Required intake:

| Question | Closed choices |
|---|---|
| What matters most? | overall quality, lowest price, sensitive-skin/user-fit, low maintenance, travel/portability |
| What is the hard limit? | budget ceiling, must-have features, excluded brands, purchase country |
| How much evidence is needed? | quick consumer view, full audit report, both |
| Which source types are allowed? | manufacturer, retailer, price aggregator, expert review, forum, all with flags |

Do not include these intake questions as a visible report section. Use them to shape the dataset, criteria, and source policy.

## 2. Research

Collect evidence into structured fields instead of prose blobs:

- Candidate name, brand, model, category, purchase market, and shortlist rationale.
- Current purchase price, currency, date observed, and source URL.
- Key technical parameters relevant to the category.
- Replaceable/consumable parts, rough price, estimated replacement interval, and quantity over the ownership horizon.
- 1-3 item links per candidate for purchase or additional info.
- Source rows with URL, domain, role, metrics contributed, and notes.
- Domain registry rows with source type, trust tier, allowed roles, and review flags.
- Product images or image-search cache.

Use official APIs and clean deterministic data sources when possible. Use page scraping only when allowed by the user and project rules. For articles, use Firecrawl when the project policy requires it.

## 3. Scoring

Default scoring uses three 0-100 quality proxies plus a three-year cost penalty:

- `effectiveness`
- `skin_safety` as the generic fit/safety/user-risk proxy
- `convenience`
- `three_year_cost_eur`

Rename display labels in the dataset `criteria` section when the domain uses different language. Keep the metric keys unless also updating the scorer.

Cost of ownership should be easy to understand:

```
three_year_cost_eur = device_price_eur + replacement_unit_price_eur * replacement_quantity_3y
```

Use caveats when replacement cadence is approximate. For goods with consumables or replaceable heads/filters/blades/bags/cartridges, include price and replacement interval directly in the quick report.

## 4. Report Generation

Run:

```bash
python3 scripts/generate_elimination_report.py \
  --dataset path/to/dataset.json \
  --output-dir path/to/outputs
```

Use `--max-price-eur` for a hard purchase-price ceiling. Use `--price-limit-basis three_year_cost_eur` only when the user explicitly wants total cost of ownership as the hard limit.

Use `--refresh-images` only when Google Custom Search credentials are available via environment variables or SOPS-encrypted dotenv.

## 5. Verification

Check both report modes:

- Quick report: images visible, ownership visible, table switch works, prices rounded, no source-debug text visible.
- Full report: task and criteria visible, all numeric data in tables, raw data embedded, caveats preserved.
- Browser: mobile and desktop layout, no incoherent overlap, no horizontal page overflow except intentional table scroll wrappers.
- JSON: `final_report.json` and `raw_research_data.json` parse cleanly.

## 6. Handoff

Tell the user:

- Which option won overall and which option won value.
- Where the quick and full reports are.
- What evidence gaps remain.
- Whether image refresh or ownership estimates relied on cached/approximate assumptions.
