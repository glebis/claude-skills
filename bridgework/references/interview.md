# Audit interview

The scan finds what is installed or configured on this Mac. The interview finds what the person actually uses, and what no scan can see. Keep it brief: two rounds of three or four questions, then build. More detail can come later, on the canvas.

## Consent for the scan

Show the output of `audit.py --plan`, then ask one multi-select question, for example:

> I can scan this Mac to start your stack. It only reads names, never contents or secret values, and nothing leaves the machine. Which parts may I look at?
> - Apps: names of installed apps
> - Command-line tools: whether known tools are on PATH (nothing is run)
> - MCP servers: server names in Claude and Cursor config files
> - Local models: model names in Ollama and LM Studio folders
> - Key names: names of variables like `OPENAI_API_KEY`, never their values

"None" is a full answer: build from the interview alone. Consent covers this conversation only. Ask again before any later scan.

## Reading the audit

- `matched`: catalog tools with evidence. `configured` means a key or MCP server exists; `installed` means an app, folder, command or model exists. Neither proves a working call.
- `unmatched.apps`: apps the person installed that the catalog does not know. Most are not stack parts (games, utilities). Pick at most ten that could take in or give out something useful (notes, audio, recordings, tasks, data, automation) and ask about those only.
- `unmatched.mcp` and `unmatched.keys`: usually real capabilities. Ask what each one is for.

## Round one: confirm

1. Show the matched tools grouped by domain. Ask which are not really in use, so they can be dropped.
2. Show the shortlisted unmatched items. Ask which ones to include.
3. Ask where things run if it is not this Mac: another machine at home (place `home`, with a label such as "Mac mini (LAN)"), a rented server (`vps`), a phone or watch (`device`), or a hosted service (`hosted`).

## Round two: what a scan cannot see

1. Data on the phone or watch: health, location, photos, voice notes.
2. Hosted accounts used every week: calendars, mail, meeting recorders, storage, research and model APIs.
3. Things built by the person: scripts, bots, small datasets, home automations.
4. Known dead ends: pairs that do not connect today, and why. These become `gaps`.

## Writing custom parts

For each confirmed item that is not in the catalog, decide, and ask only when it is unclear:

- `takes` and `gives`: one or two items each, using the types in `stack-format.md`. A part that only observes takes nothing.
- `act`: what it does, in plain words, starting with a verb ("transcribes calls", "keeps tasks").
- `evidence`: `user-confirmed` when only the person said so; the audit's level when it was found.
- `unknown`: what nobody has checked, such as "Which export formats it has". This feeds the Sources prompts.
- `docs`: the official documentation URL, when known with confidence. Leave it out rather than guess.

Never store account names, hostnames, IP addresses, file contents or secret values in the stack file. Labels like "Mac mini (LAN)" are enough.
