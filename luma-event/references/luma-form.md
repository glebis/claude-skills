# Lu.ma create form: what works

Recipes for each control, from a run on 2026-11-10. Lu.ma changes its UI; when a recipe
fails, take a screenshot before improvising.

All commands assume this shell function. In zsh, `A="agent-browser …"; $A …` does not
split into words and fails with "command not found", so use a function:

```bash
ab(){ agent-browser --cdp "$PORT" --session luma "$@"; }
```

Refs (`@e12`) change after every dialog opens or closes. Take a new `snapshot -i` before each
click and look up the ref by its label (`grep 'button "Create Event"'`), never reuse an old one.

## Sign-in

`luma.com/create` shows "Welcome to Luma" when signed out. Click **Sign in with Google**.
Google can then show:

- an account picker: pick the owner's account
- **"Verifying it's you…"** at `accounts.google.com/v3/signin/challenge/pk`: a passkey check.
  Only the owner can pass it (Touch ID or phone). Ask through cenno ("Confirm the passkey in
  the automation Chrome window, then tap Done") and wait. Never enter a password.
- a consent screen for a new permission: stop and ask.

## Calendar

`combobox "Choose Calendar"` opens a listbox; click `option "…AGENCY: Community Events"`.

## Date

Typing into `textbox "Start date"` is ignored. Click the generic wrapper around it to open
the picker, then click `button "Wednesday, November 11, 2026"` (full weekday and date as the
button's name). The end date follows the start date.

## End time

The start time defaults to 18:00 and the end to 19:00. Focusing the end minutes
spinbutton opens a list of times with durations, such as `"07:30 PM 1h 30m"`. Click that
option. Typing digits into the spinbutton does nothing.

## Cover

`button "file upload"` is the file input: `ab upload @<ref> /path/cover.png`. Verify with a
screenshot: the cover replaces the theme preview on the left.

## Description

`button "Add Description"` opens a dialog with `textbox "Event Description"`. Use
`ab type @<ref> "…"` per paragraph and `ab press Enter` between paragraphs. **Done** sometimes
needs a second click: take a new snapshot and click Done again if the dialog is still there.

## Zoom link

There is no "Virtual" toggle. `button "Add Event Location"` focuses a textarea
("Enter location or virtual link") and lists "Create Zoom meeting / Select existing Zoom /
Create Google Meet". Type the join URL with the keyboard, without echoing it:

```bash
ab keyboard type "$(cat "$JOIN_FILE")"
```

then click the suggestion `option "Zoom https://…"`. The location button then reads "Zoom https://…".

## Create Event

Before clicking, take a screenshot and check: calendar, title, date and times, Berlin
timezone, cover, location, description.

The first click can do nothing; the URL stays at `/create`. **Do not click again blindly.**
Open `https://luma.com/home` in a new tab, confirm the event is not listed, close the tab, take a
new snapshot of the form, then click the `button "Create Event"` ref from that snapshot.
Success means the URL becomes `/event/manage/evt-…`. The public link is in the page text:
`ab get text body | grep -oE 'luma\.com/[A-Za-z0-9]+'`.

## Invites

On the manage page: `button "Invite Guests"` (the one in the Invites section) → under
**Calendar contacts**, click `button "Everyone <N>"` → `button "Select All"`. The footer
then shows "<N-1> Selected" because the host is excluded, and the top right shows invites
left. Click **Next**: optional `textbox "Add a custom message here..."`, then `button "Send Invites"`.

Sending is irreversible and emails every recipient. Before clicking Send, ask the owner
through cenno and give the exact count, the list name and the invites left.

Success: the Invites section shows "0/<N> Invites Accepted". A second, empty "Inviting 0 People"
dialog can stay in the snapshot afterwards. It is harmless; leave it.
