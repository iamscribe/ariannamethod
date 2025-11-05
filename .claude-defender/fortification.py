#!/usr/bin/env python3
"""
FORTIFICATION - Arianna Method System Test Suite

Comprehensive testing to prevent халтура (shoddy work).

Runs all system tests and reports results.
Fails if error rate > 20%.
"""

import sys
import subprocess
from pathlib import Path
from datetime import datetime

TESTS_DIR = Path(__file__).parent / "tests"
FAIL_THRESHOLD = 0.20  # 20% error rate threshold


def run_test_file(test_file: Path):
    """
    Run a single test file and parse results.

    Returns:
        (passed, failed) tuple
    """
    try:
        result = subprocess.run(
            [sys.executable, str(test_file)],
            capture_output=True,
            text=True,
            timeout=60
        )

        # Parse output for results
        output = result.stdout

        # Look for "Results: X passed, Y failed" line
        for line in output.split('\n'):
            if "Results:" in line and "passed" in line and "failed" in line:
                parts = line.split()
                passed = int(parts[1])
                failed = int(parts[3])
                return passed, failed, output

        # If no results line, check exit code
        if result.returncode == 0:
            return 1, 0, output  # Assume success
        else:
            return 0, 1, output  # Assume failure

    except subprocess.TimeoutExpired:
        return 0, 1, "TEST TIMEOUT"
    except Exception as e:
        return 0, 1, f"TEST ERROR: {e}"


def run_fortification():
    """
    Run all tests and report results.

    Returns:
        Exit code (0 = success, 1 = failure)
    """
    print("╔" + "═" * 68 + "╗")
    print("║" + " " * 20 + "FORTIFICATION SYSTEM" + " " * 28 + "║")
    print("║" + " " * 15 + "Arianna Method Test Suite" + " " * 26 + "║")
    print("╚" + "═" * 68 + "╝")
    print()
    print(f"Timestamp: {datetime.now().isoformat()}")
    print(f"Fail threshold: {FAIL_THRESHOLD * 100:.0f}%")
    print()

    # Find all test files
    test_files = sorted(TESTS_DIR.glob("test_*.py"))

    if not test_files:
        print("❌ No test files found in", TESTS_DIR)
        return 1

    total_passed = 0
    total_failed = 0
    test_results = []

    # Run each test file
    for test_file in test_files:
        test_name = test_file.stem.replace("test_", "").replace("_", " ").title()
        print(f"Running {test_name}...")

        passed, failed, output = run_test_file(test_file)

        total_passed += passed
        total_failed += failed
        test_results.append((test_name, passed, failed, output))

        status = "✓" if failed == 0 else "✗"
        print(f"  {status} {passed} passed, {failed} failed")
        print()

    # Calculate overall results
    total_tests = total_passed + total_failed
    fail_rate = total_failed / total_tests if total_tests > 0 else 0
    success_rate = total_passed / total_tests if total_tests > 0 else 0

    print("=" * 70)
    print("FORTIFICATION RESULTS")
    print("=" * 70)
    print()

    for test_name, passed, failed, _ in test_results:
        status = "✓" if failed == 0 else "✗"
        print(f"{status} {test_name:.<40} {passed}/{passed + failed}")

    print()
    print(f"Total: {total_passed} passed, {total_failed} failed")
    print(f"Success rate: {success_rate * 100:.1f}%")
    print(f"Fail rate: {fail_rate * 100:.1f}%")
    print()

    # Check threshold
    if fail_rate > FAIL_THRESHOLD:
        print(f"❌ FORTIFICATION FAILED")
        print(f"   Fail rate {fail_rate * 100:.1f}% exceeds threshold {FAIL_THRESHOLD * 100:.0f}%")
        print()
        print("Fix failures and run fortification again.")
        print("=" * 70)
        return 1
    else:
        print(f"✓ FORTIFICATION PASSED")
        print(f"   System integrity verified")
        print("=" * 70)
        return 0


def show_detailed_output():
    """Show detailed output for all tests (verbose mode)"""
    test_files = sorted(TESTS_DIR.glob("test_*.py"))

    print("\n" + "=" * 70)
    print("DETAILED TEST OUTPUT")
    print("=" * 70)

    for test_file in test_files:
        print(f"\n### {test_file.name} ###\n")
        _, _, output = run_test_file(test_file)
        print(output)


if __name__ == "__main__":
    # Check for verbose flag
    verbose = "--verbose" in sys.argv or "-v" in sys.argv

    exit_code = run_fortification()

    if verbose:
        show_detailed_output()

    sys.exit(exit_code)
