# map.json

Required: `project.name`, `surfaces`, `screens`, `stages`, `kinds`, `kindGuide`. All else is optional, and tabs with nothing to show disappear.

## project

`name`, `sub` (line under the title), `footer` (where the data comes from and how to refresh it), `jobsPath` (where job bundles are saved; default `~/jtbd/<project>-<slug>/`).

## surfaces

| Field | Meaning |
|---|---|
| `id`, `name`, `path` | Identity and source location |
| `kind` | Test kind suggested for screens here |
| `kinds` | Override per state, such as `{"refused": "py"}` |

## screens

| Field | Meaning |
|---|---|
| `id` | Stable uppercase ID, such as `SITE-BUY` |
| `s` | Surface ID |
| `n` | Name |
| `w` | What it shows |
| `e` | How it is reached |
| `x` | Exits, as screen IDs |
| `b` | Backend: route, command or module. Shown and searched |
| `t` | Main test files; base names are enough |
| `c` | Coverage: `ok`, `part`, `none` or `gap` (not built) |
| `biz` | `true` for business touchpoints |
| `k` | Optional test kind that overrides the surface |

## stages

`id`, `n`, `sc` (screen IDs), optional `biz`. Their order is the column order of the flow graph.

## scenarios

| Field | Meaning |
|---|---|
| `id` | Stable, such as `S-BUY-1` |
| `st` | Stage ID |
| `n` | Name |
| `sc` | Screens crossed, in order |
| `d` | Steps; the last entry is the expected result |
| `c` | `ok`, `part`, `none` or `gap` |
| `t` | Test files that cover it today |

## gaps

`t` (one sentence) and `sc` (the scenario it points at).

## jobs

| Field | Meaning |
|---|---|
| `id`, `t` | ID and short title |
| `stmt` | Three strings: `When …`, `I want …`, `so …` |
| `src` | `code`, `people` or `cand` |
| `ev` | `none`, `inferred`, `owner` or `user` |
| `fit` | `built`, `part` or `gap` |
| `fitNote` | One line on the fit today |
| `sc` | Screens that serve it |
| `actor`, `pr`, `from` | Optional: who has it, the public promise, where it came from |

`jobSources` optionally relabels the sources: `{"code": {"n": "…", "ev": "…", "path": "…"}, "people": {…}, "cand": {…}}`.

## kinds and kindGuide

`kinds` maps an ID to `[name, one-line description]`. IDs are lowercase. The first seven get distinct colours.

`kindGuide` maps a kind to `{where, how, run}`, which go straight into agent prompts: where the test goes, how it is written and the command that runs it. A kind with no guide can be counted but not suggested. `defaultKind` is used when a surface has no kind.

`outside` is a regex of outside services. Failure paths on screens whose `b` matches suggest the `mock` kind.

## testing

| Field | Meaning |
|---|---|
| `globs` | Where tests live, relative to the repo; `**` works |
| `kinds` | Ordered `{pattern, kind}` rules on the path. Default is by extension: `py`, `js`, `rust`, `go`, `swift`, `ruby` |
| `links` | `{pattern, screens}` rules linking files to screens; a file may match several |
| `ignore` | Regex of files that are about no screen |
| `defaultScreen` | Screen that collects all unlinked files |
| `extras` | Checks with no parseable names: `{file, kind, names, screens}` |

A test whose name contains mock, fake or stub counts as `mock` when that kind exists.

## layers, rules, sequences

`layers`: `{n, items, note}`, top to bottom. `rules`: `{t, d}`. `sequences`: `{t, mermaid}`, where `mermaid` is a `sequenceDiagram` source. Diagrams are cached in `.app-map-cache/` beside the map; keep that out of git.
