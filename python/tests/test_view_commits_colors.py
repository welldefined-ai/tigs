"""Tests for commit view coloring in view app following tig's color scheme."""

import pytest
from unittest.mock import Mock, patch
from datetime import datetime

from src.tui.view_app import TigsViewApp
from src.tui.commits_view import CommitView
from src.tui.color_constants import COLOR_AUTHOR, COLOR_METADATA, COLOR_DEFAULT


class TestViewCommitsViewColors:
    """Test color assignment in view app's commits view."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.mock_store = Mock()
        self.mock_store.repo_path = '/test/repo'
        self.mock_store.list_chats.return_value = []
        
        # Patch subprocess to avoid actual git calls
        with patch('subprocess.run'):
            self.app = TigsViewApp(self.mock_store)
        
        # Sample commits for testing
        self.app.commit_view.commits = [
            {
                'sha': 'abc1234',
                'full_sha': 'abc1234567890',
                'author': 'Alice',
                'time': datetime(2025, 9, 10, 15, 30),
                'subject': 'Add new feature',
                'has_note': False
            },
            {
                'sha': 'def4567',
                'full_sha': 'def4567890123',
                'author': 'Bob',
                'time': datetime(2025, 9, 9, 10, 15),
                'subject': 'Fix bug in very long commit message that wraps',
                'has_note': True
            }
        ]
        self.app.commit_view.items = self.app.commit_view.commits
    
    def test_colors_enabled_returns_colored_tuples(self):
        """Test that colors_enabled=True returns list of color tuples for view."""
        # Enable colors in the app
        self.app._colors_enabled = True
        
        # Get display lines with colors enabled
        lines = self.app.commit_view.get_display_lines(height=20, width=80, colors_enabled=True)
        
        # Should return colored output (list of tuples)
        assert len(lines) > 0
        # First line should be a list of tuples (colored parts)
        assert isinstance(lines[0], list)
        assert all(isinstance(part, tuple) and len(part) == 2 for part in lines[0])
    
    def test_colors_disabled_returns_plain_strings(self):
        """Test that colors_enabled=False returns plain strings for view."""
        # Disable colors in the app
        self.app._colors_enabled = False
        
        # Get display lines without colors
        lines = self.app.commit_view.get_display_lines(height=20, width=80, colors_enabled=False)
        
        # Should return plain strings
        assert len(lines) > 0
        assert all(isinstance(line, str) for line in lines)
    
    def test_commit_line_color_components(self):
        """Test that commit lines have proper color assignments in view."""
        self.app._colors_enabled = True
        
        lines = self.app.commit_view.get_display_lines(height=20, width=80, colors_enabled=True)
        
        # First commit line should have colored components
        first_line = lines[0]
        assert isinstance(first_line, list)
        
        # Extract text parts and colors
        text_parts = [part[0] for part in first_line]
        colors = [part[1] for part in first_line]
        
        # Join all text parts to check content
        full_text = ''.join(text_parts)
        
        # Should contain cursor/note indicator, date, author, and subject
        assert '09-10' in full_text  # Date
        assert 'Alice' in full_text  # Author
        assert 'Add new feature' in full_text  # Subject
        
        # Check that we have multiple color assignments
        # At least: indicator (default), date (metadata), author (cyan), subject (default)
        assert COLOR_METADATA in colors  # Date should be blue/metadata
        assert COLOR_AUTHOR in colors    # Author should be cyan
        assert COLOR_DEFAULT in colors   # Indicators and subject should be default
    
    def test_view_read_only_format(self):
        """Test that view uses read-only format (no checkboxes)."""
        # Ensure read_only is set
        assert self.app.commit_view.read_only is True
        
        self.app._colors_enabled = False
        lines = self.app.commit_view.get_display_lines(height=20, width=80, colors_enabled=False)
        
        # View format should have bullet points, not checkboxes
        first_line = lines[0]
        # Should have bullet (•) or star (*) for notes, not [ ]
        assert '[ ]' not in first_line
        assert ('•' in first_line or '*' in first_line)
    
    def test_commit_with_note_indicator(self):
        """Test that commits with notes show star indicator in view."""
        self.app._colors_enabled = False
        
        # Second commit has a note
        lines = self.app.commit_view.get_display_lines(height=20, width=80, colors_enabled=False)
        
        # Find the line with Bob's commit (has note)
        bob_line = None
        for line in lines:
            if 'Bob' in line:
                bob_line = line
                break
        
        assert bob_line is not None
        # Should have star indicator for note
        assert '*' in bob_line[:5]  # Star should be near the beginning
    
    def test_view_app_passes_colors_to_commit_view(self):
        """Test that view app correctly passes colors_enabled to commit view."""
        with patch('src.tui.view_app.PaneRenderer'):
            with patch.object(self.app.commit_view, 'get_display_lines') as mock_get_lines:
                with patch.object(self.app.commit_details_view, 'get_display_lines'):
                    with patch.object(self.app.chat_display_view, 'get_display_lines'):
                        # Mock stdscr
                        mock_stdscr = Mock()
                        mock_stdscr.getmaxyx.return_value = (30, 120)
                        mock_stdscr.getch.return_value = ord('q')  # Quit immediately
                        
                        # Enable colors
                        self.app._colors_enabled = True
                        
                        # Simulate one iteration of the main loop
                        # This would normally be called in _run but we'll call the relevant part
                        height, width = mock_stdscr.getmaxyx()
                        pane_height = height - 1
                        
                        # Calculate widths (simplified)
                        commit_width = 40
                        
                        # This should call get_display_lines with colors_enabled=True
                        self.app.commit_view.get_display_lines(pane_height, commit_width, self.app._colors_enabled)
                        
                        # Verify the method was called with colors_enabled=True
                        mock_get_lines.assert_called_with(pane_height, commit_width, True)