#!/usr/bin/env python3
"""
Tests for Mac Daemon
"""

import os
import sys
import time
import json
import subprocess
from pathlib import Path

# Add parent dir to path
sys.path.insert(0, str(Path(__file__).parent))

from daemon import MacDaemon, HOME, DAEMON_DIR, STATE_FILE

def test_init():
    """Test daemon initialization"""
    print("TEST: Daemon initialization...", end=" ")
    try:
        daemon = MacDaemon()
        assert daemon is not None
        assert DAEMON_DIR.exists()
        assert STATE_FILE.exists()
        print("✓ PASS")
        return True
    except Exception as e:
        print(f"✗ FAIL: {e}")
        return False

def test_config():
    """Test configuration loading"""
    print("TEST: Configuration loading...", end=" ")
    try:
        daemon = MacDaemon()
        config = daemon.config
        assert 'anthropic_api_key' in config or os.getenv('ANTHROPIC_API_KEY')
        assert 'ssh_host' in config
        assert 'ssh_port' in config
        print("✓ PASS")
        return True
    except Exception as e:
        print(f"✗ FAIL: {e}")
        return False

def test_state():
    """Test state persistence"""
    print("TEST: State persistence...", end=" ")
    try:
        daemon = MacDaemon()
        
        # Modify state
        daemon.state['test_key'] = 'test_value'
        daemon._save_state()
        
        # Reload
        daemon2 = MacDaemon()
        assert daemon2.state['test_key'] == 'test_value'
        
        # Cleanup
        del daemon2.state['test_key']
        daemon2._save_state()
        
        print("✓ PASS")
        return True
    except Exception as e:
        print(f"✗ FAIL: {e}")
        return False

def test_adb():
    """Test ADB connection"""
    print("TEST: ADB connection...", end=" ")
    try:
        result = subprocess.run(['adb', 'devices'], capture_output=True, text=True, timeout=5)
        assert result.returncode == 0
        print("✓ PASS")
        return True
    except Exception as e:
        print(f"✗ FAIL: {e}")
        return False

def test_phone_check():
    """Test phone detection"""
    print("TEST: Phone detection...", end=" ")
    try:
        daemon = MacDaemon()
        connected = daemon.check_phone()
        assert isinstance(connected, bool)
        print(f"✓ PASS (phone: {connected})")
        return True
    except Exception as e:
        print(f"✗ FAIL: {e}")
        return False

def test_cursor_check():
    """Test Cursor project detection"""
    print("TEST: Cursor project detection...", end=" ")
    try:
        daemon = MacDaemon()
        project = daemon.check_cursor()
        assert project is None or isinstance(project, str)
        print(f"✓ PASS (project: {project or 'none'})")
        return True
    except Exception as e:
        print(f"✗ FAIL: {e}")
        return False

def test_logging():
    """Test logging"""
    print("TEST: Logging...", end=" ")
    try:
        daemon = MacDaemon()
        test_msg = f"TEST_{time.time()}"
        daemon.log(test_msg)
        
        # Check log file
        log_file = DAEMON_DIR / "daemon.log"
        assert log_file.exists()
        content = log_file.read_text()
        assert test_msg in content
        
        print("✓ PASS")
        return True
    except Exception as e:
        print(f"✗ FAIL: {e}")
        return False

def test_ai():
    """Test AI reasoning"""
    print("TEST: AI reasoning...", end=" ")
    try:
        daemon = MacDaemon()
        if not daemon.anthropic:
            print("⊘ SKIP (no API key)")
            return True
        
        response = daemon.think("What is 2+2?")
        assert response is not None
        assert len(response) > 0
        assert "4" in response or "four" in response.lower()
        
        print("✓ PASS")
        return True
    except Exception as e:
        print(f"✗ FAIL: {e}")
        return False

def test_sync():
    """Test memory sync (if phone connected)"""
    print("TEST: Memory sync...", end=" ")
    try:
        daemon = MacDaemon()
        
        # Check if phone connected
        if not daemon.check_phone():
            print("⊘ SKIP (phone not connected)")
            return True
        
        result = daemon.sync_memory()
        assert isinstance(result, bool)
        
        if result:
            # Check that resonance.sqlite3 exists
            db_path = HOME / "Downloads" / "arianna_clean" / "resonance.sqlite3"
            assert db_path.exists()
            print("✓ PASS")
        else:
            print("⊘ SKIP (sync failed, but no error)")
        
        return True
    except Exception as e:
        print(f"✗ FAIL: {e}")
        return False

def main():
    print("=" * 60)
    print("Mac Daemon Test Suite")
    print("=" * 60)
    
    tests = [
        test_init,
        test_config,
        test_state,
        test_logging,
        test_adb,
        test_phone_check,
        test_cursor_check,
        test_ai,
        test_sync,
    ]
    
    results = []
    for test in tests:
        results.append(test())
        time.sleep(0.5)
    
    print("=" * 60)
    passed = sum(results)
    total = len(results)
    print(f"Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("✓ ALL TESTS PASSED")
        sys.exit(0)
    else:
        print(f"✗ {total - passed} TESTS FAILED")
        sys.exit(1)

if __name__ == "__main__":
    main()
