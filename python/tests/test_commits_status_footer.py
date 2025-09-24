"""Tests for status footer in commits view."""

from unittest.mock import Mock, patch
from datetime import datetime

from src.tui.commits_view import CommitView
from src.tui.color_constants import COLOR_METADATA


class TestCommitsStatusFooter:
    """Test status footer functionality in commits view."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_store = Mock()
        self.mock_store.repo_path = "/test/repo"
        self.mock_store.list_chats.return_value = []

        # Patch the load_commits to avoid subprocess calls
        with patch.object(CommitView, "load_commits"):
            self.view = CommitView(self.mock_store)

        # Sample commits
        self.view.commits = [
            {
                "sha": f"{i:06x}",
                "full_sha": f"{i:040x}",
                "author": f"Author{i}",
                "time": datetime(2025, 9, 10, 12 - i, 0),  # Vary hours instead of days
                "subject": f"Commit {i}",
                "has_note": False,
            }
            for i in range(1, 11)  # 10 commits
        ]
        self.view.items = self.view.commits
        self.view.cursor_idx = 0

    def test_status_footer_appears_with_commits(self):
        """Test that status footer appears when commits are present."""
        lines = self.view.get_display_lines(height=20, width=80, colors_enabled=False)

        # Look for status footer
        footer_found = False
        for line in lines[-5:]:  # Check last few lines
            if "(" in line and "/" in line and ")" in line:
                footer_found = True
                # Should show (1/10) for first position
                assert "(1/10)" in line, f"Expected (1/10) in footer, got: {line}"
                break

        assert footer_found, "Status footer not found in display lines"

    def test_status_footer_updates_with_cursor(self):
        """Test that status footer updates when cursor moves."""
        # Initial position
        lines = self.view.get_display_lines(height=20, width=80, colors_enabled=False)
        initial_footer = None
        for line in lines[-5:]:
            if "(" in line and "/" in line and ")" in line:
                initial_footer = line.strip()
                break
        assert "(1/10)" in initial_footer

        # Move cursor to position 4 (0-indexed, so shows as 5)
        self.view.cursor_idx = 4
        lines = self.view.get_display_lines(height=20, width=80, colors_enabled=False)
        updated_footer = None
        for line in lines[-5:]:
            if "(" in line and "/" in line and ")" in line:
                updated_footer = line.strip()
                break
        assert "(5/10)" in updated_footer, f"Expected (5/10), got: {updated_footer}"

        # Move to last position
        self.view.cursor_idx = 9
        lines = self.view.get_display_lines(height=20, width=80, colors_enabled=False)
        final_footer = None
        for line in lines[-5:]:
            if "(" in line and "/" in line and ")" in line:
                final_footer = line.strip()
                break
        assert "(10/10)" in final_footer, f"Expected (10/10), got: {final_footer}"

    def test_status_footer_no_commits(self):
        """Test that no footer appears when there are no commits."""
        self.view.commits = []
        self.view.items = []

        lines = self.view.get_display_lines(height=20, width=80, colors_enabled=False)

        # Should not have status footer
        footer_found = False
        for line in lines:
            if (
                "(" in line
                and "/" in line
                and ")" in line
                and any(c.isdigit() for c in line)
            ):
                footer_found = True
                break

        assert not footer_found, "Should not show status footer when no commits"
        # Should show "No commits" message instead
        assert any("No commits" in line for line in lines), (
            "Should show 'No commits' message"
        )

    def test_status_footer_colored(self):
        """Test that status footer uses metadata color when colors enabled."""
        lines = self.view.get_display_lines(height=20, width=80, colors_enabled=True)

        # Look for colored footer
        footer_found = False
        for line in lines[-5:]:
            if isinstance(line, list):  # Colored lines are lists of tuples
                text = "".join(t for t, _ in line)
                if "(" in text and "/" in text and ")" in text:
                    footer_found = True
                    # Check color of footer
                    for part_text, part_color in line:
                        if "(" in part_text:  # Found the footer part
                            assert part_color == COLOR_METADATA, (
                                f"Footer should use COLOR_METADATA, got {part_color}"
                            )
                    break

        assert footer_found, "Colored status footer not found"

    def test_status_footer_right_aligned(self):
        """Test that status footer is right-aligned."""
        width = 60
        lines = self.view.get_display_lines(
            height=20, width=width, colors_enabled=False
        )

        # Find footer
        footer_line = None
        for line in lines[-5:]:
            if "(" in line and "/" in line and ")" in line:
                footer_line = line
                break

        assert footer_line is not None, "Footer not found"

        # Footer should be right-aligned (end with the status text)
        assert footer_line.rstrip().endswith(")"), "Footer should be right-aligned"
        assert "(1/10)" in footer_line

        # Check that it's padded with spaces on the left
        assert footer_line.startswith(" "), (
            "Footer should have left padding for right alignment"
        )

    def test_status_footer_with_single_commit(self):
        """Test status footer with single commit."""
        self.view.commits = [
            {
                "sha": "abc123",
                "full_sha": "abc123" * 6,
                "author": "Solo",
                "time": datetime(2025, 9, 10, 12, 0),
                "subject": "Single commit",
                "has_note": False,
            }
        ]
        self.view.items = self.view.commits
        self.view.cursor_idx = 0

        lines = self.view.get_display_lines(height=20, width=80, colors_enabled=False)

        footer_found = False
        for line in lines[-5:]:
            if "(" in line and "/" in line and ")" in line:
                footer_found = True
                assert "(1/1)" in line, f"Expected (1/1) for single commit, got: {line}"
                break

        assert footer_found, "Footer should appear even with single commit"

    def test_status_footer_in_read_only_mode(self):
        """Test that status footer appears in read-only mode."""
        # Create view in read-only mode
        with patch.object(CommitView, "load_commits"):
            read_only_view = CommitView(self.mock_store, read_only=True)

        read_only_view.commits = self.view.commits[:5]  # 5 commits
        read_only_view.items = read_only_view.commits
        read_only_view.cursor_idx = 2

        lines = read_only_view.get_display_lines(
            height=20, width=80, colors_enabled=False
        )

        footer_found = False
        for line in lines[-5:]:
            if "(" in line and "/" in line and ")" in line:
                footer_found = True
                assert "(3/5)" in line, f"Expected (3/5) in read-only mode, got: {line}"
                break

        assert footer_found, "Status footer should appear in read-only mode"

    def test_status_footer_respects_height_limit(self):
        """Test that footer doesn't exceed available height."""
        # Very limited height
        lines = self.view.get_display_lines(height=5, width=80, colors_enabled=False)

        # Should not exceed height limit (height includes borders, so content is height-2)
        assert len(lines) <= 5, (
            f"Lines should fit within height limit, got {len(lines)} lines"
        )

        # Footer might not appear if no room, or might appear if there's space
        # Either case is acceptable - footer is optional if no space
