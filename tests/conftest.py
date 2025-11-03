"""
Pytest fixtures and mocks for Arianna Method test suite
Provides mock API clients, test database, and common utilities
"""

import pytest
import sqlite3
import tempfile
import os
from pathlib import Path
from unittest.mock import Mock, MagicMock


@pytest.fixture
def temp_db():
    """Create temporary test database"""
    with tempfile.NamedTemporaryFile(suffix='.sqlite3', delete=False) as f:
        db_path = f.name

    # Initialize with basic schema
    conn = sqlite3.connect(db_path)
    c = conn.cursor()

    # Watchdog table
    c.execute("""
        CREATE TABLE IF NOT EXISTS watchdog_actions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            webhook_name TEXT,
            action TEXT,
            success INTEGER
        )
    """)

    # Consilium table
    c.execute("""
        CREATE TABLE IF NOT EXISTS consilium_discussions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            initiator TEXT,
            topic TEXT,
            participants TEXT,
            decision TEXT
        )
    """)

    # GitHub scout table
    c.execute("""
        CREATE TABLE IF NOT EXISTS github_scout_findings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            repo_name TEXT,
            repo_url TEXT,
            description TEXT,
            stars INTEGER,
            language TEXT,
            query TEXT,
            relevance_score INTEGER
        )
    """)

    # Voice action table
    c.execute("""
        CREATE TABLE IF NOT EXISTS autonomous_actions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            trigger_phrase TEXT,
            action_type TEXT,
            command TEXT,
            success INTEGER,
            output TEXT
        )
    """)

    conn.commit()
    conn.close()

    yield db_path

    # Cleanup
    os.unlink(db_path)


@pytest.fixture
def mock_anthropic_client():
    """Mock Anthropic API client"""
    mock = MagicMock()

    # Mock messages.create response
    mock_response = Mock()
    mock_response.content = [Mock(text="Test response from Claude")]
    mock.messages.create.return_value = mock_response

    return mock


@pytest.fixture
def mock_openai_client():
    """Mock OpenAI API client"""
    mock = MagicMock()

    # Mock chat.completions.create response
    mock_response = Mock()
    mock_response.choices = [Mock(message=Mock(content="Test response from GPT"))]
    mock.chat.completions.create.return_value = mock_response

    return mock


@pytest.fixture
def mock_requests(monkeypatch):
    """Mock requests.get for webhook health checks"""
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"status": "healthy"}

    mock_get = Mock(return_value=mock_response)
    monkeypatch.setattr("requests.get", mock_get)

    return mock_get


@pytest.fixture
def mock_github_api(monkeypatch):
    """Mock GitHub API responses"""
    def mock_get(*args, **kwargs):
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "items": [
                {
                    "full_name": "test/repo",
                    "html_url": "https://github.com/test/repo",
                    "description": "Test autonomous agent repo",
                    "stargazers_count": 1000,
                    "language": "Python",
                    "updated_at": "2025-01-01T00:00:00Z"
                }
            ]
        }
        return mock_response

    monkeypatch.setattr("requests.get", mock_get)
    return mock_get


@pytest.fixture
def temp_logs_dir():
    """Create temporary logs directory"""
    with tempfile.TemporaryDirectory() as tmpdir:
        logs_dir = Path(tmpdir) / "logs"
        logs_dir.mkdir()
        yield logs_dir


@pytest.fixture
def mock_subprocess(monkeypatch):
    """Mock subprocess.run for command execution"""
    mock_run = Mock()
    mock_run.return_value = Mock(returncode=0, stdout="Command executed", stderr="")
    monkeypatch.setattr("subprocess.run", mock_run)
    return mock_run


@pytest.fixture(autouse=True)
def mock_env_vars(monkeypatch):
    """Mock environment variables (API keys)"""
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-anthropic-key")
    monkeypatch.setenv("OPENAI_API_KEY", "test-openai-key")
    monkeypatch.setenv("PERPLEXITY_API_KEY", "test-perplexity-key")
    monkeypatch.setenv("GITHUB_TOKEN", "test-github-token")
