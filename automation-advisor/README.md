# Automation Advisor Skill

Interactive decision framework for evaluating automation opportunities using the **Automation Decision Matrix**.

## Overview

Helps you make data-driven decisions about whether to automate a task by:
- Gathering context through conversational questions
- Scoring four dimensions (Frequency, Time, Error Cost, Longevity)
- Calculating automation score and ROI
- Identifying risk factors and validation needs
- Generating comprehensive Obsidian-formatted analysis
- Creating visual decision diagrams

## Usage

### Method 1: Claude Code Skill (Recommended)

```bash
# From your Obsidian vault
claude /automation-advisor
```

Claude will guide you through an interactive questionnaire using AskUserQuestion.

### Method 2: Standalone Console Interface

```bash
# Direct Python execution
cd ~/.claude/skills/automation-advisor
python server.py --mode console
```

### Method 3: Web Server (Voice-Enabled)

```bash
# Quick start
./start_server.sh

# Or specify port
./start_server.sh 3000

# Or direct launch
python server.py --mode server --port 8080

# Or launch web server directly
python server_web.py --port 8080 --host 0.0.0.0
```

**Then open**: http://localhost:8080

Features:
- ✅ Modern web interface with dark theme
- ✅ Voice input via Groq Whisper STT
- ✅ Voice output via Web Speech API (browser TTS)
- ✅ Real-time progress tracking
- ✅ Visual ASCII diagrams embedded
- ✅ Multi-user sessions (concurrent users)
- ✅ Mobile-friendly responsive design

## How It Works

### Phase 1: Context Gathering (Freeform)
- "What task are you considering?"
- "How do you currently do this?"
- "What frustrates you most?"
- "What happens if it's done wrong?"

### Phase 2: Structured Scoring
Four dimensions scored 0-5:
- **Frequency**: How often you do this (daily=5, yearly=0)
- **Time**: How long it takes (hours=5, minutes=0)
- **Error Cost**: Impact of mistakes (catastrophic=5, negligible=1)
- **Longevity**: How long you'll do it (years=5, one-time=0)

**Formula**: `Score = Frequency × Time × Error Cost × Longevity`

### Phase 3: Decision Thresholds
- **Score > 40**: AUTOMATE NOW (high ROI)
- **Score 20-40**: AUTOMATE IF EASY (< 4 hours to build)
- **Score < 20**: STAY MANUAL (not worth effort)

### Phase 4: Override Checks
Seven risk factors that may override high scores:
1. High-stakes without validation
2. Creative work needing authentic voice
3. Learning fundamentals
4. Regulated industry (HIPAA, GDPR, SOX)
5. Single point of failure
6. Rapidly changing requirements
7. Genuinely unique each time

### Phase 5: Validation Patterns (If Needed)
For high-stakes automation:
- **Human-in-the-Loop**: AI generates → You review → Approve → Execute
- **Confidence Threshold**: Auto-execute when confident, human review when uncertain
- **Audit Trail**: AI logs everything, periodic spot-checks
- **Staged Rollout**: Shadow → Assisted → Monitored → Auto

### Phase 6: Break-Even Analysis
Calculates:
- Build time investment
- Time saved per week
- Break-even point (weeks)
- ROI after 1 year

