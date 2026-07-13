# Automation Advisor - Web Server Guide

Complete guide to using the voice-enabled web interface.

## Quick Start

```bash
cd ~/.claude/skills/automation-advisor

# Install dependencies (first time only)
pip3 install -r requirements.txt

# Start server
./start_server.sh

# Or with custom port
python3 server_web.py --port 3000
```

Open browser: **http://localhost:8080**

## Interface Overview

### Start Screen

```
🤖 Automation Advisor
───────────────────────────────────────
Data-driven automation decisions using
the Decision Matrix framework

          📊

Should you automate this task?

I'll guide you through 8 questions to
help you make a data-driven decision.
You can type or use voice input.

       [Let's Begin →]
```

### Chat Interface

**Top**: Progress bar showing completion %
**Middle**: Conversation history (your answers + assistant responses)
**Bottom**: Input area (changes based on question type)

### Question Types

**1. Multiple Choice**
- Large buttons with descriptions
- Click to select and auto-submit
- Example: "How often do you perform this task?"
  - Multiple times per day
  - Weekly
  - Monthly
  - Rarely or one-time

**2. Multiple Select**
- Checkboxes for selecting multiple options
- Click entire card or checkbox
- Submit button appears when ready
- Example: "Do any of these concerns apply?"
  - High-stakes decisions
  - Creative work
  - Learning fundamentals
  - (select all that apply)

**3. Freeform Text**
- Text area for detailed answers
- Voice button (🎤) for voice input
- Enter key to submit
- Example: "What task are you considering automating?"

## Voice Features

### Voice Input (Speech-to-Text)

**How to use**:
1. Click the purple **🎤 Voice** button
2. Start speaking (button turns red ⏹️)
3. Click **⏹️ Stop** when done
4. Text appears in input field
5. Review and submit

**Requirements**:
- Microphone permission (browser will ask)
- Groq API key configured (`GROQ_API_KEY`)
- Internet connection

**Without Groq API**:
- Recording works
- Transcription fails gracefully
- Just type instead

**Tips**:
- Speak clearly and pause briefly at end
- Review transcription before submitting
- Can edit transcription if needed
- Works best in quiet environment

### Voice Output (Text-to-Speech)

**Automatic**:
- Questions are read aloud when displayed
- Results are spoken when complete
- Uses browser's built-in TTS

**No setup needed**:
- Works in Chrome, Edge, Safari
- No API key required
- Can be muted via browser controls

**Browser Support**:
- ✅ Chrome/Edge: Full support
- ✅ Safari: Full support
- ⚠️ Firefox: Limited support
- ❌ Old browsers: Fallback to silent mode

## Progress Tracking

### Progress Bar

Shows completion from 0% to 100%:
- **0-30%**: Context gathering (What/How/Why/Consequences)
- **30-70%**: Scoring (Frequency, Time, Error Cost, Longevity)
- **70-90%**: Risk assessment (Flags, Validation)
- **90-100%**: Build estimate & completion

### Phase Labels

Current step displayed above progress bar:
- "Task identification"
- "Understanding process"
- "Pain points"
- "Risk assessment"
- "Frequency scoring"
- "Time scoring"
- "Error cost scoring"
- "Longevity scoring"
- "Risk factors"
- "Validation strategy"
- "Build estimate"
- "Complete!"

## Results Screen

### Decision Banner

```
✅ AUTOMATE NOW
       ✅

Score: 225

Score of 225 indicates high ROI.
Time investment will pay off quickly.
```

### Score Breakdown

Four cards showing individual dimension scores:
```
┌─────────┬─────────┬─────────┬─────────┐
│    3    │    5    │    5    │    3    │
│Frequency│  Time   │  Error  │Longevity│
└─────────┴─────────┴─────────┴─────────┘
```

### ASCII Visualization

Full decision tree, threshold gauge, break-even timeline, and risk matrix embedded in report.

### Action Items

**Next Steps**: Numbered action plan
- What to do first
- What to do next
- Success criteria

**Red Flags**: Warning signs to monitor
- Risk factors to watch
- When to re-evaluate

**Report Location**: Path to markdown file in Obsidian vault

### Actions

- **Analyze Another Task**: Reset and start new session
- **Download Report**: Access saved markdown file

## Multi-User Support

### Sessions

Each browser gets unique session ID:
- Tracked server-side
- Persists during runtime
- Independent progress
- Concurrent users supported

