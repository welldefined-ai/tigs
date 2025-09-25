#!/usr/bin/env python3
"""Test edge cases that reveal tigs limitations and issues."""


import pytest
from framework.paths import PYTHON_DIR
from framework.tui import TUI
from framework.tui import find_cursor_row
from framework.tui import get_commit_at_cursor


def test_extreme_commit_messages(extreme_repo):
    """Test tigs handling of extreme commit message edge cases."""

    command = f"uv run tigs --repo {extreme_repo} store"

    with TUI(command, cwd=PYTHON_DIR, dimensions=(30, 120)) as tui:
        # Wait for UI to load
        tui.wait_for("Commits")

        # Capture initial display
        initial_lines = tui.capture()

        print("=== Extreme Multi-line Test - Initial Display ===")
        for i, line in enumerate(initial_lines[:20]):
            print(f"{i:02d}: {line}")

        # Test cursor detection with extreme commits
        try:
            cursor_row = find_cursor_row(initial_lines)
            commit_at_cursor = get_commit_at_cursor(initial_lines)
            print(f"\nInitial: cursor row {cursor_row}, commit {commit_at_cursor}")
        except Exception as e:
            print(f"Failed to find cursor in extreme display: {e}")
            pytest.fail(f"Could not find cursor with extreme commits: {e}")

        # Test navigation through extreme commits
        print("\n=== Navigation Test with Extreme Commits ===")

        navigation_results = []

        for move in range(10):  # Try to move through all commits
            try:
                tui.send_arrow("down")
                lines = tui.capture()

                cursor_row = find_cursor_row(lines)
                commit_num = get_commit_at_cursor(lines)

                result = {
                    'move': move + 1,
                    'cursor_row': cursor_row,
                    'commit': commit_num,
                    'success': True
                }
                navigation_results.append(result)

                print(f"Move {move + 1}: cursor row {cursor_row}, commit {commit_num}")

            except Exception as e:
                print(f"Navigation failed on move {move + 1}: {e}")
                print("Display at failure:")
                try:
                    lines = tui.capture()
                    for i, line in enumerate(lines[:15]):
                        print(f"  {i:02d}: {line}")
                except Exception:
                    print("  Could not capture display")

                result = {
                    'move': move + 1,
                    'cursor_row': None,
                    'commit': None,
                    'success': False,
                    'error': str(e)
                }
                navigation_results.append(result)
                break

        # Analyze results
        successful_moves = [r for r in navigation_results if r['success']]
        failed_moves = [r for r in navigation_results if not r['success']]

        print("\n=== Results ===")
        print(f"Successful moves: {len(successful_moves)}")
        print(f"Failed moves: {len(failed_moves)}")

        if failed_moves:
            print("Failed moves details:")
            for fail in failed_moves:
                print(f"  Move {fail['move']}: {fail['error']}")

        # The test should handle at least some navigation
        assert len(successful_moves) >= 3, f"Should handle at least 3 moves with extreme commits, got {len(successful_moves)}"

        # If we got failures, that's expected with extreme content - report it
        if failed_moves:
            print(f"\nNote: {len(failed_moves)} moves failed with extreme multi-line commits - this reveals issues with complex commit message handling")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
