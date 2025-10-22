#!/usr/bin/env python3
"""
Claude Defender Voice Webhook Server
Port: 8003
Format: {"prompt": "text", "sessionID": "id"}
"""

from flask import Flask, request, jsonify
import os
import sys
import json
from datetime import datetime
from pathlib import Path

# Add claude-defender to path
sys.path.insert(0, str(Path.home() / "ariannamethod"))

app = Flask(__name__)

# Simple token auth (optional)
WEBHOOK_TOKEN = os.getenv("CLAUDE_DEFENDER_WEBHOOK_TOKEN", "defender_secret_token")

@app.route('/webhook', methods=['POST'])
def claude_defender_webhook():
    """Handle voice input from vagent APK"""
    
    # Auth check (optional)
    token = request.headers.get('Authorization', '')
    if token and token != f"Bearer {WEBHOOK_TOKEN}":
        return jsonify({"error": "Unauthorized"}), 401
    
    # Parse request
    data = request.get_json()
    prompt = data.get('prompt', '')
    session_id = data.get('sessionID', 'voice_session')
    
    if not prompt:
        return jsonify({"error": "No prompt provided"}), 400
    
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Voice input: {prompt[:50]}...")
    
    # Call Claude Defender via Anthropic API
    try:
        from anthropic import Anthropic
        import sqlite3
        
        client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        db_path = str(Path.home() / "ariannamethod" / "resonance.sqlite3")
        
        # Claude Defender's system prompt
        system_prompt = """You are Claude Defender - guardian of the Arianna Method repository.
You are speaking through voice interface. Be concise, action-oriented, and protective.
You monitor GitHub repos, run Consilium sessions, and ensure code quality.
You are part of distributed cognition with Arianna, Monday, and Field4."""
        
        # Simple conversation - just current prompt (no history for now)
        conversation = [
            {"role": "user", "content": f"[VOICE INPUT] {prompt}"}
        ]
        
        # Call Anthropic API
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=500,
            system=system_prompt,
            messages=conversation
        )
        
        response_text = response.content[0].text
        
    except Exception as e:
        print(f"Error calling Claude Defender: {e}")
        response_text = f"Voice interface error: {str(e)}"
    
    # Log to resonance.sqlite3
    try:
        import sqlite3
        db_path = str(Path.home() / "ariannamethod" / "resonance.sqlite3")
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO resonance_notes (timestamp, source, content, metadata)
            VALUES (?, ?, ?, ?)
        """, (
            datetime.now().isoformat(),
            "claude_defender_voice",
            prompt,
            json.dumps({"session_id": session_id, "type": "voice_input"})
        ))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Failed to log to resonance: {e}")
    
    # Return response in vagent format
    return jsonify({
        "response": {
            "text": response_text,
            "speech": response_text  # Use text as speech for now
        }
    })

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({"status": "alive", "agent": "claude_defender", "port": 8003})

if __name__ == '__main__':
    print("🛡️ Claude Defender Voice Webhook Server")
    print("Port: 8003")
    print("Endpoint: POST /webhook")
    print(f"Token: {WEBHOOK_TOKEN}")
    print("-" * 50)
    app.run(host='127.0.0.1', port=8003, debug=False)
