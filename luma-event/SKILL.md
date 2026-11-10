---
name: luma-event
description: End-to-end AGENCY Community event on Lu.ma - cover image, Zoom meeting, the Lu.ma event page, invites to calendar contacts, and a social announcement draft. Use when creating a community meetup, talk, workshop or discussion on Lu.ma, or when the user says "/luma-event", "set up a luma event", "create the meetup on luma".
---

# Lu.ma Event Creator

Pipeline: **cover → owner approves → Zoom → Lu.ma event → invites (owner confirms) → announcement draft.**
Stop and report if a step fails. Never run bare `sleep N` or `timeout` (neither works in this
harness on macOS). To wait for something, poll in a loop: `n=0; until <check> || [ $n -ge 15 ]; do sleep 2; n=$((n+1)); done`.

## Inputs

Ask once for anything missing; resolve relative dates ("tomorrow") to absolute ones.

| Field | Required | Notes |
|---|---|---|
| title | yes | e.g. `Fable 5.2 — новый фронтир?` |
| date, time | yes | Europe/Berlin |
| duration | no, 90 | minutes |
| description | no | if the owner gives text, use it **verbatim**; otherwise use the template below |
| topics | no | 2–4 short lines for the cover; derive from the description when none are given |
| speaker, bio, photo | no | an event can have **no speaker**: skip the slot entirely |
| calendar | no | `AGENCY: Community Events` |

Do not put third-party logos (Anthropic, OpenAI, …) on covers. A trademarked logo can make
a community event look like an official one. Use the title and a graphic instead, and say why.

## Step 1: Cover

```bash
python3 scripts/render_cover.py --title "*Fable 5.2*|новый|фронтир?" \
  --date 2026-11-11 --time 18:00 \
  --topic "смотрим примеры" --topic "рекомендации по использованию" --topic "свободное обсуждение" \
  [--speaker "Name" --bio "…" --photo path.png] [--field wave|horizon|none]
```

- `|` breaks a title line; `*…*` is the orange accent. The first two topics get orange markers.
- With no photo the title runs full width at 84px and the bottom carries a wireframe field:
  `wave` (warped terrain with a diagonal crest and teal echoes; the default) or `horizon` (calm
  terrain, off-centre sun). With a photo the field defaults to `none`.
- Photo from the clipboard: save it first with
  `osascript -e 'set f to POSIX file "'$HOME'/Desktop/speaker-photo.png"' -e 'set i to the clipboard as «class PNGf»' -e 'set r to open for access f with write permission' -e 'write i to r' -e 'close access r'`.
- Output: `~/Desktop/agency-luma-cover.{html,png}`. The script checks the size (1600×1600).
  Rendering uses Python Playwright and falls back to installed Chrome; Node `playwright` is not
  installed globally.
- Look at the PNG yourself (Read it) before showing it: dots or graphics must not touch the
  text, and the thin frame must be visible all round. Then `open` it and **wait for the owner's
  approval**. Iterate here; nothing external exists yet.

## Step 2: Zoom

```bash
python3 scripts/zoom_create.py "<title>" <date> <time> --duration 90
```

Prints the meeting id and a masked join URL, and writes the real URL (with its passcode) to the
printed file. Never grep or echo the raw Zoom output: the join URL contains `pwd=`, and filtering
lines with `pwd` also throws away the URL you need. Zoom reports the start in UTC; 17:00 UTC is
18:00 CET.

## Step 3: Lu.ma event

Use **browser-mate's** dedicated Chrome. It never quits or kills any browser (no
`osascript quit`, no `pkill`), and the owner's windows stay open.

```bash
PORT=$(python3 ~/.claude/skills/browser-mate/scripts/browser.py automation | tail -1)
ab(){ agent-browser --cdp "$PORT" --session luma "$@"; }
ab open "https://lu.ma/create"
```

Then fill the form following **`references/luma-form.md`**: the recipes for sign-in
(Google passkey check: the owner confirms it via cenno), calendar, the date picker, the end-time
list, cover upload, description, the Zoom link, and the safe Create Event retry. The owner's
go-ahead after the cover counts as approval to publish; still take a screenshot of the filled
form before clicking Create.

Success: URL `/event/manage/evt-…`; take the public `luma.com/<slug>` from the page text.

## Step 4: Invites

Lu.ma → Invite Guests → Calendar contacts → **Everyone** → Select All → Next → Send.
Recipes are in `references/luma-form.md`. **Always confirm through cenno first**, with the exact
recipient count and invites left, and offer "add a short message first". Do not count an
earlier "go" or "send invites to everyone" as consent to the number shown: say the number.

## Step 5: Announcement draft

Draft a post (Facebook/Telegram) in the owner's voice and hand it over as text. Do not post it.
Merge any opener the owner gives with the event description, turn third person into first
("интро Глеба Калинина" → "моё интро"), and drop repeated phrases. End with the date, time in CET,
"Zoom · бесплатно" and the Lu.ma link.

## Finish

Report: Lu.ma URL, Zoom meeting ID (not the passcode), the cover path, the invite count, and the
announcement text. Leave browser-mate's Chrome running.

## Description template (when the owner gives none)

```
О чём поговорим:

• {topic 1}
• {topic 2}
• {topic 3}

Спикер: {speaker_name} — {speaker_bio}
```

Leave out the Спикер line when there is no speaker.