### List Sessions

API endpoint: `GET /api/sessions`

Shows all active sessions:
```json
{
  "sessions": [
    {
      "session_id": "abc-123",
      "task_name": "Invoice Generation",
      "current_phase": "score_time",
      "started": "2025-01-24T10:30:00"
    }
  ]
}
```

### Session State

API endpoint: `GET /api/session/<id>`

Returns full session state:
```json
{
  "session_id": "abc-123",
  "current_phase": "score_frequency",
  "task_data": {...},
  "conversation": [...]
}
```

## API Reference

### POST /api/start

Start new advisory session.

**Request**: `POST /api/start`
```json
{}
```

**Response**:
```json
{
  "session_id": "abc-123",
  "question": {
    "text": "What task are you considering automating?",
    "type": "freeform",
    "placeholder": "e.g., Invoice generation..."
  }
}
```

### POST /api/answer

Submit answer to current question.

**Request**: `POST /api/answer`
```json
{
  "session_id": "abc-123",
  "answer": "Invoice generation for clients"
}
```

**Response** (next question):
```json
{
  "phase": "context_how",
  "next_question": {
    "text": "Walk me through how you currently do this manually:",
    "type": "freeform",
    "placeholder": "Describe the steps..."
  }
}
```

**Response** (completion):
```json
{
  "phase": "complete",
  "score": 225,
  "decision": "AUTOMATE NOW",
  "task_name": "Invoice generation",
  "scores": {...},
  "visualization": "ASCII art...",
  "filepath": "/path/to/report.md",
  "reasoning": "Score of 225...",
  "next_steps": "1. Break down task...",
  "red_flags": "- High error cost..."
}
```

### POST /api/transcribe

Transcribe audio using Groq Whisper.

**Request**: `POST /api/transcribe`
- FormData with audio file (webm)
- session_id in form data

**Response**:
```json
{
  "text": "Invoice generation for clients"
}
```

**Error** (no Groq API):
```json
{
  "error": "Groq API not configured"
}
```

## Configuration

### Environment Variables

```bash
# Required for voice transcription
export GROQ_API_KEY="gsk_..."

# Optional: Flask secret key
export FLASK_SECRET_KEY="your-secret-key"

# Optional: Anthropic for future features
export ANTHROPIC_API_KEY="sk-ant-..."
```

### Server Options

**Port**:
```bash
python3 server_web.py --port 3000
```

**Host** (localhost only):
```bash
python3 server_web.py --host 127.0.0.1
```

**Host** (all interfaces):
```bash
python3 server_web.py --host 0.0.0.0
```

### Production Deployment

**Using Gunicorn**:
```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:8080 server_web:app
```

**Using systemd** (Linux):
```ini
[Unit]
Description=Automation Advisor Web Server
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/path/to/automation-advisor
Environment="GROQ_API_KEY=gsk_..."
ExecStart=/usr/bin/gunicorn -w 4 -b 127.0.0.1:8080 server_web:app
Restart=always

[Install]
WantedBy=multi-user.target
```

**Using nginx** (reverse proxy):
```nginx
server {
    listen 80;
    server_name automation.example.com;

    location / {
        proxy_pass http://127.0.0.1:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
```

## Troubleshooting

### "Module not found: flask"

```bash
pip3 install -r requirements.txt
```

### Voice recording not working

**Check browser permissions**:
1. Click lock icon in address bar
2. Check microphone permission
3. Allow and refresh page

**Check HTTPS** (required for mic access):
- localhost: Works without HTTPS
- Remote server: Must use HTTPS

### Transcription fails

**Check Groq API key**:
```bash
echo $GROQ_API_KEY
# Should print: gsk_...
```

**Set API key**:
```bash
export GROQ_API_KEY="gsk_..."
python3 server_web.py
```

**Fallback**: Just type your answer instead

### Voice output not working

- Check browser support (Chrome/Edge/Safari work best)
- Check browser volume/mute settings
- Try different browser
- Silent mode is fine, just read questions visually

### Port already in use

```bash
# Use different port
python3 server_web.py --port 8081

# Or find what's using port 8080
lsof -i :8080

# Kill process using port
kill -9 <PID>
```

### Session not found

- Server restarted (sessions are in-memory)
- Refresh page to start new session
- For persistent sessions, implement database storage

