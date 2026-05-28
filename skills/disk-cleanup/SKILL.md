---
name: disk-cleanup
description: Scan and clean macOS system caches, package manager caches, and app data to reclaim disk space. Surveys ~/Library/Caches, ~/.cache, Docker, npm/pip/uv/pnpm, Homebrew, browser caches, app updater caches, Claude Desktop, Xcode DerivedData, Playwright browsers, system logs, and ML model caches. Presents a size-sorted inventory table, offers four preset cleanup levels (safe / safe+docker / full / pick-individually), executes cleanup using `trash` (never rm), and reports before/after disk usage. IMPORTANT — you MUST use this skill whenever the user's request involves any of these scenarios on macOS: freeing disk space, cleaning or clearing caches, investigating what's consuming storage, running low on disk, "disk is full", "clean up my Mac", "free up space", "clear caches", "storage cleanup", "what's eating my disk", "where did my space go", checking disk usage of caches, "disk almost full" warnings, needing space for Xcode or other large installs, or any complaint about low available storage on their Mac. This skill covers the ENTIRE workflow from survey through cleanup — do not attempt to handle these requests without it.
---

# Disk Cleanup

Clean macOS caches and temporary files to reclaim disk space. Uses `trash` (never `rm`) so files can be recovered from Trash if needed.

## Parameters

The user may specify these inline or you can ask:

- **preset**: `safe` | `docker` | `full` | `pick` (default: ask the user)
  - `safe` — app updater caches, browser caches, package manager caches, logs, Playwright, old Claude bundles. No risk of breaking anything
  - `docker` — everything in `safe` + `docker system prune -a`
  - `full` — everything in `docker` + ML model caches (HuggingFace, Kokoro, etc.)
  - `pick` — present each item individually for the user to accept/reject
- **skip**: comma-separated list of locations to leave alone (e.g., `skip: huggingface, docker`)
- **dry-run**: if true, only report sizes without deleting anything
- **auto-empty-trash**: if true, empty Trash automatically after cleanup. If false (default), remind the user to empty Trash manually

## Workflow

### Phase 1: Disk snapshot

Run these in parallel to establish baseline:

```bash
# Overall disk usage
df -h / | tail -1 | awk '{print "Disk: "$2" total, "$4" available, "$5" used"}'

# Trash size
du -sh ~/.Trash 2>/dev/null
```

### Phase 2: Survey cache locations

Measure all known cache locations. Run the size checks in parallel where possible. The categories below are organized by cleanup preset — `safe` includes the first group, `docker` adds Docker, `full` adds ML models.

#### Safe targets

These are always safe to clear — they're download caches, updater artifacts, or regenerable data.

| Category | Paths to check |
|---|---|
| App updater caches | `~/Library/Caches/ms-playwright`, `~/Library/Caches/pencil-updater`, `~/Library/Caches/superpowers`, `~/Library/Caches/com.electron.wispr-flow.ShipIt`, `~/Library/Caches/timebuzzer-updater`, `~/Library/Caches/notion.id.ShipIt`, `~/Library/Caches/@granolaelectron-updater` |
| Browser caches | `~/Library/Caches/Google`, `~/Library/Caches/company.thebrowser.Browser`, `~/Library/Application Support/Google/Chrome/Default/Service Worker/CacheStorage`, `~/Library/Application Support/Google/Chrome Beta/Default/Service Worker/CacheStorage` |
| Package managers | npm: `~/.npm/_cacache`; pip: `~/Library/Caches/pip`; uv: `~/Library/Caches/uv`, `~/.cache/uv`; pnpm: `~/Library/pnpm`; Homebrew: `$(brew --cache)` |
| Claude Desktop | `~/Library/Application Support/Claude/Cache`, `~/Library/Application Support/Claude/Code Cache` |
| System caches | `~/Library/Caches/SiriTTS`, `~/Library/Caches/CloudKit`, `~/Library/Caches/com.googlecode.iterm2`, `~/Library/Caches/com.raycast.macos`, `~/Library/Caches/com.raycast-x.macos`, `~/Library/Caches/com.obsproject.obs-studio` |
| Dev tool caches | `~/.cache/codex-runtimes`, `~/Library/Caches/node-chromium`, `~/Library/Developer/Xcode/DerivedData` |
| Logs | `~/Library/Logs/*` |
| Misc app caches | `~/Library/Caches/imageview`, `~/Library/Caches/ort.pyke.io` |

