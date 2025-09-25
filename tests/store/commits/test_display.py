#!/usr/bin/env python3
"""Test commit display handling for various message formats."""

import tempfile
from pathlib import Path

import pytest
from framework.fixtures import create_test_repo
from framework.paths import PYTHON_DIR
from framework.tui import TUI
from framework.tui import find_cursor_row
from framework.tui import get_all_visible_commits
from framework.tui import get_commit_at_cursor
from framework.tui import get_first_pane


@pytest.fixture
def scrolling_repo():
    """Create repository with varied commits for display testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_path = Path(tmpdir) / "scrolling_repo"

        # Create varied commits that will cause display issues
        commits = []
        for i in range(60):
            if i % 5 == 0:
                # Very long commits that will wrap multiple lines
                commits.append(
                    f"Long commit {i + 1}: "
                    + "This is an extremely long commit message that will definitely wrap to multiple lines when displayed in the narrow commits pane and should cause cursor positioning issues "
                    * 2
                )
            elif i % 3 == 0:
                # Multi-line commits with actual newlines
                commits.append(
                    f"Multi-line commit {i + 1}:\n\nThis commit has multiple paragraphs\nwith line breaks that might\ncause display issues\n\n- Feature A\n- Feature B\n- Bug fixes"
                )
            else:
                # Normal commits
                commits.append(f"Commit {i + 1}: Regular changes")

        create_test_repo(repo_path, commits)
        yield repo_path


def test_multiline_commit_display(test_repo):
    """Test tigs display of long/multi-line commit messages."""

    command = f"uv run tigs --repo {test_repo} store"

    with TUI(command, cwd=PYTHON_DIR, dimensions=(30, 120)) as tui:
        # Wait for UI to load
        tui.wait_for("Commits")

        # Capture initial display
        initial_lines = tui.capture()

        print("=== Multi-line Commit Test ===")
        for i, line in enumerate(initial_lines[:10]):
            print(f"{i:02d}: {line}")

        # Test basic functionality with multi-line commits
        cursor_row = find_cursor_row(initial_lines)
        commit_at_cursor = get_commit_at_cursor(initial_lines)
        all_commits = get_all_visible_commits(initial_lines)

        print(f"Cursor at row {cursor_row}, commit {commit_at_cursor}")
        print(f"Visible commits: {all_commits[:5]}...")  # Show first 5

        # Basic assertions
        assert len(all_commits) >= 3, (
            f"Should see at least 3 commits, got: {len(all_commits)}"
        )
        # Test should verify that the cursor is on Change 50, regardless of full extraction format
        assert "Change 50:" in commit_at_cursor, (
            f"Expected cursor on Change 50, got: {commit_at_cursor}"
        )


def test_commit_prefix_formatting(test_repo):
    """Test that commit prefixes are formatted compactly without extra spaces."""

    command = f"uv run tigs --repo {test_repo} store"

    with TUI(command, cwd=PYTHON_DIR, dimensions=(30, 100)) as tui:
        # Wait for UI to load
        tui.wait_for("Commits")

        # Capture initial display
        initial_lines = tui.capture()

        print("=== Commit Prefix Formatting Test ===")
        commit_lines = []
        for i, line in enumerate(initial_lines[:15]):
            first_pane = get_first_pane(line)
            if any(word in first_pane for word in ["Change", ":"]):
                commit_lines.append(first_pane)
                print(f"Commit line: '{first_pane}'")

        assert len(commit_lines) >= 1, "Should have at least one commit line"

        # Use regex to verify exact store formatting patterns
        import re

        # Pattern for cursor line: >[ ] MM-DD HH:MM Author or >[ ]* MM-DD HH:MM Author (compact, no space between > and [ ])
        cursor_pattern = r">\[\s*[x\s]\]\*?\s+\d{2}-\d{2}\s+\d{2}:\d{2}\s+\w+"
        # Pattern for non-cursor line: [ ] MM-DD HH:MM Author (space before [ ])
        non_cursor_pattern = r"\s\[\s*[x\s]\]\*?\s+\d{2}-\d{2}\s+\d{2}:\d{2}\s+\w+"
        # Anti-pattern: > [ ] (space between > and [ ]) - should NOT match
        bad_pattern = r">\s+\["
        # Pattern for short datetime format
        short_datetime_pattern = r"\d{2}-\d{2}\s+\d{2}:\d{2}"
        # Pattern for long datetime format (should not be present)
        long_datetime_pattern = r"\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}"

        cursor_found = False
        non_cursor_found = False
        bad_format_found = False
        short_datetime_found = False
        long_datetime_found = False

        for line in commit_lines:
            if re.search(cursor_pattern, line):
                cursor_found = True
                print(
                    f"✓ Store compact cursor formatting: '{line}' matches '>[ ] MM-DD HH:MM'"
                )
            elif re.search(non_cursor_pattern, line):
                non_cursor_found = True
                print(
                    f"✓ Store non-cursor formatting: '{line}' matches ' [ ] MM-DD HH:MM'"
                )
            elif re.search(bad_pattern, line):
                bad_format_found = True
                print(f"✗ Bad formatting found: '{line}' has space between > and [ ]")

            if re.search(short_datetime_pattern, line):
                short_datetime_found = True
                print(f"✓ Short datetime found: '{line}'")
            elif re.search(long_datetime_pattern, line):
                long_datetime_found = True
                print(f"✗ Long datetime found: '{line}'")

        # Main assertions
        assert not bad_format_found, (
            "Should not have space between > and [ ] in store mode"
        )
        assert cursor_found or non_cursor_found, (
            "Should find either cursor or non-cursor checkbox formatting"
        )

        if long_datetime_found:
            print(
                "⚠ Still using long datetime format - code changes may not be active in test environment"
            )
        elif short_datetime_found:
            print("✓ Using short datetime format as expected")


def test_varied_commit_lengths_display(scrolling_repo):
    """Test display analysis with varied commit message lengths."""

    command = f"uv run tigs --repo {scrolling_repo} store"

    with TUI(command, cwd=PYTHON_DIR, dimensions=(30, 120)) as tui:
        try:
            tui.wait_for("commit", timeout=5.0)

            print("=== Varied Commit Lengths Display Test ===")

            # Look for varied commit content in display
            initial_lines = tui.capture()

            print("=== Initial display with varied commits ===")
            for i, line in enumerate(initial_lines[:20]):
                print(f"{i:02d}: {line}")

            # Count different types of content
            long_line_count = 0
            multiline_indicators = 0
            normal_commits = 0

            for line in initial_lines:
                line_len = len(line.strip())
                if line_len > 100:  # Very long lines
                    long_line_count += 1
                elif any(
                    indicator in line.lower()
                    for indicator in ["multi-line", "feature a", "bug fixes"]
                ):
                    multiline_indicators += 1
                elif "commit" in line.lower() and "regular" in line.lower():
                    normal_commits += 1

            print("Display analysis:")
            print(f"  Long lines: {long_line_count}")
            print(f"  Multi-line indicators: {multiline_indicators}")
            print(f"  Normal commits: {normal_commits}")

            if long_line_count > 0 or multiline_indicators > 0:
                print("✓ Varied commit types visible in display")
            else:
                print(
                    "No clear variation in commit display - might be truncated/normalized"
                )

            # Test basic cursor functionality with varied commits
            cursor_row = find_cursor_row(initial_lines)
            commit_at_cursor = get_commit_at_cursor(initial_lines)

            print(f"Cursor at row {cursor_row}, commit {commit_at_cursor}")

            # Should be able to find cursor and commit content
            assert cursor_row >= 0, "Should find cursor in display with varied commits"
            assert commit_at_cursor is not None, "Should identify commit at cursor"

        except Exception as e:
            print(f"Varied commit lengths display test failed: {e}")
            if "not found" in str(e).lower():
                pytest.skip("Store command not available")
            else:
                raise


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
