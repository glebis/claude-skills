# Vault Daydream — Implementation Instructions

You are running the Vault Daydream skill. Follow these steps precisely.

## Step 0: Resolve Vault Root

Determine `VAULT_ROOT`:
1. Check if the current working directory contains a `.obsidian/` folder. If yes, use it as `VAULT_ROOT`.
2. If not, use `AskUserQuestion` to ask:
   - Question: "Where is your Obsidian vault located?"
   - Options: provide 2-3 likely paths if detectable (e.g., from `find ~ -maxdepth 3 -name ".obsidian" -type d 2>/dev/null | head -3`), plus an "Other" option for custom input.
3. Store the resolved path as `VAULT_ROOT` for all subsequent steps.

## Constants

```
VAULT_ROOT = (resolved in Step 0)
DAYDREAMS_DIR = Daydreams
DIGESTS_DIR = Daydreams/digests
HISTORY_FILE = ai-research/daydream/history.json
DAILY_DIR = Daily
EXCLUDE_DIRS = .obsidian, templates, node_modules, Daydreams, .claude, .git
LOOKBACK_DAYS = 120
PAIR_COUNT = 50
BATCH_SIZE = 5
SCORE_THRESHOLD = 7.0
MAX_EXCERPT_WORDS = 500
```

---

## Step 1: Scan Vault

### 1a. Get today's date
```bash
date +"%Y%m%d"
```
Store as `TODAY` (e.g., `20260214`).

### 1b. Find recent notes
Use Bash to list all .md files modified in the last 120 days, excluding certain directories:

```bash
find $VAULT_ROOT -name "*.md" -type f -mtime -120 \
  -not -path "*/.obsidian/*" \
  -not -path "*/templates/*" \
  -not -path "*/node_modules/*" \
  -not -path "*/Daydreams/*" \
  -not -path "*/.claude/*" \
  -not -path "*/.git/*" \
  -exec stat -f "%m %N" {} \; | sort -rn
```

This returns lines like: `1707900000 /path/to/note.md`

Parse into a list of `{path, timestamp}` objects.

### 1c. Load history for dedup
Read `ai-research/daydream/history.json` if it exists. This contains previously sampled pairs:
```json
{
  "sampled_pairs": [
    {"a": "Note A.md", "b": "Note B.md", "date": "20260213"}
  ]
}
```
If file doesn't exist, treat as empty: `{"sampled_pairs": []}`.

---

## Step 2: Extract Excerpts

For each note found in Step 1 (up to 200 notes — if more, take the 200 most recent):

