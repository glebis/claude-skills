# Data format

A project folder holds the research and one file, `catalogue.json`, that tells the page what the collection is. Records join on a stable `id` (lowercase, underscores); keep ids across runs so favourites and links survive.

| File | Required | Holds |
| --- | --- | --- |
| `catalogue.json` | yes | Page title, nouns, facets, card rows, table columns, detail fields, optional `date` / `measures` / `verification` blocks, copy overrides |
| `items.json` | yes | Array of researched records, any fields, each with `id` |
| `items-meta.json` | no | Object keyed by id; compact display fields merged into each record |
| `snapshot.json` | yes | `{"date": "YYYY-MM-DD", "label": "21 November 2026", ...}` — the last research run, not the build date |
| `profile.json` | no | `{"criteria": [...]}` shown under the selection-criteria disclosure |
| `assets/manifest.json` | no | Image records (below); its presence turns images on |
| `template.html` | no | Overrides the skill template for this project |

Legacy names `calls.json` and `catalog-meta.json` and the single `cost` block are still read.

## Text in records

- Unknown facts are `—` (text) or `null` (numbers and dates).
- Inline links: `[label](https://…)`; only https links render.
- In `profile.json` criteria and `dek`: `**bold**`, `{snapshot}`, and any ISO date key from `snapshot.json` as `{key}` (formatted as a long date). `{minDeadline}` aliases `{minimumDeadline}`.

## catalogue.json

```json
{
  "language": "en",
  "locale": "en-GB",
  "pageTitle": "Sleep and Memory Studies",
  "title": {"lead": "Sleep and", "accent": "memory studies"},
  "dek": "Six studies compared on design, sample and effect. Researched {snapshot}.",
  "description": "Meta description.",
  "noun": {"one": "study", "many": "studies"},
  "storageKey": "sleep-memory",
  "fields": {"name": "name", "short": "short", "subtitle": "authors", "url": "url", "sources": "extra"},
  "images": false,
  "date": {},
  "measures": [],
  "verification": {},
  "facets": [],
  "sorts": [],
  "defaultSort": "date",
  "search": ["name", "authors", "finding"],
  "card": [],
  "table": [],
  "detail": {"subtitle": [], "lead": [], "fields": []},
  "strings": {}
}
```

`fields` maps the roles the page needs to record fields; defaults are `name`, `short`, `place`, `url`, `extra`. `short` falls back to `name`. `storageKey` namespaces favourites and theme in the browser — keep it stable.

### date (optional)

```json
{"field": "date", "kind": "deadline", "label": "Deadline", "note": "timeNote",
 "detail": {"label": "Submission deadline", "field": "deadline"},
 "countdown": true, "soonDays": 30, "timeline": true}
```

`field` holds `YYYY-MM-DD` or is empty. `kind` sets wording and behaviour:

| `kind` | Marker | Timeline sentence | First sort |
| --- | --- | --- | --- |
| `deadline` (default) | "12 days left", "Closed"; urgent within `soonDays` | "Next to close: …" | soonest first |
| `event` | "In 12 days", "Tomorrow", "Past" | "Next up: …" | soonest first |
| `published` | "3 months ago" | "Most recent: …" | newest first |
| `other` | none | none (range only) | earliest first |

`label` defaults from the kind. `note` is a short line under the date; `detail.field` is the full researched text in the dialog. `countdown: false` hides the marker; `timeline: false` hides the timeline.

### measures (optional)

```json
[{"key": "cost", "field": "euro", "label": "Entry fee", "sortLabel": "Fee", "sortChip": "By price",
  "format": "currency", "currency": "EUR", "better": "low",
  "note": "price", "tableNote": "feeNote", "approxIf": ["US$", "£"],
  "zeroLabel": "Free", "zeroFilter": "No entry fee", "zeroKey": "free",
  "detail": [{"label": "Fees & packages", "field": "fee"},
             {"label": "Selected package", "field": "price", "withCost": true}]},
 {"key": "noise", "field": "noiseDb", "label": "Noise", "unit": "dB(A)", "decimals": 0,
  "better": "low", "sortChip": "Quietest first"}]
```

