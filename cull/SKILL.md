---
name: cull
description: Use when the user wants to view, review, rate, organize, search, or export images / AI-art generations and the Cull MCP server is connected. Trigger on "show me these images", "review this batch", "open these in Cull", "rate / shortlist / collect these", "find similar images", "make a smart collection", "run a quality pass", "export the keepers", "publish this collection". Cull-specific — requires the `mcp__cull__*` tools; do not use for agents without that MCP.
---

# Cull

Cull is a local AI-art image-library app: import folders, browse, rate/decide, build collections, run vision/quality analysis, find-similar via embeddings, and export/publish. This skill is a usage map over its MCP, not a reimplementation — it teaches the key tools and the recipes that chain them.

## The one core rule (do not skip)

**To show or review images, use Cull — never `open <image>` or Preview.** The user does not want Preview windows. To display: `import_folder` then `navigate_to_folder`, or `show_collection` / `show_image`. Fronting the app with `open -a Cull` is fine; opening image *files* with `open` is not.

## Mechanics (do not skip)

These are MCP tools named `mcp__cull__<tool>`, and in Claude Code they are **deferred** — their schemas are not loaded, so calling one directly fails. Load before calling:

```
ToolSearch "select:mcp__cull__import_folder,mcp__cull__navigate_to_folder"
```

Load only the tools a recipe needs. Params below are kept generic on purpose — after loading a tool, read its schema for exact arguments. Long-running ops (embeddings, analysis, export) return a job; poll it, don't assume it's done.

## Quick reference

**Import / browse / display**
| Tool | One-liner |
|---|---|
| `import_folder` / `import_files` | Bring a folder / specific files into the library |
| `list_folders` / `list_folder_images` / `list_images` | Enumerate folders and their images |
| `navigate_to_folder` | Show a folder in the app (primary "review this batch" call) |
| `show_image` / `show_collection` | Display one image / a collection in the app |
| `get_image` / `get_library_stats` | Fetch one image's data / library-wide counts |

**Curate (rate / decide / collect)**
| Tool | One-liner |
|---|---|
| `set_rating` / `set_decision` | Star-rate / mark keep-reject-pick on an image |
| `create_collection` / `add_to_collection` | Make a manual collection and add images |
| `create_smart_collection` | Rule-based auto-collection (e.g. rating ≥ N, has object) |
| `list_collections` / `list_collection_images` / `show_collection` | List collections / their images / display one |
| `delete_collection` | Remove a collection (destructive — see Safety) |

**Search & vision**
| Tool | One-liner |
|---|---|
| `find_similar` | Visually similar images (needs embeddings first) |
| `search_by_object` / `detect_objects` / `get_detections` | Find / run / read object detection |
| `analyze_images` / `analyze_image_quality` / `get_image_quality` / `get_quality_count` | Run vision/quality analysis, read scores, count by bucket |
| `get_vision_metadata` | Read stored vision metadata for an image |

**Embeddings**
| Tool | One-liner |
|---|---|
| `download_embedding_model` | Fetch the model (one-time prerequisite) |
| `generate_embeddings` | Build embeddings so `find_similar` works (async job) |

**Jobs (long-running ops)**
| Tool | One-liner |
|---|---|
| `list_jobs` / `get_job` / `cancel_job` | Track / inspect / stop async work |

**Export & publish**
| Tool | One-liner |
|---|---|
| `list_export_presets` / `export_images` | List presets / export images to disk |
| `export_static_publish_package` / `serve_static_publish_package` | Build / serve a static web gallery |
| `export_static_publish_canvas` / `get_canvas_layout` / `list_session_canvases` | Canvas-layout publish helpers |

**Clipboard publish**
| Tool | One-liner |
|---|---|
| `publish_clipboard_collection` / `show_clipboard_collection` | Publish / show the clipboard-monitored collection |
| `get_clipboard_monitor_status` / `get_last_clipboard_publish` | Monitor status / last publish result |

**Generation metadata**
| Tool | One-liner |
|---|---|
| `set_generation_metadata` / `get_generation_run` | Attach / read AI-generation params (prompt, seed, model) |

**Tokens & admin** (don't touch unless asked — see Safety)
| Tool | One-liner |
|---|---|
| `create_token` / `list_tokens` / `rotate_token` / `revoke_token` | Manage API tokens |
| `get_audit_log` / `prune_audit_log` | Read / trim the audit log (prune is destructive) |
| `rescan_sources` / `rescan_sidecars` | Re-scan source folders / sidecar files for changes |

## Recipes

**Review a fresh batch.** `import_folder` (path) → `navigate_to_folder`. The user now sees the batch in Cull. Never `open` the files.

**Shortlist favorites.** Walk the batch, `set_rating` and/or `set_decision` per image → `create_collection` ("keepers") → `add_to_collection` the picks → `show_collection` to present. For a rule-driven shortlist instead, use a smart collection (below).

**Find more like this.** Ensure embeddings exist (see embeddings recipe), then `find_similar` on a reference image. For "all images containing a cat" use `search_by_object` (or `detect_objects` to populate, then `get_detections`).

**Smart collection.** `create_smart_collection` with rules (e.g. rating ≥ 4, quality bucket, detected object) → auto-populates and stays live → `show_collection`.

**Quality / vision pass.** `analyze_images` / `analyze_image_quality` over a folder (async — poll jobs) → `get_quality_count` for the distribution → `get_image_quality` / `get_vision_metadata` per image. Feed results into a smart collection (keep top quality) or a manual shortlist.

**Embeddings prerequisite.** `download_embedding_model` (once) → `generate_embeddings` (async) → watch with `list_jobs` / `get_job` until done. Only then will `find_similar` return results.

**Export the keepers.** `list_export_presets` → `export_images` (collection + preset + destination). To publish a shareable gallery: `export_static_publish_package` then `serve_static_publish_package` to view it locally.

## Common mistakes

- **Using `open` / Preview instead of Cull.** The cardinal sin — review always happens in Cull (`navigate_to_folder` / `show_collection` / `show_image`).
- **Calling a tool before loading it.** Deferred tools fail until `ToolSearch "select:mcp__cull__…"` loads the schema.
- **Calling `find_similar` with no embeddings.** It needs `download_embedding_model` + `generate_embeddings` first, or it returns nothing useful.
- **Treating long ops as synchronous.** Embeddings, analysis, and large exports are jobs — poll with `list_jobs` / `get_job` instead of assuming completion.
- **Guessing params.** Load the tool and read its actual schema rather than inventing argument names.

## Safety & limits

- **Requires the Cull MCP connected.** This skill is Cull-specific and not portable to agents without the `mcp__cull__*` tools.
- **Tokens are admin.** `create_token` / `rotate_token` / `revoke_token` change access credentials — don't touch unless the user explicitly asks.
- **Destructive ops need explicit intent.** `delete_collection` and `prune_audit_log` remove data; confirm the user actually wants it before running.
