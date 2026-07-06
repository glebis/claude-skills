---
name: elimination-research
description: This skill should be used for elimination-style research where the user wants to choose from a shortlist of products, tools, services, vendors, or other options using explicit criteria, numeric evidence, tournament-style comparison, source/domain classification, image-supported consumer reports, raw data tables, and ownership-cost estimates for replaceable parts. Use this skill whenever the user asks to compare options, buy something, shortlist candidates, rank alternatives, generate a "don't make me think" report, or produce a full audit report with raw numeric data.
---

# Elimination Research

## Purpose

Generate a reproducible elimination-research package: a shortlist dataset, numeric scoring model, quick consumer report, full audit report, raw data JSON, source/domain audit, purchase/info links, contextual images, and ownership-cost estimates.

Use this skill to turn fuzzy "which one should I choose?" requests into a clean decision workflow with explicit criteria and inspectable data.

## Workflow

Follow this sequence for new comparisons:

1. Read `references/workflow.md` for the full operating procedure.
2. Ask the intake questions before researching. Prefer `cenno` popup questions when available. Use closed choices and include a free-text comment field.
3. Gather candidate, source, price, spec, replacement-part, image, and evidence data.
4. Save all collected data into a dataset JSON matching `references/dataset-schema.md`.
5. Run `scripts/generate_elimination_report.py` to generate reports.
6. Verify the quick report and full report in a browser.
7. Preserve raw data and numeric tables; do not hide or discard evidence just because the quick report is simplified.

## Intake Questions

Ask these at the start of a new comparison, not inside the final report:

- What matters most: overall quality, lowest price, sensitive-skin/user-fit, low maintenance, or travel/portability?
- What is the hard limit: budget ceiling, must-have features, excluded brands, or purchase country?
- How much evidence is needed: quick consumer view, full audit report, or both?
- Which source types are allowed: manufacturer, retailer, price aggregator, expert review, forum, or all with flags?

Always include a comment field for constraints that do not fit the closed choices.

## Output Contract

Produce these files in the chosen output directory:

- `quick_report.html` — consumer-facing "don't make me think" report with cards/table switch, images in context, rounded prices, links, and visible ownership summaries.
- `report.html` — full audit report with task, criteria, scoring, raw numeric data, source/domain tables, tournament, and embedded JSON.
- `report.md` — markdown version of the full audit report.
- `final_report.json` — normalized report payload.
- `raw_research_data.json` — collected dataset before rendering.
- `image_search_results.json` — cached Google image-search output when image refresh is used.

The quick report should keep numeric detail behind expandable evidence links, but the full report must expose all numeric data as tables.

## Generator

Run the bundled generator from the skill directory:

```bash
python3 scripts/generate_elimination_report.py \
  --dataset assets/examples/consumer_goods_dataset.example.json \
  --output-dir /tmp/elimination-report \
  --max-price-eur 200
```

Common options:

```bash
--dataset PATH             Structured shortlist dataset JSON
--output-dir PATH          Output directory
--max-price-eur NUMBER     Purchase-price ceiling override
--price-limit-basis FIELD  Usually device_price_eur or three_year_cost_eur
--question TEXT            Override report task question
--market TEXT              Purchase market/country
--currency TEXT            Currency label
--domain-registry PATH     Optional domain registry JSON
--refresh-images           Refresh Google Custom Search image data
--image-results NUMBER     Image results per candidate when refreshing
```

For Google Images, load keys only from environment variables or SOPS-encrypted dotenv files. Never commit plaintext keys. The image helper checks `GOOGLE_CUSTOM_SEARCH_JSON_API_KEY`, `GOOGLE_CUSTOM_SEARCH_API_KEY`, `GOOGLE_CUSTOM_SEARCH_CX`, and `GOOGLE_IMAGE_SEARCH_ENV_FILE`.

## Data Rules

Read `references/dataset-schema.md` before creating or editing the dataset.

Key requirements:

- Use stable candidate IDs.
- Keep every numeric observation as a number, not prose.
- Store prices in explicit currency fields such as `device_price_eur`.
- For replaceable parts, include rough `replacement_unit_price_eur`, `replacement_quantity_3y`, `replacement_interval_months`, and `replacement_part_name`.
- Include `item_links` or source references so each item has 1-3 purchase/info links.
- Classify source domains by role and trust tier. Manufacturer/spec, retailer, price aggregator, expert review, forum, and affiliate sources should remain distinct.
- Store caveats explicitly. Do not silently remove weak assumptions.

## Report Design Rules

For consumer reports:

- Let product images illustrate the options in context; do not create a standalone image-source section.
- Keep image blocks on a light neutral background.
- Hide image host/score/dimensions from the consumer report; keep them in JSON.
- Round visible prices in the quick report.
- Avoid eyebrow labels.
- Provide a card/table switch where cards and table are mutually exclusive views.
- Show ownership cost directly on each option card/table row when replaceable parts exist.
- Keep source links as short action chips: price, official, review, parts, or head price.

For audit reports:

- Start with the task and criteria so the report is understandable without conversation context.
- Show all numeric data as tables.
- Include the full candidate dataset, domain/source audit, score formula, tournament rows, sensitivity rankings, and caveats.

## Verification

Before handing off:

- Run the generator on the dataset.
- Validate JSON with `python3 -m json.tool`.
- Open `quick_report.html` and verify the card/table switch replaces the options view rather than stacking table below cards.
- Check mobile width for text overflow, low contrast, and touch targets under 44px.
- Confirm `report.html` includes raw numeric columns for device price, replacement allowance, part unit price, interval, quantity, and three-year cost.
- Commit and push changes when editing the skills repo or generated report project.
