# Elimination Research Dataset Schema

The generator accepts a JSON object. The example file is `assets/examples/consumer_goods_dataset.example.json`.

## Top-Level Fields

| Field | Type | Required | Notes |
|---|---:|---:|---|
| `title` | string | yes | Report title |
| `question` | string | recommended | Decision task shown in reports |
| `market` | string | recommended | Purchase market/country |
| `currency` | string | recommended | Currency label, e.g. `EUR` |
| `created_at` | string | optional | ISO timestamp for research observation |
| `source_policy` | string | recommended | One-paragraph source policy/scope |
| `constraints` | object | optional | Price ceiling and hard limits |
| `criteria` | array | optional | Display labels for criteria table |
| `candidates` | array | yes | Candidate option rows |
| `sources` | array | recommended | Source/evidence rows |
| `domain_registry` | array/object | optional | Source domain policy |
| `tournament` | array | optional | Explicit tournament rows |
| `open_caveats` | array | recommended | Known evidence gaps |
| `image_search` | object | optional | Cached image-search results |

## Constraints

```json
{
  "constraints": {
    "max_device_price_eur": 200,
    "price_limit_basis": "device_price_eur"
  }
}
```

Use `device_price_eur` as the hard budget ceiling unless the user explicitly says total cost of ownership is the hard limit.

## Criteria

The default scorer expects these metric keys:

```json
[
  {
    "id": "effectiveness",
    "label": "Effectiveness proxy",
    "coefficient": 0.4488,
    "unit": "0-100",
    "direction": "higher is better",
    "definition": "Primary product-performance proxy."
  },
  {
    "id": "skin_safety",
    "label": "Fit / safety",
    "coefficient": 0.236,
    "unit": "0-100",
    "direction": "higher is better",
    "definition": "User-fit, safety, comfort, or risk proxy."
  },
  {
    "id": "convenience",
    "label": "Convenience",
    "coefficient": 0.3568,
    "unit": "0-100",
    "direction": "higher is better",
    "definition": "Maintenance, setup, portability, battery, or bundle convenience."
  },
  {
    "id": "three_year_cost_eur",
    "label": "Three-year cost penalty",
    "coefficient": -0.00584,
    "unit": "EUR",
    "direction": "lower is better",
    "definition": "Device price plus replaceable-part allowance."
  }
]
```

Keep candidate `metrics` keys aligned with the scorer.

## Candidate Row

Required:

```json
{
  "id": "stable_candidate_id",
  "name": "Product Name",
  "metrics": {
    "effectiveness": 88,
    "skin_safety": 86,
    "convenience": 88
  },
  "three_year_cost_eur": 240.97
}
```

Recommended for consumer goods:

```json
{
  "brand": "Brand",
  "category": "electric shaver",
  "type": "foil",
  "device_price_eur": 193.99,
  "replacement_head_eur": 46.98,
  "replacement_unit_price_eur": 46.98,
  "replacement_quantity_3y": 1,
  "replacement_interval_months": 18,
  "replacement_part_name": "head cassette",
  "ownership_note": "",
  "runtime_min": 60,
  "charging_min": 60,
  "cleaning_station": true,
  "wet_dry": true,
  "source_refs": ["src_price", "src_specs", "src_parts"],
  "item_links": [
    {
      "label": "Price",
      "url": "https://example.com/product",
      "title": "Price reference",
      "role": "price"
    }
  ],
  "image_query": "Product Name product photo",
  "preferred_image_hosts": ["brand.example", "retailer.example"],
  "image_exclude_terms": ["review", "manual", "pdf", "logo"]
}
```

If `three_year_cost_eur` is missing, the CLI computes:

```text
device_price_eur + replacement_head_eur
```

If `replacement_head_eur` is missing but unit price and quantity are present, the CLI computes:

```text
replacement_unit_price_eur * replacement_quantity_3y
```

## Source Row

```json
{
  "id": "src_price",
  "title": "Price aggregator product page",
  "url": "https://example.com/product",
  "domain": "example.com",
  "role": "price_specs",
  "metrics": {
    "device_price_eur": 193.99
  },
  "notes": "Observed offer price."
}
```

Keep source roles specific:

- `official_specs`
- `price`
- `price_specs`
- `replacement_price`
- `replacement_interval`
- `expert_review`
- `forum`
- `performance_proxy`

## Domain Registry Row

```json
{
  "domain": "example.com",
  "source_type": "price_aggregator",
  "trust_tier": "high",
  "allowed_roles": ["price", "price_specs"],
  "blocked_roles": ["performance_claim"],
  "human_approval_status": "approved",
  "confidence": 0.9
}
```

Use the domain registry to separate source reliability from the data itself.

## Tournament Row

```json
{
  "round": "Final",
  "a": "Option A",
  "b": "Option B",
  "winner": "Option A",
  "reason": "Higher balanced score under the current criteria."
}
```

If omitted, the CLI generates simple comparisons from the ranking.
