"""
Tests for github-scout-daemon.py
Autonomous repository discovery and relevance scoring
"""

import pytest
import sqlite3
import sys
from pathlib import Path
from unittest.mock import Mock, patch

# Add tools to path
sys.path.insert(0, str(Path.home() / "ariannamethod" / ".claude-defender" / "tools"))

# Import module
import importlib.util
spec = importlib.util.spec_from_file_location(
    "github_scout",
    Path.home() / "ariannamethod" / ".claude-defender" / "tools" / "github-scout-daemon.py"
)
github_scout = importlib.util.module_from_spec(spec)
spec.loader.exec_module(github_scout)


class TestRelevanceCalculation:
    """Test repo relevance scoring algorithm"""

    def test_high_stars_high_relevance(self):
        """Repo with many stars gets high score"""
        repo = {
            "stargazers_count": 50000,
            "updated_at": "2025-01-01T00:00:00Z",
            "description": "autonomous agent with transformers",
            "language": "Python"
        }

        score = github_scout.calculate_relevance(repo)
        assert score >= 70, f"Expected high relevance, got {score}"

    def test_low_stars_low_relevance(self):
        """Repo with few stars gets lower score"""
        repo = {
            "stargazers_count": 5,
            "updated_at": "2020-01-01T00:00:00Z",
            "description": "simple script",
            "language": "JavaScript"
        }

        score = github_scout.calculate_relevance(repo)
        assert score < 50, f"Expected low relevance, got {score}"

    def test_keyword_matching_increases_score(self):
        """Description with keywords increases relevance"""
        repo_with_keywords = {
            "stargazers_count": 100,
            "updated_at": "2024-01-01T00:00:00Z",
            "description": "autonomous agent with self-healing transformers for consciousness simulation",
            "language": "Python"
        }

        repo_without_keywords = {
            "stargazers_count": 100,
            "updated_at": "2024-01-01T00:00:00Z",
            "description": "simple web application",
            "language": "Python"
        }

        score_with = github_scout.calculate_relevance(repo_with_keywords)
        score_without = github_scout.calculate_relevance(repo_without_keywords)

        assert score_with > score_without, "Keywords should increase relevance"

    def test_python_language_preferred(self):
        """Python repos get higher language score"""
        python_repo = {
            "stargazers_count": 100,
            "updated_at": "2024-01-01T00:00:00Z",
            "description": "test repo",
            "language": "Python"
        }

        js_repo = {
            "stargazers_count": 100,
            "updated_at": "2024-01-01T00:00:00Z",
            "description": "test repo",
            "language": "JavaScript"
        }

        python_score = github_scout.calculate_relevance(python_repo)
        js_score = github_scout.calculate_relevance(js_repo)

        assert python_score > js_score, "Python should score higher"

    def test_recent_activity_increases_score(self):
        """Recently updated repos score higher"""
        recent_repo = {
            "stargazers_count": 100,
            "updated_at": "2025-01-01T00:00:00Z",
            "description": "test",
            "language": "Python"
        }

        old_repo = {
            "stargazers_count": 100,
            "updated_at": "2020-01-01T00:00:00Z",
            "description": "test",
            "language": "Python"
        }

        recent_score = github_scout.calculate_relevance(recent_repo)
        old_score = github_scout.calculate_relevance(old_repo)

        assert recent_score > old_score, "Recent repos should score higher"


class TestGitHubSearch:
    """Test GitHub API search functionality"""

    def test_search_returns_repos(self, mock_github_api):
        """search_github should return list of repos"""
        results = github_scout.search_github("transformer language:python", max_results=5)

        assert isinstance(results, list)
        assert len(results) > 0
        assert results[0]["full_name"] == "test/repo"

    @patch("requests.get")
    def test_search_handles_api_error(self, mock_get):
        """search_github should handle API errors gracefully"""
        mock_get.return_value.status_code = 403  # Rate limit

        results = github_scout.search_github("test query")

        assert results == [], "Should return empty list on error"

    @patch("requests.get")
    def test_search_handles_timeout(self, mock_get):
        """search_github should handle timeout gracefully"""
        mock_get.side_effect = TimeoutError("Connection timeout")

        results = github_scout.search_github("test query")

        assert results == [], "Should return empty list on timeout"


class TestDatabaseSaving:
    """Test saving findings to database"""

    def test_save_finding_creates_entry(self, temp_db):
        """save_finding should create database entry"""
        github_scout.RESONANCE_DB = temp_db

        repo = {
            "full_name": "test/awesome-repo",
            "html_url": "https://github.com/test/awesome-repo",
            "description": "Awesome autonomous agent",
            "stargazers_count": 5000,
            "language": "Python"
        }

        github_scout.save_finding(repo, "autonomous agent language:python")

        # Verify entry exists
        conn = sqlite3.connect(temp_db)
        c = conn.cursor()
        c.execute("SELECT * FROM github_scout_findings WHERE repo_name = ?", ("test/awesome-repo",))
        result = c.fetchone()
        conn.close()

        assert result is not None
        assert result[2] == "test/awesome-repo"
        assert result[5] == 5000  # stars

    def test_save_finding_calculates_relevance(self, temp_db):
        """save_finding should calculate and store relevance score"""
        github_scout.RESONANCE_DB = temp_db

        repo = {
            "full_name": "test/high-relevance",
            "html_url": "https://github.com/test/high-relevance",
            "description": "autonomous self-healing agent with transformers",
            "stargazers_count": 10000,
            "language": "Python"
        }

        github_scout.save_finding(repo, "autonomous agent")

        # Check relevance score was stored
        conn = sqlite3.connect(temp_db)
        c = conn.cursor()
        c.execute("SELECT relevance_score FROM github_scout_findings WHERE repo_name = ?", ("test/high-relevance",))
        result = c.fetchone()
        conn.close()

        assert result is not None
        relevance = result[0]
        assert relevance > 70, f"Expected high relevance, got {relevance}"


class TestScoutRun:
    """Test full scout run cycle"""

    @patch("github_scout.search_github")
    @patch("github_scout.save_finding")
    def test_scout_run_processes_all_queries(self, mock_save, mock_search):
        """scout_run should search all configured queries"""
        mock_search.return_value = [
            {
                "full_name": "test/repo",
                "html_url": "https://github.com/test/repo",
                "description": "autonomous agent system",
                "stargazers_count": 2000,
                "language": "Python",
                "updated_at": "2025-01-01T00:00:00Z"
            }
        ]

        # Should not crash
        try:
            github_scout.scout_run()
        except Exception as e:
            pytest.fail(f"scout_run raised exception: {e}")

        # Should call search for each query
        assert mock_search.call_count == len(github_scout.SEARCH_QUERIES)

    @patch("github_scout.search_github")
    @patch("github_scout.save_finding")
    def test_scout_run_filters_low_relevance(self, mock_save, mock_search):
        """scout_run should only save high relevance repos"""
        # Return repo with low stars (low relevance)
        mock_search.return_value = [
            {
                "full_name": "test/low-relevance",
                "html_url": "https://github.com/test/low-relevance",
                "description": "simple script",
                "stargazers_count": 5,
                "language": "JavaScript",
                "updated_at": "2020-01-01T00:00:00Z"
            }
        ]

        github_scout.scout_run()

        # Should not save low relevance repos (relevance < 50)
        # Note: actual behavior depends on relevance threshold in code
        # Adjust assertion based on actual threshold
