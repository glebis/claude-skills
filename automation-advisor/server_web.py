#!/usr/bin/env python3
"""
Automation Advisor - Web Server

Voice-enabled web interface using:
- Flask for web server
- Groq Whisper for speech-to-text
- Web Speech API for text-to-speech (browser-native)
- Real-time interaction via Server-Sent Events

Usage:
    python server_web.py --port 8080
"""

import asyncio
import json
import os
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional
import threading
from queue import Queue
import tempfile

from flask import Flask, render_template, request, jsonify, Response, session, send_file
from flask_cors import CORS

# Import core advisor
import sys
sys.path.append(str(Path(__file__).parent))
from server import AutomationAdvisor
from visualize import generate_full_report_visualization

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "automation-advisor-secret-key")
CORS(app)

# TTS cache directory
TTS_CACHE_DIR = Path(tempfile.gettempdir()) / "automation-advisor-tts"
TTS_CACHE_DIR.mkdir(exist_ok=True)

# Store active sessions
sessions: Dict[str, Dict] = {}


class WebAdvisorSession:
    """Manages a single user's automation advisory session"""

    def __init__(self, session_id: str):
        self.session_id = session_id
        self.advisor = AutomationAdvisor()
        self.current_phase = "start"
        self.message_queue = Queue()
        self.conversation = []

    def add_message(self, role: str, content: str, data: Optional[Dict] = None):
        """Add message to conversation"""
        msg = {
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat(),
            "data": data or {}
        }
        self.conversation.append(msg)
        self.message_queue.put(msg)

    def get_question_number(self) -> tuple[int, int]:
        """Get current question number and total questions"""
        phase_order = [
            "start",
            "context_how",
            "context_frustration",
            "context_consequences",
            "score_frequency",
            "score_time",
            "score_error",
            "score_longevity"
        ]

        if self.current_phase in phase_order:
            question_num = phase_order.index(self.current_phase) + 1
            total = len(phase_order)
            return (question_num, total)
        else:
            # For override_flags, validation_pattern, build_estimate - show as complete
            return (8, 8)

    def get_next_question(self) -> Optional[Dict]:
        """Get next question based on current phase"""
        questions = {
            "start": {
                "text": "What task are you considering automating?",
                "type": "freeform",
                "placeholder": "e.g., Invoice generation, client onboarding, report creation..."
            },
            "context_how": {
                "text": "Walk me through how you currently do this manually:",
                "type": "freeform",
                "placeholder": "Describe the steps you take..."
            },
            "context_frustration": {
                "text": "What frustrates you most about this task?",
                "type": "freeform",
                "placeholder": "What's the most annoying part?"
            },
            "context_consequences": {
                "text": "What happens if this task isn't done, or is done incorrectly?",
                "type": "freeform",
                "placeholder": "What are the consequences?"
            },
            "score_frequency": {
                "text": "How often do you perform this task?",
                "type": "multiple_choice",
                "options": [
                    {"value": 5, "label": "Multiple times per day", "description": "Daily recurring task"},
                    {"value": 3, "label": "Weekly", "description": "Several times per month"},
                    {"value": 1, "label": "Monthly", "description": "Once or twice per month"},
                    {"value": 0, "label": "Rarely or one-time", "description": "Yearly or unique situation"}
                ]
            },
            "score_time": {
                "text": "How long does this task take each time you do it manually?",
                "type": "multiple_choice",
                "options": [
                    {"value": 5, "label": "Hours (2+)", "description": "Significant time investment"},
                    {"value": 3, "label": "30-120 minutes", "description": "Medium duration"},
                    {"value": 1, "label": "5-30 minutes", "description": "Quick task, adds up"},
                    {"value": 0, "label": "Under 5 minutes", "description": "Already fast"}
                ]
            },
            "score_error": {
                "text": "What happens if automation breaks or makes a mistake?",
                "type": "multiple_choice",
                "options": [
                    {"value": 5, "label": "Catastrophic", "description": "Legal liability, customer loss, revenue impact"},
                    {"value": 3, "label": "Annoying", "description": "Delays work, requires manual intervention"},
                    {"value": 1, "label": "Negligible", "description": "Easy to catch and fix"}
                ]
            },
            "score_longevity": {
                "text": "How long will you continue doing this task?",
                "type": "multiple_choice",
                "options": [
                    {"value": 5, "label": "Years", "description": "Core business process, ongoing"},
                    {"value": 3, "label": "Months", "description": "Project-specific, medium-term"},
                    {"value": 1, "label": "Weeks", "description": "Temporary situation"},
                    {"value": 0, "label": "One-time", "description": "Single use, won't repeat"}
                ]
            },
            "override_flags": {
                "text": "Do any of these concerns apply to your automation?",
                "type": "multiple_select",
                "options": [
                    {"value": "high-stakes", "label": "High-stakes decisions without validation"},
                    {"value": "creative", "label": "Creative work where authentic voice matters"},
                    {"value": "learning", "label": "Learning fundamentals you need to understand"},
                    {"value": "regulated", "label": "Regulated industry (HIPAA, GDPR, SOX)"},
                    {"value": "bus-factor", "label": "Single point of failure risk (bus factor = 1)"},
                    {"value": "changing", "label": "Rapidly changing requirements"},
                    {"value": "unique", "label": "Genuinely unique each time"}
                ]
            },
            "validation_pattern": {
                "text": "Which validation pattern fits your automation?",
                "type": "multiple_choice",
                "options": [
                    {"value": "human-in-loop", "label": "Human-in-the-Loop", "description": "AI generates → You review → Approve → Execute (safest)"},
                    {"value": "confidence", "label": "Confidence Threshold", "description": "High confidence = auto, low = review"},
                    {"value": "audit", "label": "Audit Trail", "description": "AI logs → Periodic spot-checks"},
                    {"value": "staged", "label": "Staged Rollout", "description": "Shadow → Assisted → Monitored → Auto"},
                    {"value": "none", "label": "No validation needed", "description": "Low stakes, auto-execute"}
                ]
            },
            "build_estimate": {
                "text": "How many hours do you think it would take to build this automation?",
                "type": "freeform",
                "placeholder": "e.g., 8",
                "input_type": "number"
            }
        }

        question = questions.get(self.current_phase)
        if question:
            question_num, total = self.get_question_number()
            question["question_number"] = question_num
            question["total_questions"] = total
        return question

    def process_answer(self, answer: any) -> Dict:
        """Process user answer and move to next phase"""
        phase = self.current_phase

        # Store answer based on phase
        if phase == "start":
            self.advisor.task_data["task_name"] = answer
            self.current_phase = "context_how"
            context_parts = [f"Task: {answer}"]
            self.advisor.task_data["context"] = "\n".join(context_parts)

        elif phase == "context_how":
            self.advisor.task_data["context"] += f"\n\nHow it's done: {answer}"
            self.current_phase = "context_frustration"

        elif phase == "context_frustration":
            self.advisor.task_data["context"] += f"\n\nFrustrations: {answer}"
            self.current_phase = "context_consequences"

        elif phase == "context_consequences":
            self.advisor.task_data["context"] += f"\n\nConsequences: {answer}"
            self.current_phase = "score_frequency"

        elif phase == "score_frequency":
            if not answer or not answer.strip():
                raise ValueError("Please provide a frequency score")
            self.advisor.task_data["scores"]["frequency"] = int(answer)
            self.current_phase = "score_time"

        elif phase == "score_time":
            if not answer or not answer.strip():
                raise ValueError("Please provide a time score")
            self.advisor.task_data["scores"]["time"] = int(answer)
            self.current_phase = "score_error"

        elif phase == "score_error":
            if not answer or not answer.strip():
                raise ValueError("Please provide an error cost score")
            self.advisor.task_data["scores"]["error_cost"] = int(answer)
            self.current_phase = "score_longevity"

        elif phase == "score_longevity":
            if not answer or not answer.strip():
                raise ValueError("Please provide a longevity score")
            self.advisor.task_data["scores"]["longevity"] = int(answer)
            # Calculate score and show results
            score = self.advisor.calculate_score()
            decision = self.advisor.get_decision(score)

            # Check if we need validation pattern
            if self.advisor.task_data["scores"]["error_cost"] >= 3:
                self.current_phase = "override_flags"
            else:
                self.current_phase = "override_flags"  # Still ask override flags

            return {
                "phase": "score_results",
                "score": score,
                "decision": decision,
                "next_question": self.get_next_question()
            }

        elif phase == "override_flags":
            # answer is list of selected flags
            flag_map = {
                "high-stakes": "High-stakes without validation",
                "creative": "Creative work needing authentic voice",
                "learning": "Learning fundamentals",
                "regulated": "Regulated industry",
                "bus-factor": "Single point of failure",
                "changing": "Rapidly changing requirements",
                "unique": "Unique each time"
            }
            self.advisor.task_data["override_flags"] = [flag_map[f] for f in answer if f in flag_map]

            # Check if validation needed
            if (self.advisor.task_data["scores"]["error_cost"] >= 3 or
                self.advisor.task_data["override_flags"]):
                self.current_phase = "validation_pattern"
            else:
                self.current_phase = "build_estimate"

        elif phase == "validation_pattern":
            pattern_map = {
                "human-in-loop": "Human-in-the-Loop",
                "confidence": "Confidence Threshold",
                "audit": "Audit Trail",
                "staged": "Staged Rollout",
                "none": None
            }
            self.advisor.task_data["validation_pattern"] = pattern_map.get(answer)
            self.current_phase = "build_estimate"

        elif phase == "build_estimate":
            self.advisor.task_data["build_estimate"] = float(answer)
            self.current_phase = "complete"

            # Generate final report
            return self.generate_final_report()

        return {"phase": self.current_phase, "next_question": self.get_next_question()}

    def generate_final_report(self) -> Dict:
        """Generate final recommendation and markdown report"""
        score = self.advisor.calculate_score()
        decision = self.advisor.get_decision(score)

        # Generate markdown file
        filepath = self.advisor.generate_markdown_report()

        # Generate visualization
        visualization = generate_full_report_visualization(self.advisor.task_data)

        return {
            "phase": "complete",
            "score": score,
            "decision": decision,
            "task_name": self.advisor.task_data["task_name"],
            "scores": self.advisor.task_data["scores"],
            "override_flags": self.advisor.task_data["override_flags"],
            "validation_pattern": self.advisor.task_data["validation_pattern"],
            "build_estimate": self.advisor.task_data["build_estimate"],
            "visualization": visualization,
            "filepath": filepath,
            "reasoning": self.advisor._get_decision_reasoning(score, decision),
            "next_steps": self.advisor._generate_next_steps(decision, score),
            "red_flags": self.advisor._generate_red_flags()
        }


