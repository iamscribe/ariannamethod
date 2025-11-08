-- Resonance SQLite Schema - Full Reconstruction
-- Based on .schema output from broken database

PRAGMA foreign_keys=OFF;

-- Core resonance memory table
CREATE TABLE resonance_notes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    content TEXT NOT NULL,
    context TEXT,
    source TEXT DEFAULT 'scribe'
);

-- Monday's echo log
CREATE TABLE echo_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ts TEXT NOT NULL,
    user_quote TEXT,
    tone TEXT,
    internal_reaction TEXT,
    response TEXT
);

-- Monday's haikus
CREATE TABLE haikus (
    date TEXT PRIMARY KEY,
    haiku TEXT,
    context TEXT
);

-- Field state tracking
CREATE TABLE field_state (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    iteration INTEGER,
    cell_count INTEGER,
    avg_resonance REAL,
    avg_age REAL,
    births INTEGER,
    deaths INTEGER
);

-- Field cells
CREATE TABLE field_cells (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    cell_id TEXT,
    age INTEGER,
    resonance_score REAL,
    entropy REAL,
    perplexity REAL,
    fitness REAL,
    architecture TEXT,
    status TEXT,
    context TEXT
);

-- Monday assistants tracking
CREATE TABLE monday_assistants (
    id INTEGER PRIMARY KEY,
    assistant_id TEXT,
    created_at TEXT
);

-- Consilium discussions
CREATE TABLE consilium_discussions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    repo TEXT NOT NULL,
    initiator TEXT NOT NULL,
    message TEXT NOT NULL,
    agent_name TEXT,
    response_to_id INTEGER,
    FOREIGN KEY (response_to_id) REFERENCES consilium_discussions(id)
);

-- Claude Defender conversations
CREATE TABLE claude_defender_conversations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    role TEXT NOT NULL,
    content TEXT NOT NULL,
    session_id TEXT,
    source TEXT DEFAULT 'voice_webhook'
);

CREATE INDEX idx_claude_conversations_timestamp
    ON claude_defender_conversations(timestamp DESC);

-- Autonomous actions log
CREATE TABLE autonomous_actions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    trigger_type TEXT,
    trigger_content TEXT,
    action_taken TEXT,
    result TEXT,
    status TEXT,
    execution_time_ms INTEGER
);

-- Fortification logs
CREATE TABLE fortification_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    assessment_type TEXT,
    findings TEXT,
    improvements_proposed TEXT,
    improvements_implemented TEXT,
    consilium_insights TEXT,
    status TEXT,
    duration_ms INTEGER
);

-- Boot logs
CREATE TABLE boot_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    component TEXT,
    start_status TEXT,
    pid INTEGER,
    error_message TEXT,
    retry_count INTEGER DEFAULT 0
);

-- Suppertime events
CREATE TABLE suppertime_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    event_type TEXT NOT NULL,
    chapter_num INTEGER,
    hero_name TEXT,
    content TEXT,
    metadata TEXT,
    field_notified BOOLEAN DEFAULT 0,
    field_response TEXT
);

-- Screenshot captures
CREATE TABLE screenshot_captures (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    filename TEXT NOT NULL,
    description TEXT,
    context TEXT,
    raw_analysis TEXT
);

-- GitHub scout findings
CREATE TABLE github_scout_findings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT,
    repo_name TEXT,
    repo_url TEXT,
    description TEXT,
    stars INTEGER,
    language TEXT,
    query TEXT,
    relevance_score INTEGER
);

-- Field metrics
CREATE TABLE field_metrics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ts TEXT,
    iteration INTEGER,
    pop INTEGER,
    avg_res REAL,
    avg_age REAL,
    births INTEGER,
    deaths INTEGER,
    novelty REAL,
    niches INTEGER
);

-- Watchdog actions
CREATE TABLE watchdog_actions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    webhook_name TEXT NOT NULL,
    action TEXT NOT NULL,
    status TEXT NOT NULL
);

PRAGMA foreign_keys=ON;

