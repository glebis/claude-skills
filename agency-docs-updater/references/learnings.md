# Learnings

## Pipeline
- Parallelize summary (Step 4) with YouTube upload (Step 3) — saves 10+ minutes
- `--resume-from upload` skips metadata/thumbnail regeneration on retry
- Always run `npm run build` locally before pushing — MDX errors cause Vercel deploy failures
- Zoom recordings may take ~15 min to process after meeting ends

## MDX pitfalls
- `update_meeting_doc.py` appends Marp presentation content with `<!-- -->` HTML comments — always strip everything after the summary. Use `head -N` truncation at the last valid `---` before `<!-- _class: lead -->`
- MDX breaks on HTML comments (`<!-- -->`), unescaped `<`, and bare `{` characters

## YouTube API
- Always pass `--title` from Fathom frontmatter — without it, the LLM generates poor/generic titles for Russian content
- `youtube.force-ssl` scope is needed for both uploads and metadata updates
- **Videos can silently disappear after upload.** On 2026-05-16, a video was uploaded successfully (got VIDEO_ID), but YouTube later deleted it (shows as "Deleted video" with `privacyStatusUnspecified`). Always run Step 3a verification after upload. If verification fails, re-upload before proceeding
- The YouTube oEmbed API (`youtube.com/oembed?url=...`) returns "Not Found" for deleted/private videos — useful quick check

## Meeting number detection
- Don't trust auto-detected meeting number blindly — placeholder MDX files may already exist. Check existing files by date content first, use `-n NN` to override

## Thumbnails
- Nano Banana with "pure black background" prompt usually returns black-bg + light lines — skip `-negate`
- Always inspect the raw image before recoloring — wrong assumptions flood the image with orange
- Use custom renderer config JSON with `imagePath` field

## English-language labs
- When `TRANSCRIPT_LANG=en`, rewrite the MDX entirely with English labels — `update_meeting_doc.py` defaults to Russian and the translation fallback produces broken mixed-language output
- Correct spelling: "WisprFlow" (https://wisprflow.ai/r/GLEB3)

## Git push
- Only stage pipeline-created files — never `git add .`
- If remote is ahead: `git stash push`, `git pull --rebase`, push, `git stash pop`

## Aggregations (Step 9)
- `rebuild_aggregations.py` regenerates database/glossary/library from ALL meetings — it's idempotent, safe to re-run
- Glossary definitions live in `.agency-glossary.json`, NOT in the generated MDX — edit the store, then re-run. Definitions survive rebuilds; only genuinely new terms are flagged
- Generated MDX pages carry a `{/* GENERATED ... */}` banner — don't hand-edit them
- The acronym extractor strips URLs first so referral codes (e.g. `…/r/GLEB3`) aren't mistaken for terms; still skim the NEW-term list for noise before defining
- Per-meeting Fathom/YouTube links are intentionally excluded from the library (they're in the database) — the library is for external resources only
- Always `npm run build` after a rebuild — the generated MDX can break the deploy just like meeting MDX can
