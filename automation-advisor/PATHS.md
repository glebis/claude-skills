# Automation Advisor - Correct Paths

## Installation Location

The automation-advisor skill is installed in your Obsidian vault:

```bash
/Users/glebkalinin/Brains/brain/.claude/skills/automation-advisor/
```

## Quick Commands

### Navigate to skill directory
```bash
cd /Users/glebkalinin/Brains/brain/.claude/skills/automation-advisor
```

Or use relative path from vault root:
```bash
cd ~/Brains/brain/.claude/skills/automation-advisor
```

### Start web server
```bash
# From skill directory
./start_server.sh

# Or from anywhere
/Users/glebkalinin/Brains/brain/.claude/skills/automation-advisor/start_server.sh

# Or direct launch
cd ~/Brains/brain/.claude/skills/automation-advisor
python3 server_web.py --port 8080
```

### Run console version
```bash
cd ~/Brains/brain/.claude/skills/automation-advisor
python3 server.py --mode console
```

### See example visualizations
```bash
cd ~/Brains/brain/.claude/skills/automation-advisor
python3 test_demo.py
```

## Output Locations

### Markdown reports saved to
```bash
~/Brains/brain/automation-decisions/
```

Each report: `YYYYMMDD-task-slug.md`

Example: `20260124-invoice-generation.md`

## Environment Variables (Optional)

For voice transcription:
```bash
export GROQ_API_KEY="gsk_..."
```

For Flask security (production):
```bash
export FLASK_SECRET_KEY="your-secret-key"
```

## Aliases (Optional)

Add to `~/.zshrc` or `~/.bashrc`:

```bash
# Quick access to automation advisor
alias automation-advisor='cd ~/Brains/brain/.claude/skills/automation-advisor'
alias advisor-server='cd ~/Brains/brain/.claude/skills/automation-advisor && ./start_server.sh'
alias advisor-console='cd ~/Brains/brain/.claude/skills/automation-advisor && python3 server.py --mode console'
alias advisor-demo='cd ~/Brains/brain/.claude/skills/automation-advisor && python3 test_demo.py'
```

Then reload:
```bash
source ~/.zshrc
```

Usage:
```bash
automation-advisor    # Navigate to directory
advisor-server        # Start web server
advisor-console       # Run console version
advisor-demo          # See visualizations
```