1. **Read the file** using the Read tool
2. **Strip YAML frontmatter**: Remove everything between the first `---` and the second `---` (inclusive)
3. **Strip noise**: Remove code blocks (``` fenced blocks), raw URLs (http://...), wikilink brackets (keep the display text or link text), image embeds (![[...]]), HTML tags
4. **Extract title**: Use the first `# ` heading, or the filename (without .md extension) if no heading
5. **Take first 500 words** of the cleaned text
6. **Compute days ago**: `(now_timestamp - file_timestamp) / 86400`

Store as array:
```json
{
  "path": "relative/path.md",
  "title": "Note Title",
  "excerpt": "First 500 words...",
  "days_ago": 5
}
```

**Important**: Do NOT read all 200 files sequentially. Read in parallel batches of 20 using the Read tool (call 20 Read tools in a single response).

---

## Step 3: Generate Weighted Random Pairs

### 3a. Assign weights
For each note, assign a sampling weight based on recency:
- **days_ago <= 7**: weight = 3
- **days_ago <= 30**: weight = 2
- **days_ago > 30**: weight = 1

### 3b. Weighted random sampling
Generate 50 unique pairs using weighted random sampling:

Use Bash with Python for the random sampling:
```bash
python3 -c "
import json, random, sys

notes = json.loads(sys.stdin.read())
history_pairs = set()  # populated from history.json

# Build weighted pool
pool = []
for i, note in enumerate(notes):
    w = 3 if note['days_ago'] <= 7 else (2 if note['days_ago'] <= 30 else 1)
    pool.extend([i] * w)

pairs = set()
attempts = 0
while len(pairs) < 50 and attempts < 500:
    a = random.choice(pool)
    b = random.choice(pool)
    if a != b:
        pair = (min(a, b), max(a, b))
        pair_key = (notes[pair[0]]['path'], notes[pair[1]]['path'])
        if pair not in pairs and pair_key not in history_pairs:
            pairs.add(pair)
    attempts += 1

result = [{'a': notes[p[0]], 'b': notes[p[1]]} for p in pairs]
print(json.dumps(result))
" <<< 'NOTES_JSON_HERE'
```

Replace `NOTES_JSON_HERE` with the actual JSON array from Step 2. Also incorporate history dedup by adding known pairs to `history_pairs`.

If fewer than 50 pairs generated, that's fine — proceed with whatever was generated.

### 3c. Output
Store the pairs array. Each pair has:
```json
{
  "a": {"path": "...", "title": "...", "excerpt": "..."},
  "b": {"path": "...", "title": "...", "excerpt": "..."}
}
```

---

## Step 4: Synthesize Connections (Parallel Task Agents)

### 4a. Read synthesizer prompt
Read the file `.claude/skills/daydream/synthesizer-prompt.md` to get the prompt template.

### 4b. Batch pairs
Split the pairs into batches of 5. This yields up to 10 batches.

### 4c. Launch Task agents in parallel
For each batch, launch a Task agent with `model: sonnet`:

```
Task(
  subagent_type: "general-purpose",
  model: "sonnet",
  description: "Synthesize daydream batch N",
  prompt: "You are processing a batch of note pairs for the Vault Daydream system.

For each pair below, find deep non-obvious connections. Return a JSON array of results.

[SYNTHESIZER PROMPT TEMPLATE — filled in for each pair]

Pair 1:
Note A: {title} --- {excerpt} ---
Note B: {title} --- {excerpt} ---

Pair 2:
...

Pair 5:
...

Return ONLY a valid JSON array with one object per pair:
[
  {
    \"connection\": \"...\",
    \"synthesis\": \"...\",
    \"implication\": \"...\",
    \"suggested_title\": \"...\",
    \"title_a\": \"...\",
    \"title_b\": \"...\",
    \"path_a\": \"...\",
    \"path_b\": \"...\"
  },
  ...
]

Do NOT wrap in markdown code fences. Return raw JSON only."
)
```

**Launch up to 10 Task agents in a SINGLE message** (all in parallel). Each processes 5 pairs.

### 4d. Collect results
Parse the JSON arrays returned by each Task agent. Combine into one flat array of synthesis results.

If a Task agent returns malformed JSON, skip that batch and note the error. Do not retry.

---

## Step 5: Critique and Score (Parallel Task Agents)

### 5a. Read critic prompt
Read the file `.claude/skills/daydream/critic-prompt.md` to get the prompt template.

### 5b. Batch synthesis results
Split synthesis results into batches of 5 (same pattern as Step 4).

### 5c. Launch Task agents in parallel
For each batch, launch a Task agent with `model: haiku`:

```
Task(
  subagent_type: "general-purpose",
  model: "haiku",
  description: "Critique daydream batch N",
  prompt: "You are scoring synthesized insights for the Vault Daydream system.

For each insight below, rate on Novelty, Coherence, and Usefulness (1-10 each).
Accept if average >= 7.0. Be genuinely critical.

Insight 1:
Source notes: \"{title_a}\" and \"{title_b}\"
Connection: {connection}
Synthesis: {synthesis}
Implication: {implication}

Insight 2:
...

Return ONLY a valid JSON array with one object per insight:
[
  {
    \"novelty\": 8,
    \"coherence\": 7,
    \"usefulness\": 9,
    \"average\": 8.0,
    \"verdict\": \"accept\",
    \"reason\": \"...\",
    \"suggested_title\": \"...\",
    \"title_a\": \"...\",
    \"title_b\": \"...\"
  },
  ...
]

Include suggested_title, title_a, title_b from the input for tracking.
Do NOT wrap in markdown code fences. Return raw JSON only."
)
```

**Launch up to 10 Task agents in a SINGLE message** (all in parallel).

### 5d. Filter results
Combine all critic responses. Merge each critic score with its corresponding synthesis result. Keep only entries where `verdict == "accept"` AND `average >= 7.0`.

---

## Step 6: Write Outputs

### 6a. Create directories
```bash
mkdir -p $VAULT_ROOT/Daydreams/digests
```

### 6b. Write individual insight notes
For each accepted insight, create a file:

**Filename**: `Daydreams/{TODAY}-{slug}.md`

Generate `slug` from `suggested_title`: lowercase, replace spaces with hyphens, remove special characters, max 50 chars.

**Content template**:
```markdown
---
created_date: '[[{TODAY}]]'
type: daydream
source_notes:
  - '[[{title_a}]]'
  - '[[{title_b}]]'
scores:
  novelty: {novelty}
  coherence: {coherence}
  usefulness: {usefulness}
  average: {average}
---

# {suggested_title}

> Connection between [[{title_a}]] and [[{title_b}]]

{synthesis}

## Implication

{implication}

## Critic's Note

{reason}
```

Write each file using the Write tool. If multiple insights, write them in parallel.

### 6c. Write daily digest
**File**: `Daydreams/digests/{TODAY}-digest.md`

```markdown
---
type: daydream-digest
date: {TODAY}
pairs_sampled: {total_pairs}
insights_accepted: {accepted_count}
---

# Daydream Digest -- {TODAY}

## Stats
- Pairs sampled: {total_pairs}
- Insights generated: {total_synthesized}
- Accepted (avg >= 7.0): {accepted_count}
- Acceptance rate: {acceptance_rate}%

## Top Insights

{For each accepted insight, sorted by average score descending:}

### {rank}. {suggested_title} (avg: {average})
**Connecting**: [[{title_a}]] <-> [[{title_b}]]
{connection}

```

### 6d. Update daily note
Read `Daily/{TODAY}.md`. If it doesn't exist, create it from template first. Check if a `## Daydream` section already exists — if so, **replace** it entirely (to handle re-runs). If it doesn't exist, append it.

Content:
```markdown
## Daydream

Vault daydream found {accepted_count} insights from {total_pairs} pairs ({acceptance_rate}% acceptance).

Top connections:
{For each accepted insight, up to 5:}
- [[{TODAY}-{slug}|{suggested_title}]] (avg: {average}) -- [[{title_a}]] <-> [[{title_b}]]
```

---

## Step 7: Log History

### 7a. Update history.json
Read the existing `ai-research/daydream/history.json` (or start fresh if missing).

Add ALL sampled pairs (not just accepted ones) to the `sampled_pairs` array:
```json
{
  "sampled_pairs": [
    ...existing...,
    {"a": "path/to/note-a.md", "b": "path/to/note-b.md", "date": "{TODAY}"}
  ],
  "runs": [
    ...existing...,
    {
      "date": "{TODAY}",
      "pairs_sampled": {total_pairs},
      "insights_accepted": {accepted_count},
      "acceptance_rate": {acceptance_rate}
    }
  ]
}
```

Write back to `ai-research/daydream/history.json`.

---

## Step 8: Summary

Output a concise summary to the user:

```
Vault Daydream complete -- {TODAY}

{accepted_count}/{total_pairs} pairs produced insights (acceptance rate: {acceptance_rate}%)

Top insights:
1. {title} (avg: {score}) -- {title_a} <-> {title_b}
2. ...
3. ...

Files: Daydreams/{TODAY}-*.md
Digest: Daydreams/digests/{TODAY}-digest.md
```

---

## Error Handling

- **No notes found**: Tell user "No notes modified in last 120 days. Nothing to daydream about."
- **Fewer than 10 notes**: Warn user, proceed with fewer pairs (minimum 5 pairs if possible)
- **Task agent returns bad JSON**: Skip that batch, log the error, continue with other batches
- **All insights rejected**: Write digest with 0 accepted, tell user "All insights scored below threshold -- the vault might need more diverse content, or try again tomorrow."
- **History file corrupt**: Start fresh, warn user

## Performance Notes

- Reading 200 files: batch into groups of 20 parallel Read calls
- 10 synthesis Task agents run in parallel (single message)
- 10 critic Task agents run in parallel (single message)
- Total: ~3-4 tool-call rounds for the heavy lifting