### Phase 7: Final Recommendation
Synthesized decision with:
- Clear recommendation (Automate/Maybe/Don't)
- Reasoning based on data
- Next steps
- Red flags to monitor

### Phase 8: Output Generation
Creates:
1. **Markdown Report**: Comprehensive analysis in `automation-decisions/YYYYMMDD-task-slug.md`
2. **Visualization**: Decision diagram (coming soon)

## Output Structure

```markdown
---
type: automation-decision
task: "Task Name"
date: "[[YYYYMMDD]]"
decision: "AUTOMATE NOW"
score: 225
tags:
  - automation
  - decision
---

# Automation Decision: Task Name

## Context
[Your task description and context]

## Scoring
[4-dimension breakdown with explanations]

## Decision: AUTOMATE NOW
[Clear reasoning]

## Break-Even Analysis
[Time/cost calculations]

## Override Considerations
[Risk factors and mitigations]

## Validation Pattern
[If needed]

## Implementation Plan
[Actionable next steps]

## Related
- [[Automation Decision Matrix]]
```

## Examples

### Example 1: Invoice Generation
- **Score**: 225 (3×3×5×5)
- **Decision**: AUTOMATE NOW
- **Reasoning**: Weekly task, high error cost, ongoing business need
- **Validation**: Human-in-the-Loop (review before sending)

### Example 2: Monthly Report
- **Score**: 15 (1×5×1×3)
- **Decision**: STAY MANUAL
- **Reasoning**: Only 24 hours/year, automation overhead not justified

### Example 3: Client Onboarding
- **Score**: 625 (5×5×5×5)
- **Decision**: AUTOMATE YESTERDAY
- **Reasoning**: 260 hours/year saved, ROI in 2 months

## Installation

### Requirements

```bash
pip install anthropic groq httpx
```

### Environment Variables

```bash
export ANTHROPIC_API_KEY="your-key"
export GROQ_API_KEY="your-key"  # Optional, for voice features
```

### Obsidian Setup

1. Ensure vault path is correct in `server.py`:
   ```python
   VAULT_PATH = Path("/Users/glebkalinin/Brains/brain")
   ```

2. Create decisions folder:
   ```bash
   mkdir -p ~/Brains/brain/automation-decisions
   ```

3. Install Claude Code skill:
   ```bash
   # Skill is in .claude/skills/automation-advisor/
   # Accessible via /automation-advisor command
   ```

## Architecture

```
automation-advisor/
├── skill.yaml           # Claude Code skill definition
├── prompt.md           # Interactive prompt logic
├── server.py           # Standalone Python implementation
├── README.md           # This file
└── requirements.txt    # Python dependencies
```

### Two Implementations

1. **Claude Code Skill** (`prompt.md`)
   - Uses Claude's AskUserQuestion tool
   - Integrated with vault
   - Best UX for Claude Code users

2. **Standalone Server** (`server.py`)
   - Python-based implementation
   - Can run independently
   - Voice interface via Groq
   - Web UI (coming soon)

Both generate identical markdown output in Obsidian vault.

## Web Server Interface

### Features

**Modern UI**
- Dark theme with gradient accents
- Responsive design (works on mobile)
- Real-time progress bar
- Smooth animations and transitions

**Voice Capabilities**
- **Input**: Click microphone button to record voice answer
- **Output**: Questions are read aloud automatically
- **Transcription**: Groq Whisper converts speech to text
- **TTS**: Browser's Web Speech API reads responses

**Session Management**
- Multiple concurrent users supported
- Each session tracks its own progress
- Sessions persist during server runtime

**Visual Feedback**
- Progress bar shows completion (0-100%)
- Phase labels ("Frequency scoring", "Risk assessment", etc.)
- Real-time chat-style conversation history
- ASCII visualizations in final report

### API Endpoints

```
POST   /api/start                  - Start new session
POST   /api/answer                 - Submit answer
POST   /api/transcribe             - Transcribe audio (Groq Whisper)
GET    /api/session/<id>           - Get session state
GET    /api/sessions               - List active sessions
```

### Voice Setup

**For Voice Input (Optional)**:
```bash
export GROQ_API_KEY="your-groq-api-key"
```

Without Groq API key:
- Voice recording still works
- Transcription will fail gracefully
- Users can type instead

**For Voice Output**:
- Uses browser's built-in Web Speech API
- No API key needed
- Works in Chrome, Edge, Safari
- Questions are read aloud automatically

### Customization

**Change Port**:
```bash
python server_web.py --port 3000
```

**Bind to Localhost Only** (more secure):
```bash
python server_web.py --host 127.0.0.1 --port 8080
```

**Custom Secret Key**:
```bash
export FLASK_SECRET_KEY="your-secret-key"
python server_web.py
```

### Production Deployment

For production use, run with a WSGI server:

```bash
# Install gunicorn
pip install gunicorn

# Run with gunicorn (4 workers)
gunicorn -w 4 -b 0.0.0.0:8080 server_web:app
```

Or use nginx as reverse proxy:
```nginx
server {
    listen 80;
    server_name automation-advisor.example.com;

    location / {
        proxy_pass http://127.0.0.1:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

## Roadmap

### v1.0 (Current)
- [x] Core decision framework
- [x] Console interface
- [x] Markdown report generation
- [x] ASCII art visualizations
- [x] Web server interface
- [x] Voice input/output via Groq + Web Speech

### v1.1 (In Progress)
- [ ] Claude Code skill integration (`/automation-advisor`)
- [ ] Historical decision tracking
- [ ] Multi-language support (Spanish, German, French)
- [ ] Export to PDF/image

### v1.2 (Future)
- [ ] ROI validation dashboard (did automation pay off?)
- [ ] Template library for common automations
- [ ] Integration with Claude Code lab curriculum
- [ ] Slack/Discord bot interface
- [ ] Team collaboration features

## Related

- [[Automation Decision Matrix]] - Core framework
- [[Claude Code Lab 02]] - Workshop using this skill
- [[20260121-claude-code-lab-concrete-sessions]] - Session design

## Contributing

Improvements welcome! Key areas:
- Visualization generation
- Voice interface implementation
- Additional validation patterns
- More real-world examples

## License

MIT
