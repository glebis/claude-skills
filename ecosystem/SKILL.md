---
name: ecosystem
description: Audit the Claude Code ecosystem — skill health and staleness, project activity pulse, CLAUDE.md instruction drift, Mac Mini service status. Use this skill whenever the user asks about ecosystem health, stale skills, abandoned projects, system status, infrastructure check, "what's broken", "what's stale", "how's my setup", or any request to review the state of their Claude Code environment. Also triggers on "/ecosystem", "audit my ecosystem", "ecosystem health", "ecosystem audit".
---

# Ecosystem Audit

On-demand audit of the Claude Code ecosystem. Runs 4 checks, prints a full report with an attention summary, and appends a summary to today's daily note.

## Workflow

Run all 4 checks sequentially using the bash blocks below. Each block runs in a fresh shell, so after all checks complete, compose the daily note summary and attention rollup from the terminal output you've collected.

**CRITICAL**: Run `date +"%Y%m%d"` before writing to the daily note.

### Step 1: Skill Health

Scan `~/.claude/skills/` for skill freshness and broken symlinks.

```bash
NOW=$(date +%s)
D30=$((NOW - 30*86400))
D90=$((NOW - 90*86400))
ACTIVE="" BROKEN=""
ACTIVE_N=0 RECENT_N=0 STALE_N=0 BROKEN_N=0 TOTAL=0

for entry in ~/.claude/skills/*/; do
  [ -d "$entry" ] || continue
  name=$(basename "$entry")
  TOTAL=$((TOTAL + 1))

  if [ -L "${entry%/}" ] && [ ! -e "${entry%/}" ]; then
    target=$(readlink "${entry%/}")
    BROKEN="${BROKEN}  - ${name} -> ${target}\n"
    BROKEN_N=$((BROKEN_N + 1))
    continue
  fi

  real_path="$entry"
  if [ -L "${entry%/}" ]; then
    real_path="$(readlink "${entry%/}")/"
  fi

  newest=$(find "$real_path" -type f -exec stat -f %m {} + 2>/dev/null | sort -rn | head -1)
  [ -z "$newest" ] && newest=0

  if [ "$newest" -ge "$D30" ]; then
    ACTIVE="${ACTIVE}, ${name}"
    ACTIVE_N=$((ACTIVE_N + 1))
  elif [ "$newest" -ge "$D90" ]; then
    RECENT_N=$((RECENT_N + 1))
  else
    STALE_N=$((STALE_N + 1))
  fi
done

echo "### Skills (${TOTAL} total)"
echo "- Active (30d): ${ACTIVE_N}${ACTIVE:+ — ${ACTIVE:2}}"
echo "- Recent (30-90d): ${RECENT_N}"
echo "- Stale (>90d): ${STALE_N}"
echo "- Broken symlinks: ${BROKEN_N}"
[ -n "$BROKEN" ] && printf "$BROKEN"
```

### Step 2: Project Pulse

Scan `~/ai_projects/` for git repo activity and CLAUDE.md presence. Cap dormant and abandoned lists at 10 names to keep output readable.

```bash
NOW=$(date +%s)
D30=$((NOW - 30*86400))
D180=$((NOW - 180*86400))
ACTIVE="" DORMANT="" ABANDONED="" DORMANT_N=0 ABANDONED_N=0 NO_CLAUDE=0
ACTIVE_N=0 GIT_TOTAL=0 DIR_TOTAL=0 NODATA=0

for dir in ~/ai_projects/*/; do
  [ -d "$dir" ] || continue
  DIR_TOTAL=$((DIR_TOTAL + 1))
  [ -d "${dir}.git" ] || continue
  GIT_TOTAL=$((GIT_TOTAL + 1))

  last_commit=$(git -C "$dir" log -1 --format=%ct 2>/dev/null)
  if [ -z "$last_commit" ]; then
    NODATA=$((NODATA + 1))
    continue
  fi

  name=$(basename "$dir")

  if [ "$last_commit" -ge "$D30" ]; then
    ACTIVE="${ACTIVE}, ${name}"
    ACTIVE_N=$((ACTIVE_N + 1))
  elif [ "$last_commit" -ge "$D180" ]; then
    DORMANT_N=$((DORMANT_N + 1))
    [ "$DORMANT_N" -le 10 ] && DORMANT="${DORMANT}, ${name}"
  else
    ABANDONED_N=$((ABANDONED_N + 1))
    [ "$ABANDONED_N" -le 10 ] && ABANDONED="${ABANDONED}, ${name}"
  fi

  [ ! -f "${dir}CLAUDE.md" ] && NO_CLAUDE=$((NO_CLAUDE + 1))
done

DORMANT_SUFFIX=""
[ "$DORMANT_N" -gt 10 ] && DORMANT_SUFFIX=" and $((DORMANT_N - 10)) more"
ABANDONED_SUFFIX=""
[ "$ABANDONED_N" -gt 10 ] && ABANDONED_SUFFIX=" and $((ABANDONED_N - 10)) more"

echo ""
echo "### Projects (${DIR_TOTAL} dirs, ${GIT_TOTAL} git repos)"
echo "- Active (30d): ${ACTIVE_N}${ACTIVE:+ — ${ACTIVE:2}}"
echo "- Dormant (30-180d): ${DORMANT_N}${DORMANT:+ — ${DORMANT:2}${DORMANT_SUFFIX}}"
echo "- Abandoned (>6mo): ${ABANDONED_N}${ABANDONED:+ — ${ABANDONED:2}${ABANDONED_SUFFIX}}"
[ "$NODATA" -gt 0 ] && echo "- No data (empty/corrupt): ${NODATA}"
echo "- Missing CLAUDE.md: ${NO_CLAUDE}"
```

