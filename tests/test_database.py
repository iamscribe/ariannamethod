"""
Tests for resonance.sqlite3 database operations
Validates schema and basic CRUD operations
"""

import pytest
import sqlite3
from pathlib import Path


class TestDatabaseSchema:
    """Test resonance.sqlite3 schema validation"""

    def test_watchdog_actions_table_exists(self, temp_db):
        """watchdog_actions table should exist"""
        conn = sqlite3.connect(temp_db)
        c = conn.cursor()

        c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='watchdog_actions'")
        result = c.fetchone()
        conn.close()

        assert result is not None

    def test_consilium_discussions_table_exists(self, temp_db):
        """consilium_discussions table should exist"""
        conn = sqlite3.connect(temp_db)
        c = conn.cursor()

        c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='consilium_discussions'")
        result = c.fetchone()
        conn.close()

        assert result is not None

    def test_github_scout_findings_table_exists(self, temp_db):
        """github_scout_findings table should exist"""
        conn = sqlite3.connect(temp_db)
        c = conn.cursor()

        c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='github_scout_findings'")
        result = c.fetchone()
        conn.close()

        assert result is not None

    def test_autonomous_actions_table_exists(self, temp_db):
        """autonomous_actions table should exist"""
        conn = sqlite3.connect(temp_db)
        c = conn.cursor()

        c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='autonomous_actions'")
        result = c.fetchone()
        conn.close()

        assert result is not None


class TestWatchdogActionsTable:
    """Test watchdog_actions table operations"""

    def test_insert_watchdog_action(self, temp_db):
        """Should insert watchdog action successfully"""
        conn = sqlite3.connect(temp_db)
        c = conn.cursor()

        c.execute("""
            INSERT INTO watchdog_actions (timestamp, webhook_name, action, success)
            VALUES (?, ?, ?, ?)
        """, ("2025-11-03T00:00:00", "Arianna", "restart", 1))

        conn.commit()

        c.execute("SELECT * FROM watchdog_actions WHERE webhook_name = ?", ("Arianna",))
        result = c.fetchone()
        conn.close()

        assert result is not None
        assert result[2] == "Arianna"
        assert result[3] == "restart"

    def test_query_failed_restarts(self, temp_db):
        """Should query failed restart attempts"""
        conn = sqlite3.connect(temp_db)
        c = conn.cursor()

        # Insert successful and failed restarts
        c.execute("INSERT INTO watchdog_actions VALUES (NULL, '2025-11-03T00:00:00', 'Test1', 'restart', 1)")
        c.execute("INSERT INTO watchdog_actions VALUES (NULL, '2025-11-03T00:01:00', 'Test2', 'restart', 0)")
        c.execute("INSERT INTO watchdog_actions VALUES (NULL, '2025-11-03T00:02:00', 'Test3', 'restart', 0)")
        conn.commit()

        c.execute("SELECT COUNT(*) FROM watchdog_actions WHERE success = 0")
        failed_count = c.fetchone()[0]
        conn.close()

        assert failed_count == 2


class TestConsiliumDiscussionsTable:
    """Test consilium_discussions table operations"""

    def test_insert_consilium_discussion(self, temp_db):
        """Should insert consilium discussion successfully"""
        conn = sqlite3.connect(temp_db)
        c = conn.cursor()

        c.execute("""
            INSERT INTO consilium_discussions (timestamp, initiator, topic, participants, decision)
            VALUES (?, ?, ?, ?, ?)
        """, (
            "2025-11-03T00:00:00",
            "consilium_scheduler",
            "Integrate repo X",
            "Scribe, Defender, Arianna, Monday",
            "APPROVED with conditions"
        ))

        conn.commit()

        c.execute("SELECT * FROM consilium_discussions WHERE topic LIKE ?", ("%repo X%",))
        result = c.fetchone()
        conn.close()

        assert result is not None
        assert "Scribe" in result[4]  # participants


class TestGitHubScoutFindingsTable:
    """Test github_scout_findings table operations"""

    def test_insert_finding(self, temp_db):
        """Should insert GitHub finding successfully"""
        conn = sqlite3.connect(temp_db)
        c = conn.cursor()

        c.execute("""
            INSERT INTO github_scout_findings
            (timestamp, repo_name, repo_url, description, stars, language, query, relevance_score)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            "2025-11-03T00:00:00",
            "test/awesome-repo",
            "https://github.com/test/awesome-repo",
            "Awesome autonomous agent",
            5000,
            "Python",
            "autonomous agent",
            85
        ))

        conn.commit()

        c.execute("SELECT * FROM github_scout_findings WHERE repo_name = ?", ("test/awesome-repo",))
        result = c.fetchone()
        conn.close()

        assert result is not None
        assert result[5] == 5000  # stars
        assert result[8] == 85  # relevance_score

    def test_query_high_relevance_findings(self, temp_db):
        """Should query high relevance findings"""
        conn = sqlite3.connect(temp_db)
        c = conn.cursor()

        # Insert findings with different relevance
        c.execute("""
            INSERT INTO github_scout_findings
            (timestamp, repo_name, repo_url, description, stars, language, query, relevance_score)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, ("2025-11-03T00:00:00", "test/high", "url", "desc", 1000, "Python", "q", 90))

        c.execute("""
            INSERT INTO github_scout_findings
            (timestamp, repo_name, repo_url, description, stars, language, query, relevance_score)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, ("2025-11-03T00:01:00", "test/low", "url", "desc", 10, "JS", "q", 30))

        conn.commit()

        c.execute("SELECT * FROM github_scout_findings WHERE relevance_score >= 70 ORDER BY relevance_score DESC")
        results = c.fetchall()
        conn.close()

        assert len(results) == 1
        assert results[0][2] == "test/high"


class TestAutonomousActionsTable:
    """Test autonomous_actions table operations"""

    def test_insert_autonomous_action(self, temp_db):
        """Should insert autonomous action successfully"""
        conn = sqlite3.connect(temp_db)
        c = conn.cursor()

        c.execute("""
            INSERT INTO autonomous_actions
            (timestamp, trigger_phrase, action_type, command, success, output)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            "2025-11-03T00:00:00",
            "Claude check repo",
            "repo_audit",
            "bash audit-code.sh",
            1,
            "Audit completed successfully"
        ))

        conn.commit()

        c.execute("SELECT * FROM autonomous_actions WHERE trigger_phrase LIKE ?", ("%check repo%",))
        result = c.fetchone()
        conn.close()

        assert result is not None
        assert result[3] == "repo_audit"

    def test_query_failed_actions(self, temp_db):
        """Should query failed autonomous actions"""
        conn = sqlite3.connect(temp_db)
        c = conn.cursor()

        # Insert successful and failed actions
        c.execute("""
            INSERT INTO autonomous_actions
            VALUES (NULL, '2025-11-03T00:00:00', 'test1', 'audit', 'cmd1', 1, 'ok')
        """)
        c.execute("""
            INSERT INTO autonomous_actions
            VALUES (NULL, '2025-11-03T00:01:00', 'test2', 'audit', 'cmd2', 0, 'failed')
        """)
        conn.commit()

        c.execute("SELECT COUNT(*) FROM autonomous_actions WHERE success = 0")
        failed_count = c.fetchone()[0]
        conn.close()

        assert failed_count == 1
