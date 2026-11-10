# Stack file format

`~/.bridgework/stack.json` is written by Claude after the audit and interview, and read by `scripts/build_stack.py`. The builder validates every field and lists all problems before writing anything.

```json
{
  "name": "My stack",
  "observed": "2026-11-10",
  "places": [{"id": "home", "label": "Mac mini (LAN)"}],
  "parts": [
    {"use": "obsidian", "evidence": "installed", "signals": [{"kind": "app", "detail": "Obsidian.app"}]},
    {"use": "ollama", "id": "ollama-home", "name": "Ollama on the Mac mini", "place": "home", "evidence": "user-confirmed"},
    {"id": "step-log", "name": "Step log", "domain": "body", "place": "device", "act": "counts steps on the phone",
     "takes": [], "gives": [{"type": "signal", "label": "daily step counts"}],
     "evidence": "user-confirmed", "unknown": ["How to export it"], "docs": "https://example.com/docs"}
  ],
  "gaps": [{"from": "step-log", "to": "obsidian", "statement": "No export route from the phone to the notes is known yet."}]
}
```

## Parts

- **Catalog part:** `{"use": "<catalog id>"}`. Copy `evidence` and `signals` from `audit.json` when it was found. Any field can be overridden, such as `place` or `name`. To add a second copy of a catalog tool, give it a new `id`.
- **Custom part:** needs `id` (lowercase, digits, hyphens), `name`, `domain`, `place`, `act`, `takes`, `gives`, `evidence`. Optional: `unknown` (list), `docs` (URL), `does` (verbs), `asThird` (`{"adds": "...", "then": "..."}`, used when it joins a route as a third part), `constraints` (`auth`, `data`, `deps`, `freshness`, `latency`, `cost`).
- `takes` and `gives` are lists of `{"type": "<type>", "label": "<plain words>"}`. Matching types are what the canvas draws as a direct fit.
- `places` may relabel a place or add one. A new place id also needs a sensible boundary; unknown places are treated as leaving for a vendor.

## Types (port shapes)
| id | label |
|---|---|
| `text` | Text |
| `record` | Structured record |
| `audio` | Audio |
| `media` | Image or video |
| `moment` | A moment in time |
| `file` | File |
| `signal` | Activity aggregate |
| `action` | Local action |
| `url` | URL |

## Domains
| id | label |
|---|---|
| `body` | Body and devices |
| `memory` | Notes and files |
| `time` | Time |
| `meetings` | Meetings |
| `research` | Research |
| `models` | Models |
| `sound` | Voice and sound |
| `images` | Images |
| `agents` | Agents and hosts |
| `work` | Work and messages |

## Places
| id | default label |
|---|---|
| `device` | iPhone / Watch |
| `mac` | This Mac |
| `home` | Home server (LAN) |
| `vps` | Rented server |
| `hosted` | Hosted API |

## Evidence levels
| id | meaning |
|---|---|
| `unknown` | Unknown — Named, but nothing inspected. |
| `user-confirmed` | User-confirmed — The owner said so. Live health and entitlements stay separate. |
| `configured` | Configured — A credential or config entry exists. Validity, quota and scope are untested. |
| `installed` | Installed — A tool, executable or path is present. That does not prove authentication or a working call. |
| `metadata-passed` | Metadata request passed — A read-only metadata request returned. No inference or action was run. |
| `account-connected` | Account connected — A broker reports an active connection. No action was run through it. |
| `e2e-verified` | End-to-end verified — A real run produced the outcome. Nothing in this sample has reached this state. |

Use `user-confirmed` for anything only the person said. `metadata-passed`, `account-connected` and `e2e-verified` need a run the person did themselves; the audit never sets them.