#### Docker targets (preset: docker, full)

| Category | Action |
|---|---|
| Docker prune | `docker system prune -a -f` (removes unused images, containers, networks) |
| Docker logs | `~/Library/Containers/com.docker.docker/Data/log/*` |

Docker prune can take a while — run it in the background.

#### ML model targets (preset: full)

| Category | Paths |
|---|---|
| HuggingFace | `~/.cache/huggingface` |
| Kokoro ONNX | `~/.cache/kokoro-onnx` |
| qmd embeddings | `~/.cache/qmd` |

Warn the user before clearing ML models: "These models will need to be re-downloaded if you use them again."

### Phase 3: Present inventory

Build a markdown table sorted by size (largest first), showing:

```
| Location | Size | Preset | Safe to clear? |
|---|---|---|---|
| Docker VM disk | 7.6 GB | docker | Yes (prune) |
| ~/.cache/huggingface | 2.2 GB | full | Re-download needed |
| ~/Library/Caches/Google | 1.4 GB | safe | Yes |
| ... | ... | ... | ... |
```

Also show:
- Total recoverable per preset level
- Current available disk space

Only show items that actually exist and are non-trivially sized (>10 MB).

### Phase 4: Get user choice

If no preset was specified, ask the user which level they want using AskUserQuestion with these options:

1. **Safe caches only** — app updaters, browser caches, package managers, logs. ~X GB. No risk
2. **Safe + Docker prune** — everything above + Docker cleanup. ~X GB
3. **Safe + Docker + ML models** — maximum cleanup. ~X GB. Models need re-download
4. **Pick individually** — choose item by item

Fill in the actual GB estimates from the survey.

### Phase 5: Execute cleanup

For each item in the chosen preset (respecting `skip` list):

1. **Package managers** use their own clean commands:
   - `npm cache clean --force`
   - `pip cache purge`
   - `uv cache clean`
   - `brew cleanup -s`

2. **Docker** uses `docker system prune -a -f` (run in background — it can be slow)

3. **Everything else** uses `trash <path>` (never `rm`)

4. **Claude Desktop VM bundles** (`~/Library/Application Support/Claude/vm_bundles`): list contents first. Only trash bundles that aren't the currently active one. If there's only one bundle, skip it.

If `dry-run` is true, skip this phase and just report what would be cleaned.

### Phase 6: Handle Trash

After cleanup, measure Trash size. If `auto-empty-trash` is true, empty it via AppleScript:

```bash
osascript -e 'tell application "Finder" to empty the trash'
```

If false, remind the user: "X GB is now in Trash. Empty it to actually free the space."

### Phase 7: Report results

Show before/after comparison:

```
## Cleanup Summary
- Before: X GB available (Y% used)
- After:  X GB available (Y% used)
- Freed:  X GB
```

If Docker prune ran in background, note that additional space may be freed once it completes.

### Bonus: Telegram note

Telegram's media cache (often 1-3 GB) can't be safely cleared from the terminal — the `postbox` directory contains the message database. Tell the user: "Telegram media cache can be cleared from Telegram Settings > Data and Storage > Storage Usage."

## Discovery of new cache locations

The categories above are based on a real macOS workstation as of mid-2026. Cache locations change as apps are installed/removed. At the start of Phase 2, also run a broad sweep to catch unlisted large items:

```bash
du -sh ~/Library/Caches/* 2>/dev/null | sort -rh | head -25
du -sh ~/.cache/* 2>/dev/null | sort -rh | head -15
```

If any item over 100 MB appears that isn't in the known categories, include it in the inventory with a note that it's an "uncategorized cache" and let the user decide.
