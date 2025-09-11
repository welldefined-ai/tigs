"""Tests for commit view coloring following tig's color scheme."""

import pytest
from unittest.mock import Mock, patch
from datetime import datetime

from src.tui.commits_view import CommitView
from src.tui.color_constants import COLOR_AUTHOR, COLOR_METADATA, COLOR_DEFAULT


class TestCommitsViewColors:
    """Test color assignment in commits view."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.mock_store = Mock()
        self.mock_store.repo_path = '/test/repo'
        self.mock_store.list_chats.return_value = []
        
        # Patch the load_commits to avoid subprocess calls
        with patch.object(CommitView, 'load_commits'):
            self.view = CommitView(self.mock_store)
        
        # Sample commits (matching actual format from load_commits)
        self.view.commits = [
            {
                'sha': 'abc123',
                'author': 'Alice',
                'time': datetime(2025, 9, 10, 15, 30),
                'subject': 'Add new feature'
            },
            {
                'sha': 'def456',
                'author': 'Bob',
                'time': datetime(2025, 9, 9, 10, 15),
                'subject': 'Fix bug in very long commit message that wraps to multiple lines'
            },
            {
                'sha': 'ghi789',
                'author': 'VeryLongAuthorNameThatMightCauseWrapping',
                'time': datetime(2025, 9, 8, 8, 0),
                'subject': 'Update documentation'
            }
        ]
        self.view.items = self.view.commits  # For selection mixin
    
    def test_colors_enabled_returns_colored_tuples(self):
        """Test that colors_enabled=True returns list of color tuples."""
        lines = self.view.get_display_lines(height=20, width=80, colors_enabled=True)
        
        # Should return list of color tuple lists
        assert len(lines) > 0
        for line in lines:
            if line:  # Skip empty lines
                assert isinstance(line, list), f"Expected list, got {type(line)}: {line}"
                for part in line:
                    assert isinstance(part, tuple), f"Expected tuple, got {type(part)}: {part}"
                    assert len(part) == 2, f"Expected (text, color) tuple: {part}"
                    text, color = part
                    assert isinstance(text, str)
                    assert isinstance(color, int)
                    assert 0 <= color <= 7, f"Invalid color code: {color}"
    
    def test_colors_disabled_returns_strings(self):
        """Test that colors_enabled=False returns plain strings."""
        lines = self.view.get_display_lines(height=20, width=80, colors_enabled=False)
        
        # Should return list of strings
        assert len(lines) > 0
        for line in lines:
            assert isinstance(line, str), f"Expected string, got {type(line)}: {line}"
    
    def test_author_colored_cyan(self):
        """Test that author names are colored cyan (color 2)."""
        lines = self.view.get_display_lines(height=20, width=80, colors_enabled=True)
        
        # Find lines with author names
        for line in lines:
            if isinstance(line, list):
                text_parts = "".join(t for t, _ in line)
                if "Alice" in text_parts or "Bob" in text_parts:
                    # Check that author part has cyan color
                    for text, color in line:
                        if "Alice" in text or "Bob" in text:
                            assert color == COLOR_AUTHOR, f"Author should be cyan: {text}"
    
    def test_datetime_colored_blue(self):
        """Test that date/time is colored blue (color 7)."""
        lines = self.view.get_display_lines(height=20, width=80, colors_enabled=True)
        
        # Find lines with timestamps
        for line in lines:
            if isinstance(line, list):
                for text, color in line:
                    # Check for date pattern (e.g., "09-10 15:30")
                    if any(c.isdigit() for c in text) and ("-" in text or ":" in text):
                        if len(text.strip()) > 3:  # Not just selection marker
                            assert color == COLOR_METADATA, f"DateTime should be blue: '{text}'"
    
    def test_commit_subject_default_color(self):
        """Test that commit subjects have default color."""
        lines = self.view.get_display_lines(height=20, width=80, colors_enabled=True)
        
        # Find lines with commit subjects
        for line in lines:
            if isinstance(line, list):
                text_parts = "".join(t for t, _ in line)
                if "Add new feature" in text_parts or "Fix bug" in text_parts:
                    # Check subject part has default color
                    for text, color in line:
                        if "Add new feature" in text or "Fix bug" in text:
                            assert color == COLOR_DEFAULT, f"Subject should be default: {text}"
    
    def test_wrapped_lines_maintain_color(self):
        """Test that wrapped commit lines maintain consistent colors."""
        # Use narrow width to force wrapping
        lines = self.view.get_display_lines(height=20, width=40, colors_enabled=True)
        
        # Find wrapped lines (indented continuation lines)
        wrapped_found = False
        for i, line in enumerate(lines):
            if isinstance(line, list):
                text_parts = "".join(t for t, _ in line)
                # Wrapped lines typically start with spaces
                if text_parts.startswith("    "):
                    wrapped_found = True
                    # Check that wrapped content has consistent color
                    for text, color in line:
                        if text.strip():  # Non-whitespace content
                            assert color == COLOR_DEFAULT, f"Wrapped content should be default: {text}"
        
        assert wrapped_found, "No wrapped lines found with narrow width"
    
    def test_long_author_name_coloring(self):
        """Test that very long author names are colored correctly."""
        lines = self.view.get_display_lines(height=20, width=80, colors_enabled=True)
        
        # Find line with long author name
        for line in lines:
            if isinstance(line, list):
                text_parts = "".join(t for t, _ in line)
                if "VeryLongAuthor" in text_parts:
                    # Check author part is cyan
                    for text, color in line:
                        if "VeryLongAuthor" in text:
                            assert color == COLOR_AUTHOR, f"Long author should be cyan: {text}"
    
    def test_selection_marker_default_color(self):
        """Test that selection markers have default color."""
        lines = self.view.get_display_lines(height=20, width=80, colors_enabled=True)
        
        # Check first parts of lines for selection markers
        for line in lines:
            if isinstance(line, list) and line:
                first_text, first_color = line[0]
                # Selection markers like "[ ]" or ">  "
                if first_text.strip() in ["[ ]", "[x]", ">", ">  ", "   "]:
                    assert first_color == COLOR_DEFAULT, f"Selection marker should be default: '{first_text}'"
    
    def test_empty_commits_message_colored(self):
        """Test that empty commits message is properly colored."""
        self.view.commits = []
        lines = self.view.get_display_lines(height=20, width=80, colors_enabled=True)
        
        assert len(lines) == 1
        assert isinstance(lines[0], list)
        assert lines[0][0] == ("(No commits to display)", COLOR_DEFAULT)
    
    def test_visual_mode_indicator_colored(self):
        """Test that visual mode indicator has default color."""
        self.view.visual_mode = True
        lines = self.view.get_display_lines(height=20, width=80, colors_enabled=True)
        
        # Find visual mode indicator at end
        if len(lines) >= 2:
            last_line = lines[-1]
            if isinstance(last_line, list):
                text = "".join(t for t, _ in last_line)
                if "VISUAL" in text:
                    for part_text, part_color in last_line:
                        assert part_color == COLOR_DEFAULT, f"Visual mode should be default: {part_text}"
    
    def test_color_consistency_across_width_changes(self):
        """Test that colors remain consistent when width changes."""
        # Get colors at different widths
        lines_wide = self.view.get_display_lines(height=20, width=100, colors_enabled=True)
        lines_narrow = self.view.get_display_lines(height=20, width=40, colors_enabled=True)
        
        # Both should have colored output
        assert all(isinstance(line, list) or line == "" for line in lines_wide)
        assert all(isinstance(line, list) or line == "" for line in lines_narrow)
        
        # Find author "Alice" in both
        alice_colors_wide = []
        alice_colors_narrow = []
        
        for line in lines_wide:
            if isinstance(line, list):
                for text, color in line:
                    if "Alice" in text:
                        alice_colors_wide.append(color)
        
        for line in lines_narrow:
            if isinstance(line, list):
                for text, color in line:
                    if "Alice" in text:
                        alice_colors_narrow.append(color)
        
        # Alice should be cyan in both
        assert all(c == COLOR_AUTHOR for c in alice_colors_wide)
        assert all(c == COLOR_AUTHOR for c in alice_colors_narrow)
    
    def test_build_colored_line_helper(self):
        """Test the _build_colored_line helper method."""
        # Test with typical prefix (format: selection datetime author)
        prefix = "[ ] 09-10 15:30 Alice "
        title = "Add feature"
        
        parts = self.view._build_colored_line(prefix, title, 20)
        
        # Should have multiple parts
        assert len(parts) >= 3
        
        # Check selection marker (includes space after)
        assert parts[0] == ("[ ] ", COLOR_DEFAULT)
        
        # Check for author part (cyan)
        author_found = False
        for text, color in parts:
            if "Alice" in text:
                assert color == COLOR_AUTHOR
                author_found = True
        assert author_found, "Author not found in colored parts"
        
        # Check for datetime part (blue)
        datetime_found = False
        for text, color in parts:
            if "09-10" in text or "15:30" in text:
                assert color == COLOR_METADATA
                datetime_found = True
        assert datetime_found, "DateTime not found in colored parts"
        
        # Check title part (default)
        title_found = False
        for text, color in parts:
            if "Add feature" in text:
                assert color == COLOR_DEFAULT
                title_found = True
        assert title_found, "Title not found in colored parts"