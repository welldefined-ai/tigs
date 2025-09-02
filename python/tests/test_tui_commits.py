"""Tests for TUI commit view functionality."""

import pytest
from unittest.mock import Mock, MagicMock, patch
import subprocess
from datetime import datetime, timedelta

from src.tui.commits import CommitView
from src.store import TigsStore


class TestCommitView:
    """Test commit display functionality in the TUI."""
    
    def test_load_commits_basic(self):
        """Test that commits are loaded from git log."""
        mock_store = Mock(spec=TigsStore)
        mock_store.repo_path = '.'
        mock_store.list_chats.return_value = []
        
        # Mock git log output
        git_output = """sha1234567890|First commit|Author One|1700000000
sha2345678901|Second commit|Author Two|1700000100
sha3456789012|Third commit|Author Three|1700000200"""
        
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = Mock(
                stdout=git_output,
                returncode=0
            )
            
            commit_view = CommitView(mock_store)
            
            # Verify commits were loaded
            assert len(commit_view.commits) == 3
            assert commit_view.commits[0]['sha'] == 'sha1234'
            assert commit_view.commits[0]['subject'] == 'First commit'
            assert commit_view.commits[0]['author'] == 'Author One'
            
            # Verify git command was called correctly
            mock_run.assert_called_once()
            args = mock_run.call_args[0][0]
            assert 'git' in args
            assert 'log' in args
            assert '--oneline' in args
            assert '--date-order' in args
    
    def test_display_lines_formatting(self):
        """Test that commits are formatted correctly for display."""
        mock_store = Mock(spec=TigsStore)
        mock_store.repo_path = '.'
        mock_store.list_chats.return_value = ['sha1234567890']  # First commit has note
        
        commit_view = CommitView(mock_store)
        
        # Manually set commits for testing
        commit_view.commits = [
            {
                'sha': 'sha1234',
                'full_sha': 'sha1234567890',
                'subject': 'First commit with a note',
                'author': 'Author',
                'time': datetime.now() - timedelta(hours=2),
                'has_note': True
            },
            {
                'sha': 'sha2345',
                'full_sha': 'sha2345678901',
                'subject': 'Second commit without note',
                'author': 'Another',
                'time': datetime.now() - timedelta(days=1),
                'has_note': False
            }
        ]
        commit_view.items = commit_view.commits  # Update mixin reference
        
        lines = commit_view.get_display_lines(height=10)
        
        # Check formatting
        assert len(lines) == 2
        assert '>[ ]*' in lines[0]  # Cursor, selection, note indicator
        assert 'sha1234' in lines[0]
        assert 'First commit' in lines[0]
        
        assert ' [ ] ' in lines[1]  # No cursor, not selected, no note
        assert 'sha2345' in lines[1]
        assert 'Second commit' in lines[1]
    
    def test_selection_operations(self):
        """Test commit selection operations."""
        mock_store = Mock(spec=TigsStore)
        mock_store.repo_path = '.'
        mock_store.list_chats.return_value = []
        
        commit_view = CommitView(mock_store)
        
        # Set test commits
        commit_view.commits = [
            {'sha': f'sha{i}', 'full_sha': f'sha{i}full', 'subject': f'Commit {i}',
             'author': 'Test', 'time': datetime.now(), 'has_note': False}
            for i in range(5)
        ]
        commit_view.items = commit_view.commits  # Update mixin reference
        
        # Test space toggles selection
        commit_view.handle_input(ord(' '))
        assert 0 in commit_view.selected_commits
        
        commit_view.handle_input(ord(' '))
        assert 0 not in commit_view.selected_commits
        
        # Test cursor movement
        import curses
        commit_view.handle_input(curses.KEY_DOWN)
        assert commit_view.commit_cursor_idx == 1
        
        commit_view.handle_input(curses.KEY_UP)
        assert commit_view.commit_cursor_idx == 0
        
        # Test clear all
        commit_view.selected_commits.add(0)
        commit_view.selected_commits.add(1)
        commit_view.handle_input(ord('c'))
        assert len(commit_view.selected_commits) == 0
        
        # Test select all
        commit_view.handle_input(ord('a'))
        assert len(commit_view.selected_commits) == 5
    
    def test_visual_mode(self):
        """Test visual selection mode."""
        mock_store = Mock(spec=TigsStore)
        mock_store.repo_path = '.'
        mock_store.list_chats.return_value = []
        
        commit_view = CommitView(mock_store)
        
        # Set test commits
        commit_view.commits = [
            {'sha': f'sha{i}', 'full_sha': f'sha{i}full', 'subject': f'Commit {i}',
             'author': 'Test', 'time': datetime.now(), 'has_note': False}
            for i in range(5)
        ]
        commit_view.items = commit_view.commits  # Update mixin reference
        
        # Start visual mode
        commit_view.handle_input(ord('v'))
        assert commit_view.visual_mode is True
        assert commit_view.visual_start_idx == 0
        
        # Move cursor down
        import curses
        commit_view.handle_input(curses.KEY_DOWN)
        commit_view.handle_input(curses.KEY_DOWN)
        
        # Exit visual mode
        commit_view.handle_input(ord('v'))
        assert commit_view.visual_mode is False
        
        # Check that range was selected
        assert 0 in commit_view.selected_commits
        assert 1 in commit_view.selected_commits
        assert 2 in commit_view.selected_commits
    
    def test_notes_indicator(self):
        """Test that commits with notes show the * indicator."""
        mock_store = Mock(spec=TigsStore)
        mock_store.repo_path = '.'
        mock_store.list_chats.return_value = ['sha2345678901']  # Second commit has note
        
        commit_view = CommitView(mock_store)
        
        # Set test commits
        commit_view.commits = [
            {
                'sha': 'sha1234',
                'full_sha': 'sha1234567890',
                'subject': 'No note',
                'author': 'Author',
                'time': datetime.now(),
                'has_note': False
            },
            {
                'sha': 'sha2345',
                'full_sha': 'sha2345678901',
                'subject': 'Has note',
                'author': 'Author',
                'time': datetime.now(),
                'has_note': True
            }
        ]
        commit_view.items = commit_view.commits  # Update mixin reference
        
        lines = commit_view.get_display_lines(height=10)
        
        # First commit should not have *
        assert '*' not in lines[0] or '>[ ] ' in lines[0]  # No * after selection indicator
        
        # Second commit should have *
        assert '*' in lines[1]
        assert '[ ]*' in lines[1]
    
    def test_relative_time_formatting(self):
        """Test relative time formatting."""
        mock_store = Mock(spec=TigsStore)
        mock_store.repo_path = '.'
        mock_store.list_chats.return_value = []
        
        commit_view = CommitView(mock_store)
        
        # Test various time differences
        now = datetime.now()
        
        # Seconds ago
        time1 = commit_view._format_relative_time(now - timedelta(seconds=30))
        assert time1 == "now"
        
        # Minutes ago
        time2 = commit_view._format_relative_time(now - timedelta(minutes=5))
        assert time2 == "5m"
        
        # Hours ago
        time3 = commit_view._format_relative_time(now - timedelta(hours=3))
        assert time3 == "3h"
        
        # Days ago
        time4 = commit_view._format_relative_time(now - timedelta(days=2))
        assert time4 == "2d"
        
        # Weeks ago
        time5 = commit_view._format_relative_time(now - timedelta(days=14))
        assert time5 == "2w"
        
        # Months ago
        time6 = commit_view._format_relative_time(now - timedelta(days=60))
        assert time6 == "2mo"
        
        # Years ago
        time7 = commit_view._format_relative_time(now - timedelta(days=400))
        assert time7 == "1y"
    
    def test_get_selected_shas(self):
        """Test getting full SHAs of selected commits."""
        mock_store = Mock(spec=TigsStore)
        mock_store.repo_path = '.'
        mock_store.list_chats.return_value = []
        
        commit_view = CommitView(mock_store)
        
        # Set test commits
        commit_view.commits = [
            {'sha': f'sha{i}', 'full_sha': f'sha{i}fullhash', 'subject': f'Commit {i}',
             'author': 'Test', 'time': datetime.now(), 'has_note': False}
            for i in range(3)
        ]
        commit_view.items = commit_view.commits  # Update mixin reference
        
        # Select some commits
        commit_view.selected_commits = {0, 2}
        
        shas = commit_view.get_selected_shas()
        assert len(shas) == 2
        assert 'sha0fullhash' in shas
        assert 'sha2fullhash' in shas
        assert 'sha1fullhash' not in shas
    
    def test_empty_repository(self):
        """Test handling of empty repository."""
        mock_store = Mock(spec=TigsStore)
        mock_store.repo_path = '.'
        mock_store.list_chats.return_value = []
        
        with patch('subprocess.run') as mock_run:
            # Simulate git error (no commits)
            mock_run.side_effect = subprocess.CalledProcessError(128, 'git')
            
            commit_view = CommitView(mock_store)
            
            assert len(commit_view.commits) == 0
            
            lines = commit_view.get_display_lines(height=10)
            assert len(lines) == 1
            assert "(No commits to display)" in lines[0]
    
    def test_scrolling(self):
        """Test scrolling through many commits."""
        mock_store = Mock(spec=TigsStore)
        mock_store.repo_path = '.'
        mock_store.list_chats.return_value = []
        
        commit_view = CommitView(mock_store)
        
        # Create many commits
        commit_view.commits = [
            {'sha': f'sha{i:03d}', 'full_sha': f'sha{i}full', 'subject': f'Commit {i}',
             'author': 'Test', 'time': datetime.now(), 'has_note': False}
            for i in range(100)
        ]
        commit_view.items = commit_view.commits  # Update mixin reference
        
        # Small height - should trigger scrolling
        lines = commit_view.get_display_lines(height=10)
        visible_count = 10 - 2  # height - borders
        assert len(lines) == visible_count
        
        # Move cursor down past visible area
        import curses
        for _ in range(15):
            commit_view.handle_input(curses.KEY_DOWN)
        
        # Get display lines to trigger scroll adjustment
        lines = commit_view.get_display_lines(height=10)
        
        # Should have scrolled
        assert commit_view.commit_scroll_offset > 0
        
        # Get new display lines
        lines = commit_view.get_display_lines(height=10)
        
        # Cursor should be visible in the new view
        cursor_lines = [line for line in lines if line.startswith('>')]
        assert len(cursor_lines) == 1