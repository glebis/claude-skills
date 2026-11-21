# Data format

All files live in the project folder. Records join on a stable `id` (lowercase, underscores). Keep ids across runs.

## calls.json — full research (array)

| Field | Meaning |
| --- | --- |
| `id` | Stable id |
| `group` | Region; must match a name in `profile.json` `regions`, otherwise shown as "Other countries" |
| `name` | Official name |
| `place` | City / country or "online" |
| `url` | Official page (https) |
| `deadline` | Full deadline text, including time zone, physical arrival dates and conflicts |
| `fee` | All fees and packages, original currency |
| `style`, `photos`, `print`, `rights`, `winners`, `eligibility`, `benefit` | Full researched text; `—` when unknown |
| `extra` | Further sources |

Text fields accept inline links as `[label](https://…)`. Only https links render as links.

`winners` starting with `—` renders the dash on its own line and the rest (for example an archive link) below it.

## catalog-meta.json — display fields (object keyed by id)

| Field | Meaning |
| --- | --- |
| `short` | Short name for cards, table and timeline |
| `date` | Deadline used for sorting and the timeline, `YYYY-MM-DD` |
| `euro` | Comparison fee in euros (number; `0` for free) |
| `price` | The package the euro value refers to, in original currency |
| `formats` | Any of `Awards & competitions`, `Exhibitions & festivals`, `Publications & photobooks`, `Grants & residencies` |
| `genres` | Any of `portrait`, `art`, `documentary` |
| `photoSummary`, `printSummary`, `rightsSummary` | One-line summaries |
| `timeNote` | Time and time zone, or a short caveat |
| `feeNote`, `rightsNote` | Optional one-line notes shown in the table |

A `price` containing `US$` or `£` shows the euro value with `≈`.

## snapshot.json

```json
{"date": "2026-11-21", "label": "21 November 2026", "minimumDeadline": "2026-12-21"}
```

`date` is the last research run, not the build date.

## profile.json

```json
{
  "regions": ["Nordics", "Mediterranean", "Asia Pacific", "Other countries"],
  "criteria": ["**Up to €50** per fixed-fee application", "Deadline **from {minDeadline}**", "Any nationality, over 18"]
}
```

`criteria` lines appear under "Selection criteria & budget"; `**bold**` and `{minDeadline}` are supported. Personal eligibility details belong here, in the user's own project, not in the skill.

## assets/manifest.json (array)

| Field | Meaning |
| --- | --- |
| `id` | Record id |
| `type` | What the image is: "2026 winner", "Poster", "Exhibition view" |
| `caption`, `credit` | Full caption and credit |
| `short_credit` | Name shown on the card; omit when unknown |
| `source_url` | Page the image comes from |
| `local_path` | Original file, relative to the project |
| `mime` | MIME type of the original |
| `image_url` | Remote fallback when no local file exists |

`assets/previews/<id>.webp` is preferred over `local_path` when present.