## Tips & Best Practices

### Voice Input

✅ **Do**:
- Speak clearly and at normal pace
- Pause briefly at end before clicking stop
- Review transcription before submitting
- Use for longer answers (saves typing)

❌ **Don't**:
- Mumble or speak too fast
- Record in noisy environment
- Rely on it for precise numbers (type those)

### Answer Quality

**Context Questions** (freeform):
- Be specific and detailed
- Include concrete examples
- Mention pain points
- Explain consequences

**Scoring Questions** (multiple choice):
- Read descriptions carefully
- Choose honestly, not aspirationally
- Consider realistic scenarios
- Don't inflate to justify automation

**Build Estimate**:
- Include learning time
- Add buffer for testing
- Consider maintenance
- Be realistic, not optimistic

### Decision Making

**Trust the framework**:
- Score < 20 = Don't automate (really!)
- Score 20-40 = Only if super easy
- Score > 40 = Good ROI

**Don't automate if**:
- You're still learning the process
- Requirements change weekly
- It's genuinely unique each time
- You enjoy doing it manually

**Do automate if**:
- High frequency + high time cost
- Error-prone when done manually
- Boring/repetitive work
- Clear, stable requirements

## Examples

### Example Session: Invoice Generation

**Q1**: What task are you considering automating?
**A1**: "Generating invoices for coaching clients"

**Q2**: How do you currently do this manually?
**A2**: "I open a template, fill in client name, dates, hours, calculate total, export PDF, email it"

**Q3**: What frustrates you most?
**A3**: "Doing the same thing every week, easy to make typos in numbers"

**Q4**: What happens if done wrong?
**A4**: "Client gets wrong amount, damages trust, delays payment"

**Q5**: How often? → **Weekly** (score: 3)
**Q6**: How long? → **30-120 minutes** (score: 3)
**Q7**: Error cost? → **Catastrophic** (score: 5)
**Q8**: Longevity? → **Years** (score: 5)

**Score**: 3 × 3 × 5 × 5 = **225**

**Decision**: ✅ **AUTOMATE NOW**

**Reasoning**: High-frequency task with significant error cost and long-term value. ROI clear.

**Next Steps**:
1. List all invoice data fields
2. Research invoice generation APIs
3. Build MVP in one session
4. Add human review step (high error cost)
5. Test with real data

**Red Flags**:
- High error cost: Add validation layer
- Review invoices before sending

### Example Session: Monthly Report

**Q1**: What task?
**A1**: "Monthly internal report for team"

**Q2**: How do you do it?
**A2**: "Pull data from 3 sources, create charts, write summary"

**Q3**: Frustration?
**A3**: "Takes 2 hours but only once a month"

**Q4**: Consequences?
**A4**: "Internal only, can fix if mistakes"

**Q5**: How often? → **Monthly** (score: 1)
**Q6**: How long? → **Hours (2+)** (score: 5)
**Q7**: Error cost? → **Negligible** (score: 1)
**Q8**: Longevity? → **Months** (score: 3)

**Score**: 1 × 5 × 1 × 3 = **15**

**Decision**: ❌ **STAY MANUAL**

**Reasoning**: Only 24 hours/year. Would take 8+ hours to automate. Not worth it.

**Next Steps**:
1. Create checklist for manual process
2. Optimize manual workflow
3. Re-evaluate in 6 months if frequency increases

## Advanced Usage

### Custom Themes

Edit `templates/index.html` to customize colors:
```javascript
// Find these classes and change colors:
bg-gradient-to-r from-blue-500 to-purple-500  // Primary gradient
bg-gray-900 via-gray-800 to-gray-900          // Background
text-blue-400                                  // Accent text
```

### Additional Features

**Export to JSON**:
Add button to download session data as JSON for external processing.

**Share Sessions**:
Add URL param with session ID to resume on different device.

**Analytics**:
Track average scores, common decisions, popular automation types.

**Templates**:
Pre-fill common automation scenarios (invoicing, reports, backups).

## Related Documentation

- [[Automation Decision Matrix]] - Core framework
- `README.md` - Technical documentation
- `QUICKSTART.md` - Quick reference
- `server_web.py` - Source code
- `templates/index.html` - Frontend code

## Support

**Issues**: Report bugs or feature requests in project repository

**Questions**: See main README or framework documentation

**Updates**: Check CHANGELOG for new features and fixes
