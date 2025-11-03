# Arianna Method Tests

Test suite for autonomous daemon ecosystem and core utilities.

## Structure

```
tests/
├── test_webhook_watchdog.py      # Webhook health monitoring & restart
├── test_consilium_agent.py       # Multi-engine consilium integration
├── test_github_scout.py          # Repository discovery & relevance
├── test_voice_action_monitor.py  # Voice command → action execution
├── test_fortification_plus.py    # Security scanning & auto-fixes
├── test_database.py              # resonance.sqlite3 operations
├── conftest.py                   # Pytest fixtures & mocks
└── README.md                     # This file
```

## Running Tests

```bash
# Install pytest (if not installed)
pip install pytest pytest-mock

# Run all tests
cd ~/ariannamethod
pytest tests/ -v

# Run specific test file
pytest tests/test_webhook_watchdog.py -v

# Run with coverage
pytest tests/ --cov=.claude-defender/tools --cov-report=html
```

## Test Philosophy

**Coverage focus:**
- ✅ Core autonomous systems (webhooks, daemons, consilium)
- ✅ Database operations (resonance.sqlite3)
- ✅ API integrations (mocked for CI/CD)
- ✅ Critical security functions

**Not covered (yet):**
- Field4 Core (complex transformer system)
- Genesis scripts (creative output testing is hard)
- Voice input/output (hardware-dependent)

## Mocking Strategy

All external APIs are mocked:
- `ANTHROPIC_API_KEY` → mock responses
- `PERPLEXITY_API_KEY` → mock responses
- `GITHUB_TOKEN` → mock GitHub API
- Network requests → `requests-mock` or `pytest-mock`

This allows tests to run without API keys and without network.

## CI/CD Integration

These tests are designed to work in GitHub Actions:
- No API keys required (mocked)
- No Termux-specific dependencies
- Pure Python + pytest

## Contributing

When adding new tools to `.claude-defender/tools/`, add corresponding test file:
```bash
# Tool: my_new_tool.py
# Test: tests/test_my_new_tool.py
```

Test should cover:
1. Basic functionality (happy path)
2. Error handling (API failures, missing files, etc)
3. Database operations (if applicable)
4. Edge cases

---

**Built by:** Claude Defender (Autonomous Guardian)
**For:** Arianna Method Ecosystem
**Date:** 2025-11-03
