# Data format

A project folder holds the research and one file, `catalogue.json`, that tells the page what the collection is. Records join on a stable `id` (lowercase, underscores); keep ids across runs so favourites and links survive.

| File | Required | Holds |
| --- | --- | --- |
| `catalogue.json` | yes | Page title, nouns, facets, card rows, table columns, detail fields, optional `date` / `cost` blocks, copy overrides |
| `items.json` | yes | Array of researched records, any fields, each with `id` |
| `items-meta.json` | no | Object keyed by id; compact display fields merged into each record |
| `snapshot.json` | yes | `{"date": "YYYY-MM-DD", "label": "21 November 2026", ...}` — the last research run, not the build date |
| `profile.json` | no | `{"criteria": [...]}` shown under the selection-criteria disclosure |
| `assets/manifest.json` | no | Image records (below); its presence turns images on |
| `template.html` | no | Overrides the skill template for this project |

Legacy names `calls.json` and `catalog-meta.json` are still read.

## Text in records

- Unknown facts are `—`.
- Inline links: `[label](https://…)`; only https links render.
- In `profile.json` criteria and `dek`: `**bold**`, `{snapshot}`, and any ISO date key from `snapshot.json` as `{key}` (formatted as a long date). `{minDeadline}` aliases `{minimumDeadline}`.

## catalogue.json

```json
{
  "language": "en",
  "locale": "en-GB",
  "pageTitle": "Espresso Grinders",
  "title": {"lead": "Home", "accent": "Espresso grinders"},
  "dek": "Seven grinders compared on price, burrs and noise. Researched {snapshot}.",
  "description": "Meta description.",
  "noun": {"one": "grinder", "many": "grinders"},
  "storageKey": "espresso-grinders",
  "fields": {"name": "name", "short": "short", "subtitle": "place", "url": "url", "sources": "extra"},
  "images": false,
  "date": {},
  "cost": {},
  "facets": [],
  "sorts": [],
  "defaultSort": "cost",
  "search": ["name", "place", "burr"],
  "card": [],
  "table": [],
  "detail": {"subtitle": [], "lead": [], "fields": []},
  "strings": {}
}
```

`fields` maps the roles the page needs to record fields; the defaults are shown. `short` falls back to `name`. `storageKey` namespaces favourites and theme in the browser — keep it stable.

### date (optional)

```json
{"field": "date", "label": "Deadline", "note": "timeNote",
 "detail": {"label": "Submission deadline", "field": "deadline"},
 "countdown": true, "soonDays": 30, "timeline": true}
```

`field` holds `YYYY-MM-DD` (or is empty). `note` is a short line under the date. `detail.field` is the full researched text shown in the dialog. Turn off `countdown` for dates that are not deadlines (release dates, fixed events), and `timeline` when the axis would mislead.

### cost (optional)

```json
{"field": "euro", "currency": "EUR", "label": "Entry fee", "sortLabel": "Fee",
 "note": "price", "tableNote": "feeNote", "approxIf": ["US$", "£"],
 "freeFilter": "No entry fee",
 "detail": [{"label": "Fees & packages", "field": "fee"},
            {"label": "Selected package for comparison", "field": "price", "withCost": true}]}
```

`field` is a number in `currency` (`0` = free, `null` = unknown). `note` names what that number refers to in original terms; if it contains any `approxIf` string, the price shows with `≈`. `freeFilter` adds a toggle for zero-cost items.

### facets

```json
{"key": "region", "field": "group", "label": "Region", "all": "All regions",
 "values": ["Nordics", "Mediterranean"], "other": "Other countries", "counts": true}
{"key": "genre", "field": "genres", "label": "Genre",
 "options": [["portrait", "Portrait"], ["art", "Art"]]}
{"key": "burr", "label": "Burrs", "counts": true}
```

`field` (default `key`) may hold a string or a list. Options come from `options` (`[value, label]` pairs), else `values` (+ `other`, which also catches anything unlisted), else every value found in the data. `key` becomes the URL parameter and must not be `sort`, `direction`, `view`, `q`, `free`, `favorites` or `call`.

### sorts (optional)

`[{"key": "noise", "label": "Quietest first", "field": "noiseDb"}]` — extra sort orders. Date, cost (when present) and name are built in. Missing values sort last in both directions.

### Field specs: card, table, detail

A field spec is `{"label": "…", "field": "…", "as": "…"}`. Renderers:

| `as` | Shows |
| --- | --- |
| *(none)* | Escaped text; lists join with · |
| `md` | Text with https links |
| `join` | List joined with ·; with `"facet"`, uses that facet's labels |
| `tags` | List as mono tags; with `"facet"`, uses its labels |
| `dashNote` | Value starting with — shows the dash, then the rest on its own line |
| `link` | A https value as a link (`linkLabel` optional) |
| `strong` | Bold line (table only) |
| `note` | Small muted line, hidden when empty (table only) |

- `card`: list of specs, each a row; `sub` names a second field shown smaller under the value.
- `table`: list of columns `{"label": "…", "show": [spec, …]}` after the name column and the date/cost column.
- `detail.subtitle`: fields joined under the dialog title (facet keys allowed).
- `detail.lead`: extra boxes beside the image, after the date/cost boxes.
- `detail.fields`: the two-column body.

### strings

Overrides for interface copy. Keys and English defaults are in `scripts/build.py` (`DEFAULT_STRINGS`). Common ones: `nameColumn`, `searchPlaceholder`, `details`, `detailsShort`, `researched`, `criteria`, `byDate`, `byCost`, `emptyEdition`, `source`, `next`, `allPast`, `rangeOne`, `rangeMany`, `skip`. Placeholders: `{n}`, `{total}`, `{noun}`, `{date}`, `{from}`, `{to}`.

## assets/manifest.json (array)

| Field | Meaning |
| --- | --- |
| `id` | Record id |
| `type` | What the image is: "2026 winner", "Poster", "Product photo" |
| `caption`, `credit` | Full caption and credit |
| `short_credit` | Name shown on the card; omit when unknown |
| `source_url` | Page the image comes from |
| `local_path` | Original file, relative to the project |
| `mime` | MIME type of the original |
| `image_url` | Remote fallback when no local file exists |

`assets/previews/<id>.webp` is preferred over `local_path` when present.
