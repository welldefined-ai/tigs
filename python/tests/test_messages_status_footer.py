"""Tests for status footer in messages view."""

from unittest.mock import Mock
from datetime import datetime

from src.tui.messages_view import MessageView
from src.tui.color_constants import COLOR_METADATA


class TestMessagesStatusFooter:
    """Test status footer functionality in messages view."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_parser = Mock()
        self.view = MessageView(self.mock_parser)

        # Create sample messages
        self.view.messages = [
            ("user", "Hello, how are you?", datetime(2025, 9, 10, 10, 0)),
            ("assistant", "I am doing well, thank you!", datetime(2025, 9, 10, 10, 1)),
            ("user", "Can you help me with Python?", datetime(2025, 9, 10, 10, 2)),
            (
                "assistant",
                "Of course! I would be happy to help.",
                datetime(2025, 9, 10, 10, 3),
            ),
            ("user", "Great, thanks!", datetime(2025, 9, 10, 10, 4)),
        ]
        self.view.items = self.view.messages
        self.view.cursor_idx = 0
        self.view.message_cursor_idx = 0

    def test_status_footer_appears_with_messages(self):
        """Test that status footer appears when messages are present."""
        lines = self.view.get_display_lines(height=20, width=50, colors_enabled=False)

        # Look for status footer
        footer_found = False
        for line in lines[-3:]:  # Check last few lines
            if isinstance(line, str) and "(" in line and "/" in line and ")" in line:
                footer_found = True
                # Should show (5/5) for last position (cursor starts at last message by default)
                assert "(5/5)" in line, f"Expected (5/5) in footer, got: {line}"
                break

        assert footer_found, "Status footer not found in display lines"

    def test_status_footer_updates_with_cursor(self):
        """Test that status footer updates when cursor moves."""
        # Initial position
        lines = self.view.get_display_lines(height=20, width=50, colors_enabled=False)
        initial_footer = None
        for line in lines[-3:]:
            if isinstance(line, str) and "(" in line and "/" in line and ")" in line:
                initial_footer = line.strip()
                break
        assert "(5/5)" in initial_footer  # Cursor starts at last message by default

        # Move cursor to position 2
        self.view.cursor_idx = 2
        self.view.message_cursor_idx = 2
        lines = self.view.get_display_lines(height=20, width=50, colors_enabled=False)
        updated_footer = None
        for line in lines[-3:]:
            if isinstance(line, str) and "(" in line and "/" in line and ")" in line:
                updated_footer = line.strip()
                break
        assert "(3/5)" in updated_footer, f"Expected (3/5), got: {updated_footer}"

        # Move to last position
        self.view.cursor_idx = 4
        self.view.message_cursor_idx = 4
        lines = self.view.get_display_lines(height=20, width=50, colors_enabled=False)
        final_footer = None
        for line in lines[-3:]:
            if isinstance(line, str) and "(" in line and "/" in line and ")" in line:
                final_footer = line.strip()
                break
        assert "(5/5)" in final_footer, f"Expected (5/5), got: {final_footer}"

    def test_status_footer_no_messages(self):
        """Test that no footer appears when there are no messages."""
        self.view.messages = []
        self.view.items = []

        lines = self.view.get_display_lines(height=20, width=50, colors_enabled=False)

        # Should not have status footer
        footer_found = False
        for line in lines:
            if isinstance(line, str) and "(" in line and "/" in line and ")" in line:
                if any(c.isdigit() for c in line):
                    footer_found = True
                    break

        assert not footer_found, "Should not show status footer when no messages"
        # Should show "No messages" message instead
        assert any("No messages" in str(line) for line in lines), (
            "Should show 'No messages' message"
        )

    def test_status_footer_colored(self):
        """Test that status footer uses metadata color when colors enabled."""
        lines = self.view.get_display_lines(height=20, width=50, colors_enabled=True)

        # Look for colored footer
        footer_found = False
        for line in lines[-3:]:
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
        width = 40
        lines = self.view.get_display_lines(
            height=20, width=width, colors_enabled=False
        )

        # Find footer
        footer_line = None
        for line in lines[-3:]:
            if isinstance(line, str) and "(" in line and "/" in line and ")" in line:
                footer_line = line
                break

        assert footer_line is not None, "Footer not found"

        # Footer should be right-aligned
        assert footer_line.rstrip().endswith(")"), "Footer should be right-aligned"
        assert "(5/5)" in footer_line  # Cursor starts at last message by default

        # Check that it's padded with spaces on the left
        assert footer_line.startswith(" "), (
            "Footer should have left padding for right alignment"
        )

    def test_status_footer_with_single_message(self):
        """Test status footer with single message."""
        self.view.messages = [("user", "Single message", None)]
        self.view.items = self.view.messages
        self.view.cursor_idx = 0
        self.view.message_cursor_idx = 0

        lines = self.view.get_display_lines(height=20, width=50, colors_enabled=False)

        footer_found = False
        for line in lines[-3:]:
            if isinstance(line, str) and "(" in line and "/" in line and ")" in line:
                footer_found = True
                assert "(1/1)" in line, (
                    f"Expected (1/1) for single message, got: {line}"
                )
                break

        assert footer_found, "Footer should appear even with single message"

    def test_status_footer_respects_height_limit(self):
        """Test that footer fits within available height."""
        # Very limited height
        lines = self.view.get_display_lines(height=8, width=50, colors_enabled=False)

        # Should not exceed height limit
        assert len(lines) <= 8, (
            f"Lines should fit within height limit, got {len(lines)} lines"
        )

        # Footer should still appear if there's room
        # Footer is optional if no space, so we don't assert it must be there
