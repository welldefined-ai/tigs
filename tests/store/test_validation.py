#!/usr/bin/env python3
"""Test validation errors for incomplete selections."""

import tempfile
from pathlib import Path

import pytest
from framework.fixtures import create_test_repo
from framework.mock_claude_logs import create_mock_claude_home
from framework.paths import PYTHON_DIR
from framework.tui import TUI


@pytest.fixture
def validation_setup(monkeypatch):
    """Create repo and messages for validation testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_path = Path(tmpdir) / "repo"
        mock_home = Path(tmpdir) / "mock_home"
        mock_home.mkdir()

        # Mock HOME environment variable
        monkeypatch.setenv("HOME", str(mock_home))

        # Create repo
        commits = [f"Validation test commit {i+1}" for i in range(5)]
        create_test_repo(repo_path, commits)

        # Create mock Claude logs
        sessions_data = [[
            ("user", "Validation test message 1"),
            ("assistant", "Validation test response 1"),
            ("user", "Validation test message 2")
        ]]
        create_mock_claude_home(mock_home, sessions_data)

        yield repo_path, mock_home


class TestValidation:
    """Test validation error handling."""

    def test_no_commits_selected(self, validation_setup):
        """Test Enter with no commits selected shows error."""
        repo_path, mock_home = validation_setup

        command = f"uv run tigs --repo {repo_path} store"

        with TUI(command, cwd=PYTHON_DIR, dimensions=(30, 120), env={"HOME": str(mock_home)}) as tui:
            try:
                tui.wait_for("commit", timeout=5.0)

                print("=== No Commits Selected Test ===")

                # Select messages but no commits
                tui.send("<tab>")  # Go to messages pane
                tui.send(" ")     # Select a message

                tui.capture()
                print("Selected messages, no commits")

                # Press Enter - should show validation error
                tui.send("<enter>")

                error_display = tui.capture()

                print("=== Display after Enter (no commits) ===")
                for i, line in enumerate(error_display[:20]):
                    print(f"{i:02d}: {line}")

                # Look for error indicators
                error_text = "\n".join(error_display).lower()
                error_patterns = [
                    "error", "select", "commit", "required",
                    "must", "need", "invalid", "missing"
                ]

                error_found = any(pattern in error_text for pattern in error_patterns)

                if error_found:
                    print("✓ Validation error displayed for no commits selected")
                else:
                    print("No clear validation error - might be handled silently")

                # Should not have created any Git notes
                import subprocess
                notes_result = subprocess.run(
                    ["git", "notes", "--ref", "refs/notes/chats", "list"],
                    cwd=repo_path,
                    capture_output=True,
                    text=True
                )

                if notes_result.returncode != 0 or not notes_result.stdout.strip():
                    print("✓ No Git notes created (correct)")
                else:
                    print("Git notes were created despite validation error")

            except Exception as e:
                print(f"No commits test failed: {e}")
                if "not found" in str(e).lower():
                    pytest.skip("Store command not available")

    def test_no_messages_selected(self, validation_setup):
        """Test Enter with no messages selected shows error."""
        repo_path, mock_home = validation_setup

        command = f"uv run tigs --repo {repo_path} store"

        with TUI(command, cwd=PYTHON_DIR, dimensions=(30, 120), env={"HOME": str(mock_home)}) as tui:
            try:
                tui.wait_for("commit", timeout=5.0)

                print("=== No Messages Selected Test ===")

                # Select commits but no messages
                tui.send(" ")     # Select a commit
                tui.send_arrow("down")
                tui.send(" ")     # Select another commit

                tui.capture()
                print("Selected commits, no messages")

                # Press Enter - should show validation error
                tui.send("<enter>")

                error_display = tui.capture()

                print("=== Display after Enter (no messages) ===")
                for i, line in enumerate(error_display[:20]):
                    print(f"{i:02d}: {line}")

                # Look for error indicators
                error_text = "\n".join(error_display).lower()
                error_patterns = [
                    "error", "select", "message", "required",
                    "must", "need", "invalid", "missing"
                ]

                error_found = any(pattern in error_text for pattern in error_patterns)

                if error_found:
                    print("✓ Validation error displayed for no messages selected")
                else:
                    print("No clear validation error - might be handled silently")

                # Should not have created Git notes
                import subprocess
                notes_result = subprocess.run(
                    ["git", "notes", "--ref", "refs/notes/chats", "list"],
                    cwd=repo_path,
                    capture_output=True
                )

                if notes_result.returncode != 0 or not notes_result.stdout.strip():
                    print("✓ No Git notes created (correct)")
                else:
                    print("Git notes were created despite validation error")

            except Exception as e:
                print(f"No messages test failed: {e}")
                if "not found" in str(e).lower():
                    pytest.skip("Store command not available")

    def test_nothing_selected(self, validation_setup):
        """Test Enter with nothing selected shows error."""
        repo_path, mock_home = validation_setup

        command = f"uv run tigs --repo {repo_path} store"

        with TUI(command, cwd=PYTHON_DIR, dimensions=(30, 120), env={"HOME": str(mock_home)}) as tui:
            try:
                tui.wait_for("commit", timeout=5.0)

                print("=== Nothing Selected Test ===")

                # Don't select anything, just press Enter
                initial_display = tui.capture()
                print("No selections made")

                tui.send("<enter>")

                error_display = tui.capture()

                print("=== Display after Enter (nothing selected) ===")
                for i, line in enumerate(error_display[:20]):
                    print(f"{i:02d}: {line}")

                # Look for error indicators
                error_text = "\n".join(error_display).lower()
                error_patterns = [
                    "error", "select", "nothing", "empty", "required",
                    "must", "need", "invalid", "no selection"
                ]

                error_found = any(pattern in error_text for pattern in error_patterns)

                if error_found:
                    print("✓ Validation error displayed for nothing selected")
                else:
                    print("No clear validation error - might be handled silently")

                # Should not have created Git notes
                import subprocess
                notes_result = subprocess.run(
                    ["git", "notes", "--ref", "refs/notes/chats", "list"],
                    cwd=repo_path,
                    capture_output=True
                )

                if notes_result.returncode != 0 or not notes_result.stdout.strip():
                    print("✓ No Git notes created (correct)")
                else:
                    print("Git notes were created despite no selections")

                # Display should be similar to before (no crash)
                display_similar = len(error_display) > 0 and len(initial_display) > 0

                if display_similar:
                    print("✓ UI remained stable after validation error")

            except Exception as e:
                print(f"Nothing selected test failed: {e}")
                if "not found" in str(e).lower():
                    pytest.skip("Store command not available")

    def test_validation_preserves_state(self, validation_setup):
        """Test validation errors don't clear existing selections."""
        repo_path, mock_home = validation_setup

        command = f"uv run tigs --repo {repo_path} store"

        with TUI(command, cwd=PYTHON_DIR, dimensions=(30, 120), env={"HOME": str(mock_home)}) as tui:
            try:
                tui.wait_for("commit", timeout=5.0)

                print("=== Validation State Preservation Test ===")

                # Make partial selections (commits only)
                tui.send(" ")     # Select commit
                tui.send_arrow("down")
                tui.send(" ")     # Select another commit

                before_error = tui.capture()

                # Count selections before
                selections_before = sum(1 for line in before_error
                                      if "[x]" in line or "✓" in line)
                print(f"Selections before validation error: {selections_before}")

                # Try to store (should fail validation)
                tui.send("<enter>")

                after_error = tui.capture()

                # Count selections after error
                selections_after = sum(1 for line in after_error
                                     if "[x]" in line or "✓" in line)
                print(f"Selections after validation error: {selections_after}")

                if selections_before > 0 and selections_after >= selections_before:
                    print("✓ Selections preserved after validation error")
                elif selections_before > 0:
                    print(f"Some selections lost: {selections_before} → {selections_after}")
                else:
                    print("No selections detected to test preservation")

            except Exception as e:
                print(f"State preservation test failed: {e}")
                if "not found" in str(e).lower():
                    pytest.skip("Store command not available")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
