---
name: cull
description: Use when the user wants to view, review, rate, organize, search, or export images / AI-art generations with the Cull app (https://cull.company/ · https://github.com/glebis/cull). Trigger on "show me these images", "review this batch", "open these in Cull", "rate / shortlist / collect these", "find similar images", "make a smart collection", "run a quality pass", "export the keepers", "publish this collection". Works via the `cull` CLI by default (no MCP required); the `mcp__cull__*` tools are optional for richer interactive control.
---

# Cull

Cull is a local AI-art image-library app: import folders, browse, rate/decide, build collections, run vision/quality analysis, find-similar via embeddings, and export/publish. This skill is a usage map over its automation surface, not a reimplementation.

**Links:** website [cull.company](https://cull.company/) · source [github.com/glebis/cull](https://github.com/glebis/cull)

Cull exposes the **same operations four ways**: the `cull` CLI, the `cull://` URL scheme, the GUI, and an MCP server — all thin wrappers over one Rust core. **Default to the CLI + URL scheme.** They need no MCP connection and survive app restarts. Reach for the MCP only when you need interactive control the headless surface doesn't implement yet (see "When you need the MCP").

## The one core rule (do not skip)

**To show or review images, use Cull — never `open <image>` or Preview.** The user does not want Preview windows. Display by importing into Cull's library and fronting the app on the folder (below). Fronting the app is fine; opening image *files* with `open` is not.

## Driving Cull headless (the default path)

The binary lives at `/Applications/Cull.app/Contents/MacOS/cull`. Set it once:

```bash
CULL="/Applications/Cull.app/Contents/MacOS/cull"
```

With no subcommand it launches the GUI; with a subcommand it runs **headless and exits**, writing to the same library DB the running app reads. Add `--json` for machine-readable output.

**Show / review a batch** — the most common task. Import (headless), then front the app on the folder via the URL scheme:

```bash
$CULL --json import_folder --folder_path "/abs/path/to/batch"
open "cull://open?path=/abs/path/to/batch&view=grid"   # &view=loupe for single-image detail
open -a Cull                                            # ensure the window is frontmost
```

The user now sees the batch in Cull. Never `open` the image files. Re-running `import_folder` is safe — already-imported files are skipped.

### Implemented CLI subcommands

These are live in the shipped binary (`cull --help` to confirm). Field names match the MCP tool params.

| Command | Purpose |
|---|---|
| `import_folder --folder_path P` / `import_files --file_paths a,b` | Bring a folder / specific files into the library |
| `list_folders` / `list_images [--limit N --offset N]` / `list_collections` | Enumerate folders / images / collections |
| `get_library_stats` | Library-wide counts |
| `list_export_presets` / `export_images --image_ids … --output_dir … --format …` | List presets / export to disk (also `--collection_id` or `--folder_path`) |
| `get_embedding_model_download_info` / `download_embedding_model` / `generate_embeddings` | Embedding model prereq + build (async) |
| `analyze_image_quality` / `get_image_quality` / `get_quality_count` | Run quality analysis / read scores / count by bucket |
| `call_tool <tool> --params_json '{…}'` | Generic escape hatch — call any MCP-named tool with a JSON object |

`call_tool` accepts MCP-shaped params, so anything you'd do over MCP you can try headless:

```bash
$CULL --json call_tool import_folder --params_json '{"folder_path":"/abs/path"}'
$CULL --json call_tool export_images --params_json '{"collection_id":"<id>","output_dir":"/tmp/out","format":"original"}'
```

### URL scheme (GUI actions)

`open "cull://<action>?<params>"` — paths URL-encoded, multiple paths comma-separated. GUI actions front the window; if the app isn't running, macOS launches it.

| Action | Example |
|---|---|
| open / navigate | `cull://open?path=/abs/folder&view=grid` (`view=loupe`, `&focus=N`, `&fullscreen=true`) |
| search | `cull://search?q=sunset` |
| similar | `cull://similar?path=/abs/ref.jpg&top=5` |
| rate / accept | `cull://rate?path=/abs/img.jpg&stars=4` · `cull://accept?path=/abs/img.jpg` |
| collection | `cull://collection/add?name=picks&paths=/abs/a.jpg,/abs/b.jpg` |

URL-scheme calls are fire-and-forget (no return value). When you need a result, use the CLI (`--json`) or the MCP.

## Recipes (CLI-first)

**Review a fresh batch.** `import_folder` → `open "cull://open?path=…&view=grid"` → `open -a Cull`. The user sees it in Cull. Never `open` the files.

**Loupe one image.** `open "cull://open?path=/abs/img.png&view=loupe"`.

**Export the keepers.** `list_export_presets` → `export_images` with `--collection_id` / `--folder_path` / `--image_ids`, an `--output_dir`, and `--format`.

**Quality pass.** `analyze_image_quality` (async — it returns a job; for CLI poll by re-reading) → `get_quality_count` for the distribution → `get_image_quality` per image.

**Embeddings prerequisite.** `download_embedding_model` (once) → `generate_embeddings` (async). Only then does similarity work (`cull://similar?…`, or `find_similar` over MCP).

## When you need the MCP (optional)

The headless CLI does **not** yet implement interactive curation and live navigation — those exist only as `mcp__cull__*` tools (or manual GUI). Reach for the MCP when you need to:

- **Navigate / show precisely from the agent**: `navigate_to_folder`, `show_image`, `show_collection` (the URL scheme covers the common cases, but these give programmatic control and confirmation).
- **Curate with round-trips**: `set_rating`, `set_decision`, `create_collection`, `add_to_collection`, `create_smart_collection`.
- **Search & vision with results**: `find_similar`, `search_by_object`, `detect_objects` / `get_detections`, `analyze_images`, `get_vision_metadata`.
- **Track async jobs**: `list_jobs` / `get_job` / `cancel_job`.
- **Publish**: `export_static_publish_package` / `serve_static_publish_package`, clipboard-collection tools.

**MCP mechanics.** These tools are named `mcp__cull__<tool>` and in Claude Code are **deferred** — schemas aren't loaded, so a direct call fails. Load before calling, only what the recipe needs:

```
ToolSearch "select:mcp__cull__navigate_to_folder,mcp__cull__set_rating"
```

**The MCP drops when Cull restarts.** Quitting/relaunching the app kills its MCP server; it must be reconnected by the user via `/mcp` before any `mcp__cull__*` call works again. The CLI + URL scheme have no such dependency — prefer them, and fall back to MCP only for the interactive operations above.

## Common mistakes

- **Using `open` / Preview instead of Cull.** The cardinal sin — review always happens in Cull (`import_folder` + `cull://open`, or the MCP show/navigate tools).
- **Reaching for the MCP first.** Default to the CLI + URL scheme; they're connection-free and restart-proof. MCP is the fallback for interactive curation.
- **Assuming the MCP survived a Cull restart.** It doesn't — the user must `/mcp` reconnect. Don't restart Cull mid-task if you depend on the MCP.
- **Calling a deferred MCP tool before loading it.** `ToolSearch "select:mcp__cull__…"` first.
- **Treating async ops as synchronous.** Embeddings, analysis, and large exports are jobs — poll, don't assume completion.
- **Guessing params.** Check `cull <command> --help` or load the MCP tool and read its schema.

## Safety & limits

- **Destructive ops need explicit intent.** `delete_collection` and `prune_audit_log` remove data; confirm before running.
- **Tokens are admin.** `create_token` / `rotate_token` / `revoke_token` change access credentials — don't touch unless the user explicitly asks.
