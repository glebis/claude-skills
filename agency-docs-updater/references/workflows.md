# Fan-out workflows for agency-docs

Two jobs in this domain are a natural fit for the new [dynamic workflows](https://code.claude.com/docs/en/workflows.md)
feature (Opus 4.8, research preview): the **repo-wide MDX/embed audit** and the
**backfill/repair of past meetings**. Both fan out one agent per meeting, which is
exactly what workflows are built for — and what the single-meeting publish pipeline is
*not* (see `workflow-conversion-analysis.md`).

## Why these are prompts, not committed `.js` files

Dynamic workflows are created by *running* them: include the word `workflow` in a prompt,
let Claude write and run the orchestration script, then press `s` in `/workflows` to save
that run's script as a reusable `/command`. There is no published API for hand-authoring
the runtime `.js`, so the correct, runnable deliverable is a precise **trigger prompt** you
paste once. After the first good run, save it (`s` → `.claude/workflows/`) and it becomes
`/agency-mdx-audit` / `/agency-backfill` in every future session.

Run these **locally**, where `$DOCS_SITE_DIR` points at your agency-docs checkout. Before a
long run, allowlist the shell commands the agents need (`npm`, `git`, `python3`, the
YouTube/oEmbed checks) so they don't prompt mid-run.

---

## 1. MDX / embed audit  →  save as `/agency-mdx-audit`

Paste this (the word *workflow* triggers it):

> Run a **workflow** to audit every published lab meeting on the agency-docs site for
> publishing defects. The meetings are MDX files at
> `$DOCS_SITE_DIR/content/docs/claude-code-internal-*/meetings/NN.mdx` (NN = two digits).
> Fan out **one agent per meeting file**. Each agent checks its file and reports findings;
> do not fix anything. Check for:
>
> 1. **MDX compile hazards** (these break the Vercel build): HTML comments `<!-- -->`,
>    unescaped `<` that isn't a known tag like `<iframe>`, and bare `{` / `}` outside code
>    fences. (See `references/learnings.md`.)
> 2. **Unfilled placeholders** left by the pipeline: `[Название встречи]`,
>    `[Краткое описание встречи]`, `[Дата встречи]`.
> 3. **YouTube embed health**: extract the video id from the `youtube.com/embed/<id>`
>    iframe, then verify the video is live via the oEmbed endpoint
>    `https://www.youtube.com/oembed?url=https://youtu.be/<id>&format=json` — a "Not Found"
>    means the video was deleted/made private (a documented failure mode). Flag any meeting
>    with a missing iframe or a dead id.
> 4. **Dead external links**: HEAD/GET each external link in the body; flag non-2xx/3xx.
> 5. **Missing pieces**: no Fathom link, no YouTube link, or an empty summary.
>
> Have a final agent **cross-check and dedupe** the findings, then return one grouped
> report: per meeting (lab + number + path), the list of issues and a one-line suggested
> fix for each. Order by severity (build-breakers first). No code changes.

Once the report looks right, press `s` to save it as `/agency-mdx-audit`. Re-run it after
big edits or before a release; feed its build-breaker findings into the backfill workflow.

---

## 2. Backfill / repair past meetings  →  save as `/agency-backfill`

Run the audit first so this one has a worklist. Then paste:

> Run a **workflow** to repair the lab meetings flagged by the audit. Input: the list of
> `(lab, meeting number, issues)` from `/agency-mdx-audit` (or, if none given, re-derive it
> by scanning `$DOCS_SITE_DIR/content/docs/claude-code-internal-*/meetings/NN.mdx` for the
> same defects). Fan out **one agent per broken meeting**. Each agent fixes only its own
> file and only the flagged issues:
>
> - **Unfilled placeholders** → derive the title/description/date from the meeting's own
>   summary body and the YouTube metadata; fill them in. Keep the page's language
>   consistent (don't mix RU/EN — see `references/learnings.md`).
> - **MDX compile hazards** → escape/strip per the learnings (remove `<!-- -->`, escape bare
>   `<` and `{`).
> - **Dead/missing YouTube embed** → if the original `$VAULT_DIR/<video-name>.mp4` and the
>   Fathom transcript still exist, re-run the relevant `agency-docs-updater` steps (Step 3
>   re-upload + Step 3a verify + Step 4b metadata) and swap in the new id; otherwise leave
>   a `TODO` note in the agent's report rather than inventing a link.
> - **Dead external links** → mark them, don't guess replacements.
>
> Each agent must `cd $DOCS_SITE_DIR && npx mdx-bundler` or `npm run build` on its file's
> path (or, cheaper, validate the single file compiles) before declaring success, since the
> whole point is not to re-break the build. Agents touch **different files**, so no worktree
> conflicts. Return a per-meeting report of what was changed and what still needs a human.
>
> Do **not** commit or push — leave the working tree dirty so I can review the diff, run
> `npm run build`, and commit myself.

Save as `/agency-backfill`. Keep commit/push manual: this writes to a public site, and a
workflow can't pause for sign-off mid-run.

---

## Caveats (per the official docs)

- **Research preview**, v2.1.154+. Turn on via `/config` (Pro) if needed.
- **No mid-run user input** — only tool-permission prompts can pause. That's why both
  workflows *report* (audit) or *leave the tree dirty* (backfill) instead of pushing.
- **Cost**: many parallel agents use meaningfully more tokens than a conversational pass.
  Consider routing the per-file agents to a smaller model when you describe the task.
- **Limits**: up to 16 concurrent agents, 1,000 per run. Fine for dozens of meetings.
- **Resume** works only within the same session; if you exit, the run starts fresh.