Each value is a number or `null`. Options:

| Option | Meaning |
| --- | --- |
| `format` | `number` (default), `integer`, `currency` (+ `currency`), `percent` (0.42 → 42 %), `year` |
| `unit`, `decimals` | Suffix and maximum decimals |
| `better` | `low` (default) or `high`; sets the first sort direction |
| `note`, `tableNote` | Fields shown under the value (what it refers to, caveats); `approxIf` strings in `note` add `≈` |
| `zeroLabel` | Text for 0 (currency defaults to "Free") |
| `zeroFilter`, `zeroKey` | Adds a toggle for items whose value is 0; `zeroKey` is its URL parameter |
| `card: false`, `table: false` | Hide from cards or table |
| `hideEmpty: true` | For a measure that applies to only some items (model prices in a news catalogue): cards and the dialog leave it out when the value is missing instead of showing `—`; the table still shows `—` and sorts it last. Leave it off when a missing value means "not found" |
| `sortLabel`, `sortChip` | Table header text and the label in the Order group |
| `detail` | Boxes in the dialog instead of the default value box; `withCost` appends the formatted value |

Up to three measures show as boxes on cards. The first table measure shares the date column; the rest get their own sortable columns.

### verification (optional)

```json
{"field": "status", "checked": "checked", "confidence": "confidence", "note": "verificationNote",
 "filter": true,
 "values": [["verified", "Verified", "ok"], ["unverified", "Unverified", "warn"],
            ["conflicting", "Conflicting sources", "alert"], ["outdated", "Needs re-check", "warn"]]}
```

All keys are optional; the values shown are the defaults. Each record may carry `status`, `checked` (`YYYY-MM-DD`), `confidence` (free text, e.g. `high`) and `verificationNote` (markdown with links). The third element of each value is its tone: `ok`, `warn` or `alert`. `filter` adds a Status facet. A record without a status shows "not yet checked".

### facets

```json
{"key": "region", "field": "group", "label": "Region", "all": "All regions",
 "values": ["Nordics", "Mediterranean"], "other": "Other countries", "counts": true}
{"key": "genre", "field": "genres", "label": "Genre",
 "options": [["portrait", "Portrait"], ["art", "Art"]]}
{"key": "design", "label": "Design", "counts": true}
```

`field` (default `key`) may hold a string or a list. Options come from `options` (`[value, label]` pairs), else `values` (+ `other`, which also catches anything unlisted), else every value found in the data. `key` becomes the URL parameter: it must not clash with measure or sort keys or with `sort`, `direction`, `view`, `q`, `favorites`, `item`, `date`, `name`.

### sorts (optional)

`[{"key": "rank", "label": "By rank", "field": "rank", "better": "low"}]` — orders on non-measure fields. Date, measures and name are built in. Missing values sort last in both directions.

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
- `table`: list of columns `{"label": "…", "show": [spec, …]}` after the name, date and measure columns.
- `detail.subtitle`: fields joined under the dialog title (facet keys allowed).
- `detail.lead`: extra boxes beside the image, after the verification, date and measure boxes.
- `detail.fields`: the two-column body.

### strings

Overrides for interface copy. Keys and English defaults are in `scripts/build.py` (`DEFAULT_STRINGS`, plus `DATE_STRINGS` per date kind). Common ones: `nameColumn`, `searchPlaceholder`, `details`, `detailsShort`, `researched`, `criteria`, `source`, `byDate`, `byMeasure`, `emptyEdition`, `skip`. Placeholders: `{n}`, `{total}`, `{noun}`, `{date}`, `{from}`, `{to}`, `{label}`, `{level}`.

## URL

Facets, zero toggles, search (`q`), `sort`, `direction` (only when not the natural one), `view`, `favorites` and the open record (`item`) live in the query string. Old `?call=` links still open the record.

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