@app.route('/')
def index():
    """Serve main application page"""
    return render_template('index.html')


@app.route('/api/start', methods=['POST'])
def start_session():
    """Start a new advisory session"""
    session_id = str(uuid.uuid4())
    web_session = WebAdvisorSession(session_id)
    sessions[session_id] = web_session

    session['session_id'] = session_id

    return jsonify({
        "session_id": session_id,
        "question": web_session.get_next_question()
    })


@app.route('/api/answer', methods=['POST'])
def submit_answer():
    """Submit answer and get next question"""
    data = request.json
    session_id = data.get('session_id') or session.get('session_id')

    if not session_id or session_id not in sessions:
        return jsonify({"error": "Invalid session"}), 400

    web_session = sessions[session_id]
    answer = data.get('answer')

    # Process answer
    result = web_session.process_answer(answer)

    # Add to conversation
    web_session.add_message("user", str(answer))

    return jsonify(result)


@app.route('/api/transcribe', methods=['POST'])
def transcribe_audio():
    """Transcribe audio using Groq Whisper"""
    if 'audio' not in request.files:
        return jsonify({"error": "No audio file"}), 400

    audio_file = request.files['audio']

    # Check if Groq is available
    session_id = request.form.get('session_id') or session.get('session_id')
    if not session_id or session_id not in sessions:
        return jsonify({"error": "Invalid session"}), 400

    web_session = sessions[session_id]

    if not web_session.advisor.groq:
        return jsonify({"error": "Groq API not configured"}), 400

    try:
        # Save temp file
        temp_path = f"/tmp/audio_{session_id}.webm"
        audio_file.save(temp_path)

        # Transcribe with Groq Whisper
        with open(temp_path, "rb") as f:
            transcription = web_session.advisor.groq.audio.transcriptions.create(
                file=f,
                model="whisper-large-v3",
                response_format="json"
            )

        # Cleanup
        os.remove(temp_path)

        return jsonify({
            "text": transcription.text
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/synthesize', methods=['POST'])
def synthesize_speech():
    """Synthesize speech using Groq TTS (Orpheus)"""
    data = request.json
    text = data.get('text')

    if not text:
        return jsonify({"error": "No text provided"}), 400

    # Check if Groq is available
    session_id = data.get('session_id') or session.get('session_id')
    if not session_id or session_id not in sessions:
        return jsonify({"error": "Invalid session"}), 400

    web_session = sessions[session_id]

    if not web_session.advisor.groq:
        return jsonify({"error": "Groq API not configured"}), 400

    try:
        # Generate unique filename
        audio_id = str(uuid.uuid4())[:8]
        audio_path = TTS_CACHE_DIR / f"tts_{audio_id}.wav"

        # Synthesize speech with Groq Orpheus
        response = web_session.advisor.groq.audio.speech.create(
            model="canopylabs/orpheus-v1-english",
            voice="autumn",  # Options: autumn, winter, spring, summer
            response_format="wav",
            input=text
        )

        # Save to file
        with open(audio_path, 'wb') as f:
            # BinaryAPIResponse is iterable
            for chunk in response.iter_bytes():
                f.write(chunk)

        # Return audio URL
        return jsonify({
            "audio_url": f"/api/audio/{audio_id}"
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/audio/<audio_id>')
def serve_audio(audio_id):
    """Serve generated TTS audio file"""
    audio_path = TTS_CACHE_DIR / f"tts_{audio_id}.wav"

    if not audio_path.exists():
        return jsonify({"error": "Audio file not found"}), 404

    return send_file(
        audio_path,
        mimetype='audio/wav',
        as_attachment=False,
        download_name=f'speech_{audio_id}.wav'
    )


@app.route('/api/session/<session_id>')
def get_session(session_id):
    """Get current session state"""
    if session_id not in sessions:
        return jsonify({"error": "Session not found"}), 404

    web_session = sessions[session_id]

    return jsonify({
        "session_id": session_id,
        "current_phase": web_session.current_phase,
        "task_data": web_session.advisor.task_data,
        "conversation": web_session.conversation
    })


@app.route('/api/sessions')
def list_sessions():
    """List all active sessions"""
    return jsonify({
        "sessions": [
            {
                "session_id": sid,
                "task_name": web_session.advisor.task_data.get("task_name", "Unnamed"),
                "current_phase": web_session.current_phase,
                "started": web_session.conversation[0]["timestamp"] if web_session.conversation else None
            }
            for sid, web_session in sessions.items()
        ]
    })


def run_server(host='0.0.0.0', port=8080):
    """Run the Flask server"""
    print(f"""
╔══════════════════════════════════════════════════════════╗
║     AUTOMATION ADVISOR - WEB SERVER                      ║
╠══════════════════════════════════════════════════════════╣
║                                                          ║
║  Server running at: http://localhost:{port}             ║
║                                                          ║
║  Features:                                               ║
║  ✅ Web interface                                        ║
║  ✅ Voice input (Groq Whisper)                           ║
║  ✅ Voice output (Browser TTS)                           ║
║  ✅ Real-time interaction                                ║
║  ✅ Multi-user sessions                                  ║
║                                                          ║
║  Press Ctrl+C to stop                                    ║
║                                                          ║
╚══════════════════════════════════════════════════════════╝
""")

    app.run(host=host, port=port, debug=False)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Automation Advisor Web Server")
    parser.add_argument("--port", type=int, default=8080, help="Port to run server on")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind to")

    args = parser.parse_args()

    run_server(host=args.host, port=args.port)