### Step 3: CLAUDE.md Drift

Check if CLAUDE.md files are stale relative to their project's latest commit. Uses git commit dates (not filesystem mtime) for accuracy.

```bash
NOW=$(date +%s)
STALE_LIST="" STALE_N=0
UNTRACKED_LIST="" UNTRACKED_N=0

while IFS= read -r claude_file; do
  project_dir=$(dirname "$claude_file")
  while [ ! -d "${project_dir}/.git" ] && [ "$project_dir" != "$HOME/ai_projects" ]; do
    project_dir=$(dirname "$project_dir")
  done
  [ -d "${project_dir}/.git" ] || continue

  claude_commit=$(git -C "$project_dir" log -1 --format=%ct -- "$claude_file" 2>/dev/null)
  project_commit=$(git -C "$project_dir" log -1 --format=%ct 2>/dev/null)
  [ -z "$project_commit" ] && continue

  if [ -z "$claude_commit" ]; then
    rel_path="${claude_file#$HOME/}"
    UNTRACKED_LIST="${UNTRACKED_LIST}  - ~/${rel_path}\n"
    UNTRACKED_N=$((UNTRACKED_N + 1))
    continue
  fi

  diff=$((project_commit - claude_commit))
  if [ "$diff" -gt $((90*86400)) ]; then
    rel_path="${claude_file#$HOME/}"
    claude_date=$(date -r "$claude_commit" +%Y-%m-%d)
    project_date=$(date -r "$project_commit" +%Y-%m-%d)
    STALE_LIST="${STALE_LIST}  - ~/${rel_path} (last: ${claude_date}, project: ${project_date})\n"
    STALE_N=$((STALE_N + 1))
  fi
done < <(find ~/ai_projects -maxdepth 2 -name CLAUDE.md 2>/dev/null)

echo ""
echo "### CLAUDE.md Drift"
echo "- Stale instructions (>90d behind project): ${STALE_N}"
[ -n "$STALE_LIST" ] && printf "$STALE_LIST"
echo "- Untracked: ${UNTRACKED_N}"
[ -n "$UNTRACKED_LIST" ] && printf "$UNTRACKED_LIST"
```

### Step 4: Mac Mini Health

SSH to agents-mac-mini and check services. Uses `-T` to avoid pseudo-tty and `ECOSYS:` prefix to filter iTerm escape codes from the output.

Custom services on the Mac Mini use various prefixes (`com.server.*`, `com.telegram-agent.*`, `com.photopulse.*`, `com.health.*`, `com.temporal.*`, `ai.hermes.*`, etc.), so count all non-Apple LaunchAgents.

```bash
echo ""
echo "### Mac Mini"

MINI_OUTPUT=$(ssh -T -o ConnectTimeout=5 -o BatchMode=yes mac-mini 'export TERM=dumb; thumb=$(curl -s --max-time 3 -o /dev/null -w "%{http_code}" http://localhost:8080/ 2>/dev/null); viz=$(curl -s --max-time 3 -o /dev/null -w "%{http_code}" http://localhost:8081/ 2>/dev/null); agents=$(launchctl list 2>/dev/null | tail -n +2 | awk "{print \$3}" | grep -cv "^com\.apple" || echo 0); hdb_size=$(stat -f %z ~/ai_projects/health-import/health.db 2>/dev/null || echo 0); echo "ECOSYS:${thumb}|${viz}|${agents}|${hdb_size}"' 2>/dev/null)

DATA=$(echo "$MINI_OUTPUT" | grep "^ECOSYS:" | sed 's/^ECOSYS://')

if [ -z "$DATA" ]; then
  echo "- Status: UNREACHABLE (SSH failed)"
else
  IFS='|' read -r THUMB VIZ AGENTS HDB_SIZE <<< "$DATA"
  [ "$THUMB" = "200" ] && echo "- Thumb server (:8080): UP" || echo "- Thumb server (:8080): DOWN (${THUMB})"
  [ "$VIZ" = "200" ] && echo "- Viz server (:8081): UP" || echo "- Viz server (:8081): DOWN (${VIZ})"
  echo "- Custom LaunchAgents: ${AGENTS}"
  if [ "$HDB_SIZE" -gt 0 ] 2>/dev/null; then
    HDB_GB=$(echo "scale=1; ${HDB_SIZE}/1073741824" | bc)
    echo "- Health DB: ${HDB_GB} GB"
  else
    echo "- Health DB: NOT FOUND"
  fi
fi
```

### Step 5: Attention Summary + Daily Note

After printing the full terminal report, add an attention summary highlighting anything that needs action:

```
### Attention
- [list any: broken symlinks, services DOWN, stale CLAUDE.md, Mac Mini unreachable]
- If nothing needs attention: "All clear."
```

Then compose a summary and write it to today's daily note.

Get today's date first:

```bash
TODAY=$(date +"%Y%m%d")
```

Build the summary block from the results you collected in Steps 1-4 (re-read the terminal output above — variables don't carry across bash blocks). Format:

```markdown
## Ecosystem

Skills: N active / N recent / N stale / N broken
Projects: N active / N dormant / N abandoned
CLAUDE.md drift: N stale, N untracked
Mac Mini: [status summary]

_Ecosystem audit · YYYY-MM-DD_
```

Write to `~/Brains/brain/Daily/${TODAY}.md`:
- If `## Ecosystem` section already exists, replace everything from `## Ecosystem` to the next `##` heading (or `- - -` separator)
- If it doesn't exist, insert above the first `- - -` separator
- If any red flags (broken symlinks > 0, services down, stale CLAUDE.md > 3), prepend `> [!warning] Ecosystem issues detected`
