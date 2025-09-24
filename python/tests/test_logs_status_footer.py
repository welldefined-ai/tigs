"""Tests for status footer in logs view."""

from unittest.mock import Mock
from datetime import datetime, timedelta

from src.tui.logs_view import LogsView
from src.tui.color_constants import COLOR_METADATA


class TestLogsStatusFooter:
    """Test status footer functionality in logs view."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_parser = Mock()
        self.view = LogsView(self.mock_parser)

        # Create sample logs with metadata
        base_time = datetime.now()
        self.view.logs = [
            ("log_001", {"modified": (base_time - timedelta(hours=0)).isoformat()}),
            ("log_002", {"modified": (base_time - timedelta(hours=1)).isoformat()}),
            ("log_003", {"modified": (base_time - timedelta(hours=2)).isoformat()}),
            ("log_004", {"modified": (base_time - timedelta(hours=3)).isoformat()}),
            ("log_005", {"modified": (base_time - timedelta(hours=4)).isoformat()}),
        ]
        self.view.selected_log_idx = 0
        self.view.log_scroll_offset = 0

    def test_status_footer_appears_with_logs(self):
        """Test that status footer appears when logs are present."""
        lines = self.view.get_display_lines(height=20)

        # Look for status footer
        footer_found = False
        for line in lines[-3:]:  # Check last few lines
            if "(" in line and "/" in line and ")" in line:
                footer_found = True
                # Should show (1/5) for first position
                assert "(1/5)" in line, f"Expected (1/5) in footer, got: {line}"
                break

        assert footer_found, "Status footer not found in display lines"

    def test_status_footer_updates_with_selection(self):
        """Test that status footer updates when selection changes."""
        # Initial position
        lines = self.view.get_display_lines(height=20)
        initial_footer = None
        for line in lines[-3:]:
            if "(" in line and "/" in line and ")" in line:
                initial_footer = line.strip()
                break
        assert "(1/5)" in initial_footer

        # Move selection to position 2
        self.view.selected_log_idx = 2
        lines = self.view.get_display_lines(height=20)
        updated_footer = None
        for line in lines[-3:]:
            if "(" in line and "/" in line and ")" in line:
                updated_footer = line.strip()
                break
        assert "(3/5)" in updated_footer, f"Expected (3/5), got: {updated_footer}"

        # Move to last position
        self.view.selected_log_idx = 4
        lines = self.view.get_display_lines(height=20)
        final_footer = None
        for line in lines[-3:]:
            if "(" in line and "/" in line and ")" in line:
                final_footer = line.strip()
                break
        assert "(5/5)" in final_footer, f"Expected (5/5), got: {final_footer}"

    def test_status_footer_no_logs(self):
        """Test that no footer appears when there are no logs."""
        self.view.logs = []

        lines = self.view.get_display_lines(height=20)

        # Should not have status footer
        footer_found = False
        for line in lines:
            if "(" in line and "/" in line and ")" in line:
                if any(c.isdigit() for c in line):
                    footer_found = True
                    break

        assert not footer_found, "Should not show status footer when no logs"
        # Should show "No logs found" message instead
        assert any("No logs found" in line for line in lines), (
            "Should show 'No logs found' message"
        )

    def test_status_footer_right_aligned(self):
        """Test that status footer is right-aligned."""
        lines = self.view.get_display_lines(height=20)

        # Find footer
        footer_line = None
        for line in lines[-3:]:
            if "(" in line and "/" in line and ")" in line:
                footer_line = line
                break

        assert footer_line is not None, "Footer not found"

        # Footer should be right-aligned (logs pane is narrow)
        assert footer_line.rstrip().endswith(")"), "Footer should be right-aligned"
        assert "(1/5)" in footer_line

        # Check that it's padded with spaces on the left
        assert footer_line.startswith(" "), (
            "Footer should have left padding for right alignment"
        )

    def test_status_footer_with_single_log(self):
        """Test status footer with single log."""
        self.view.logs = [("single_log", {"modified": datetime.now().isoformat()})]
        self.view.selected_log_idx = 0

        lines = self.view.get_display_lines(height=20)

        footer_found = False
        for line in lines[-3:]:
            if "(" in line and "/" in line and ")" in line:
                footer_found = True
                assert "(1/1)" in line, f"Expected (1/1) for single log, got: {line}"
                break

        assert footer_found, "Footer should appear even with single log"

    def test_status_footer_respects_height_limit(self):
        """Test that footer fits within available height."""
        # Very limited height
        lines = self.view.get_display_lines(height=8)

        # Should not exceed height limit minus borders
        assert len(lines) <= 6, (
            f"Lines should fit within height limit, got {len(lines)} lines"
        )

        # Footer should still appear if there's room
        footer_found = any(
            "(" in line and "/" in line and ")" in line for line in lines
        )
        # With height 8, we have 6 lines available (8-2 borders), so footer should appear
        assert footer_found, "Footer should appear when there's room"

    def test_status_footer_with_scrolling(self):
        """Test that footer shows correct position during scrolling."""
        # Create many logs to enable scrolling
        base_time = datetime.now()
        self.view.logs = [
            (f"log_{i:03d}", {"modified": (base_time - timedelta(hours=i)).isoformat()})
            for i in range(20)
        ]
        self.view.selected_log_idx = 10
        self.view.log_scroll_offset = 5

        lines = self.view.get_display_lines(height=10)

        # Footer should show current selection, not scroll offset
        footer_found = False
        for line in lines[-3:]:
            if "(" in line and "/" in line and ")" in line:
                footer_found = True
                assert "(11/20)" in line, (
                    f"Expected (11/20) for position 10, got: {line}"
                )
                break

        assert footer_found, "Footer should show during scrolling"

    def test_status_footer_truncation_narrow_width(self):
        """Test that footer is truncated when too wide for pane."""
        # Create many logs to get double-digit numbers
        base_time = datetime.now()
        self.view.logs = [
            (f"log_{i:03d}", {"modified": (base_time - timedelta(hours=i)).isoformat()})
            for i in range(100)
        ]
        self.view.selected_log_idx = 99

        # Test with very narrow width (e.g., 10 total, 6 usable after borders and padding)
        lines = self.view.get_display_lines(height=20, width=10)

        # Find the footer
        footer_line = lines[-1] if lines else ""

        # With width 10, we have 6 chars after borders and padding (10 - 4)
        # "(100/100)" is 10 chars, so it should be truncated to "(100/1"
        assert len(footer_line) <= 6, (
            f"Footer should be truncated to fit width, got: '{footer_line}' with length {len(footer_line)}"
        )

        # The footer should be truncated
        assert "(100/1" in footer_line or len(footer_line) == 6, (
            f"Footer should be truncated, got: '{footer_line}'"
        )

    def test_status_footer_different_widths(self):
        """Test footer behavior with different pane widths."""
        # Test with standard logs pane width (17)
        lines = self.view.get_display_lines(height=20, width=17)
        footer = lines[-1] if lines else ""
        assert "(1/5)" in footer, (
            f"Footer should show correctly at standard width, got: '{footer}'"
        )

        # Test with narrower width (12)
        lines = self.view.get_display_lines(height=20, width=12)
        footer = lines[-1] if lines else ""
        # Width 12 - 4 (borders+padding) = 8 usable, "(1/5)" is 5 chars, should fit with padding
        assert "(1/5)" in footer, f"Footer should show at width 12, got: '{footer}'"
        assert len(footer) <= 8, "Footer should not exceed usable width"

        # Test with very narrow width (9)
        lines = self.view.get_display_lines(height=20, width=9)
        footer = lines[-1] if lines else ""
        # Width 9 - 4 = 5 usable, "(1/5)" is 5 chars, should just fit
        assert len(footer) <= 5, (
            f"Footer should fit within 5 chars, got: '{footer}' with length {len(footer)}"
        )
        assert "(1/5)" in footer or footer == "(1/5", (
            f"Footer should show or be truncated, got: '{footer}'"
        )

    def test_status_footer_colored(self):
        """Test that status footer uses metadata color when colors enabled."""
        lines = self.view.get_display_lines(height=20, width=17, colors_enabled=True)

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
