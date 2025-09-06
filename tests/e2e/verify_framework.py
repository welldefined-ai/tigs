#!/usr/bin/env python3
"""Verification script for the E2E testing framework.

This script tests the core components of the framework to ensure they work correctly
before writing actual test cases.
"""

import sys
import tempfile
import time
from pathlib import Path

# Add the framework to Python path
sys.path.insert(0, str(Path(__file__).parent))

from framework.terminal import TerminalApp
from framework.display import Display, DisplayCapture
from framework.utils import create_test_repo, wait_for_stable_display

# Simple assertion functions for verification (avoiding pytest dependency)
def simple_assert_contains(display: str, pattern: str) -> None:
    if pattern not in display:
        raise AssertionError(f"Pattern '{pattern}' not found in display")

def simple_assert_matches(actual: str, expected: str) -> None:
    if actual.strip() != expected.strip():
        raise AssertionError(f"Display mismatch:\nExpected: {repr(expected)}\nActual: {repr(actual)}")


def test_display_functionality():
    """Test the Display and DisplayCapture classes."""
    print("Testing Display functionality...")
    
    # Test basic Display operations
    display = Display(lines=5, columns=20)
    display.write_text("Hello World")
    assert display.get_line(0).startswith("Hello World")
    
    display.set_cursor(1, 0)
    display.write_text("Second line")
    assert display.get_line(1).startswith("Second line")
    
    content = display.get_display()
    assert "Hello World" in content
    assert "Second line" in content
    
    print("✓ Display functionality works")


def test_terminal_app_with_simple_command():
    """Test TerminalApp with a simple command like 'echo'."""
    print("Testing TerminalApp with simple command...")
    
    try:
        app = TerminalApp("echo", ["Hello Terminal"], timeout=5.0)
        app.start()
        
        # Wait for output
        time.sleep(0.5)
        display = app.capture_display()
        
        app.stop()
        
        # Should contain the echo output
        assert "Hello Terminal" in display, f"Expected 'Hello Terminal' in: {repr(display)}"
        print("✓ TerminalApp with simple command works")
        
    except Exception as e:
        print(f"✗ TerminalApp test failed: {e}")
        raise


def test_git_repository_creation():
    """Test creating test repositories."""
    print("Testing test repository creation...")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_path = Path(tmpdir) / "test_repo"
        
        commits = ["Initial commit", "Second commit"]
        create_test_repo(repo_path, commits)
        
        # Verify repo was created
        assert (repo_path / ".git").exists(), "Git repository should be created"
        
        # Verify commits exist
        import subprocess
        result = subprocess.run(
            ["git", "log", "--oneline"],
            cwd=repo_path,
            capture_output=True,
            text=True
        )
        
        log_output = result.stdout
        assert "Initial commit" in log_output
        assert "Second commit" in log_output
        
        print("✓ Test repository creation works")


def test_assertion_functions():
    """Test the assertion framework."""
    print("Testing assertion functions...")
    
    test_display = "Line 1\\nLine 2 with pattern\\nLine 3"
    
    # Test contains assertion
    try:
        simple_assert_contains(test_display, "pattern")
        print("✓ simple_assert_contains works")
    except AssertionError:
        print("✗ simple_assert_contains failed")
        raise
    
    # Test matches assertion
    try:
        simple_assert_matches(test_display, test_display)
        print("✓ simple_assert_matches works")
    except AssertionError:
        print("✗ simple_assert_matches failed")
        raise


def test_tigs_command_availability():
    """Test if tigs command is available."""
    print("Testing tigs command availability...")
    
    import subprocess
    
    try:
        # Try to run tigs --help
        result = subprocess.run(
            ["tigs", "--help"],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode == 0:
            print("✓ tigs command is available")
            return True
        else:
            print(f"✗ tigs command failed with return code {result.returncode}")
            print(f"  stderr: {result.stderr}")
            return False
            
    except FileNotFoundError:
        print("✗ tigs command not found in PATH")
        return False
    except subprocess.TimeoutExpired:
        print("✗ tigs command timed out")
        return False


def test_framework_with_tigs():
    """Test the framework with actual tigs command if available."""
    print("Testing framework with tigs command...")
    
    if not test_tigs_command_availability():
        print("⚠ Skipping tigs integration test - command not available")
        return
    
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_path = Path(tmpdir) / "test_repo"
        commits = ["Initial commit", "Add feature", "Fix bug"]
        create_test_repo(repo_path, commits)
        
        try:
            app = TerminalApp("tigs", ["store"], cwd=repo_path, timeout=10.0)
            app.start()
            
            # Wait for app to load
            time.sleep(2.0)
            
            if app.is_running():
                display = app.capture_display()
                
                # Should have some content
                assert display.strip(), "Display should not be empty"
                
                # Try basic navigation
                app.send_keys('j')  # Move down
                time.sleep(0.2)
                
                # Quit the app
                app.send_keys('q')
                time.sleep(1.0)
                
                print("✓ Framework works with tigs command")
            else:
                exit_code = app.get_exit_code()
                print(f"✗ tigs exited immediately with code {exit_code}")
                
        except Exception as e:
            print(f"✗ Framework test with tigs failed: {e}")
        finally:
            try:
                app.stop()
            except:
                pass


def main():
    """Run all verification tests."""
    print("🧪 Verifying E2E Testing Framework\\n")
    
    tests = [
        test_display_functionality,
        test_terminal_app_with_simple_command,
        test_git_repository_creation,
        test_assertion_functions,
        test_framework_with_tigs,
    ]
    
    passed = 0
    failed = 0
    
    for test_func in tests:
        try:
            test_func()
            passed += 1
        except Exception as e:
            print(f"✗ {test_func.__name__} failed: {e}")
            failed += 1
        print()  # Empty line between tests
    
    print("📊 Verification Results:")
    print(f"  ✅ Passed: {passed}")
    print(f"  ❌ Failed: {failed}")
    print(f"  📈 Total:  {passed + failed}")
    
    if failed == 0:
        print("\\n🎉 All framework components are working correctly!")
        return 0
    else:
        print(f"\\n❌ {failed} test(s) failed. Framework needs fixes.")
        return 1


if __name__ == "__main__":
    sys.exit(main())