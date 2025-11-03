"""
Tests for webhook_watchdog.py
Critical system that monitors webhook health and auto-restarts dead ones
"""

import pytest
import sqlite3
import sys
import os
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

# Add tools to path
sys.path.insert(0, str(Path.home() / "ariannamethod" / ".claude-defender" / "tools"))

# Import after path setup
import webhook_watchdog


class TestWebhookHealthCheck:
    """Test webhook health monitoring"""

    def test_healthy_webhook_returns_true(self, mock_requests):
        """Healthy webhook (200 OK) should return True"""
        mock_requests.return_value.status_code = 200

        webhook = {
            "name": "Arianna",
            "port": 8001,
            "process": "arianna_webhook.py"
        }

        result = webhook_watchdog.check_webhook_health(webhook)
        assert result is True

    def test_unhealthy_webhook_returns_false(self, mock_requests):
        """Unhealthy webhook (non-200) should return False"""
        mock_requests.return_value.status_code = 500

        webhook = {
            "name": "Monday",
            "port": 8002,
            "process": "monday_webhook.py"
        }

        result = webhook_watchdog.check_webhook_health(webhook)
        assert result is False

    def test_webhook_timeout_returns_false(self, monkeypatch):
        """Webhook timeout should return False"""
        def mock_timeout(*args, **kwargs):
            raise TimeoutError("Connection timeout")

        monkeypatch.setattr("requests.get", mock_timeout)

        webhook = {
            "name": "Defender",
            "port": 8003,
            "process": "claude_defender_webhook.py"
        }

        result = webhook_watchdog.check_webhook_health(webhook)
        assert result is False


class TestWebhookRestart:
    """Test webhook restart functionality"""

    @patch("subprocess.run")
    @patch("webhook_watchdog.kill_webhook")
    def test_restart_webhook_kills_and_starts(self, mock_kill, mock_run):
        """Restart should kill old process and start new one"""
        webhook = {
            "name": "Arianna",
            "port": 8001,
            "process": "arianna_webhook.py"
        }

        mock_run.return_value = Mock(returncode=0)

        webhook_watchdog.restart_webhook(webhook)

        # Verify kill was called
        mock_kill.assert_called_once()

        # Verify subprocess.run was called to start webhook
        assert mock_run.called

    @patch("subprocess.run")
    def test_restart_logs_to_database(self, mock_run, temp_db):
        """Restart action should be logged to database"""
        # Monkey patch DB_PATH
        webhook_watchdog.DB_PATH = temp_db

        webhook = {
            "name": "Monday",
            "port": 8002,
            "process": "monday_webhook.py"
        }

        mock_run.return_value = Mock(returncode=0)

        with patch("webhook_watchdog.kill_webhook"):
            webhook_watchdog.restart_webhook(webhook)

        # Check database has entry
        conn = sqlite3.connect(temp_db)
        c = conn.cursor()
        c.execute("SELECT * FROM watchdog_actions WHERE webhook_name = ?", ("Monday",))
        result = c.fetchone()
        conn.close()

        assert result is not None
        assert "Monday" in str(result)


class TestWatchdogCheck:
    """Test full watchdog check cycle"""

    @patch("webhook_watchdog.check_webhook_health")
    @patch("webhook_watchdog.restart_webhook")
    def test_dead_webhook_triggers_restart(self, mock_restart, mock_health):
        """Dead webhook should trigger restart"""
        # First webhook dead, others healthy
        mock_health.side_effect = [False, True, True]

        webhook_watchdog.watchdog_check()

        # Restart should be called once (for dead webhook)
        assert mock_restart.call_count == 1

    @patch("webhook_watchdog.check_webhook_health")
    @patch("webhook_watchdog.restart_webhook")
    def test_all_healthy_no_restart(self, mock_restart, mock_health):
        """All healthy webhooks should not trigger restart"""
        # All webhooks healthy
        mock_health.return_value = True

        webhook_watchdog.watchdog_check()

        # Restart should not be called
        mock_restart.assert_not_called()


class TestDatabaseLogging:
    """Test database logging functionality"""

    def test_log_action_creates_entry(self, temp_db):
        """log_action should create database entry"""
        webhook_watchdog.DB_PATH = temp_db

        webhook_watchdog.log_action("Test Webhook", "restart", True)

        # Verify entry exists
        conn = sqlite3.connect(temp_db)
        c = conn.cursor()
        c.execute("SELECT * FROM watchdog_actions WHERE webhook_name = ?", ("Test Webhook",))
        result = c.fetchone()
        conn.close()

        assert result is not None
        assert result[2] == "Test Webhook"  # webhook_name
        assert result[3] == "restart"  # action
        assert result[4] == 1  # success (True)

    def test_log_action_handles_missing_table(self, temp_db):
        """log_action should handle missing table gracefully"""
        webhook_watchdog.DB_PATH = temp_db

        # Drop table to simulate missing schema
        conn = sqlite3.connect(temp_db)
        c = conn.cursor()
        c.execute("DROP TABLE IF EXISTS watchdog_actions")
        conn.commit()
        conn.close()

        # Should not crash
        try:
            webhook_watchdog.log_action("Test", "restart", True)
        except Exception as e:
            pytest.fail(f"log_action raised exception: {e}")
