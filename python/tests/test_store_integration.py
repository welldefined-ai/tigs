"""End-to-end tests for TUI store command functionality."""

import subprocess
import threading
import time
import curses
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

import pytest
import yaml

from src.tui.store_app import TigsStoreApp
from src.tui.commits_view import CommitView
from src.store import TigsStore


class TestTUIStoreEndToEnd:
    """Test TUI store functionality with real operations."""
    
    def test_tui_store_app_initialization_with_real_cligent(self, git_repo):
        """Test TUI app initialization with real cligent data."""
        store = TigsStore(git_repo)
        
        # Create app with real store
        app = TigsStoreApp(store)
        
        # Verify app initializes correctly
        assert app.store == store
        assert hasattr(app, 'commit_view')
        assert hasattr(app, 'message_view')
        assert hasattr(app, 'log_view')
        
        # Verify cligent integration works (chat_parser can be None if cligent not available)
        assert hasattr(app, 'chat_parser')
        # Don't assert on logs availability as it depends on environment
        if app.chat_parser:
            # Just verify we can call list_logs without error
            logs = app.chat_parser.list_logs()
            assert isinstance(logs, list)  # Should return a list, even if empty
    
    
    def test_tui_commit_loading_with_real_git(self, multi_commit_repo):
        """Test commit loading with real Git repository."""
        git_repo, commits = multi_commit_repo
        store = TigsStore(git_repo)
        
        app = TigsStoreApp(store)
        
        # Load commits from real Git repo
        app.commit_view.load_commits()
        
        # Verify commits were loaded (should have at least the initial commit + 3 more)
        assert len(app.commit_view.commits) >= 4
        
        # Verify commit format (should be dicts with SHA and message)
        for commit in app.commit_view.commits:
            assert isinstance(commit, dict)
            assert 'sha' in commit or 'full_sha' in commit
            assert 'message' in commit or 'subject' in commit
            # Check SHA length
            sha = commit.get('sha') or commit.get('full_sha')
            assert len(sha) >= 7  # At least 7 chars for short SHA
            # Check message content
            message = commit.get('message') or commit.get('subject')
            assert len(message) > 0
    
    def test_store_operation_error_handling_real_git(self, git_repo, sample_yaml_content):
        """Test store operation error handling with real Git operations."""
        store = TigsStore(git_repo)
        app = TigsStoreApp(store)
        
        # Mock views
        app.commit_view = Mock()
        app.message_view = Mock()
        app.commit_view.load_commits = Mock()
        app.commit_view.clear_selection = Mock()
        app.message_view.clear_selection = Mock()
        
        # Test storing to invalid commit SHA
        app.commit_view.get_selected_shas.return_value = ['invalid-sha-that-does-not-exist']
        app.message_view.selected_messages = set([0])
        app.message_view.get_selected_messages_content = Mock(return_value=sample_yaml_content)
        
        # This should handle the error gracefully
        app._handle_store_operation(None)
        
        # Should have error message
        assert hasattr(app, 'status_message')
        assert app.status_message is not None
    
    def test_store_with_existing_notes_overwrite(self, git_repo, sample_yaml_content, git_notes_helper):
        """Test store operation with existing notes (overwrite scenario)."""
        store = TigsStore(git_repo)
        
        # First, manually add a note using tigs CLI
        from tigs.cli import main
        from click.testing import CliRunner
        runner = CliRunner()
        
        result = runner.invoke(main, ["--repo", str(git_repo), "add-chat", "-m", "Original content"])
        assert result.exit_code == 0
        commit_sha = result.output.split(":")[-1].strip()
        
        # Verify original note exists
        assert git_notes_helper.verify_note_exists(git_repo, commit_sha)
        
        # Now test TUI overwrite
        app = TigsStoreApp(store)
        app.commit_view = Mock()
        app.message_view = Mock()
        app.commit_view.load_commits = Mock()
        app.commit_view.clear_selection = Mock()
        app.message_view.clear_selection = Mock()
        
        # Set up for overwrite
        app.commit_view.get_selected_shas.return_value = [commit_sha]
        app.message_view.selected_messages = set([0])
        app.message_view.get_selected_messages_content = Mock(return_value=sample_yaml_content)
        app.commit_view.selected_commits = set([0])
        
        # Execute store (should overwrite)
        app._handle_store_operation(None)
        
        # Verify note was overwritten (handle whitespace normalization)
        stored_content = git_notes_helper.get_note_content(git_repo, commit_sha)
        assert git_notes_helper.validate_yaml_schema(stored_content)
        assert "How do I create a Python function?" in stored_content
        assert "Original content" not in stored_content
    
    def test_message_selection_integration(self, git_repo, claude_logs):
        """Test message selection with real Claude Code data."""
        if not claude_logs:
            pytest.skip("No Claude Code logs available")
            
        store = TigsStore(git_repo)
        app = TigsStoreApp(store)
        
        # Load real log
        log_id, _ = claude_logs[0]
        chat = app.chat_parser.parse(log_id)
        
        if len(chat.messages) == 0:
            pytest.skip("No messages in log")
        
        # Initialize message view with real data
        app.message_view.messages = chat.messages
        app.message_view.logs = {log_id: chat}
        
        # Test message selection
        message_count = min(3, len(chat.messages))
        app.message_view.selected_messages = set(range(message_count))
        
        # Verify selection
        assert len(app.message_view.selected_messages) == message_count
        
        # Test getting selected content
        app.chat_parser.clear_selection()
        app.chat_parser.select(log_id, list(app.message_view.selected_messages))
        yaml_content = app.chat_parser.compose()
        
        # Verify YAML format
        import yaml as yaml_lib
        data = yaml_lib.safe_load(yaml_content)
        assert data['schema'] == 'tigs.chat/v1'
        assert len(data['messages']) == message_count
    
    def test_full_tui_workflow_simulation(self, multi_commit_repo, claude_logs, git_notes_helper):
        """Simulate a full TUI workflow: load → select → store → verify."""
        if not claude_logs:
            pytest.skip("No Claude Code logs available")
            
        git_repo, commits = multi_commit_repo
        store = TigsStore(git_repo)
        app = TigsStoreApp(store)
        
        # Step 1: Load commits (real Git operation)
        app.commit_view.load_commits()
        assert len(app.commit_view.commits) >= 4
        
        # Step 2: Load messages (real cligent operation)
        log_id, _ = claude_logs[0]
        chat = app.chat_parser.parse(log_id)
        
        if len(chat.messages) == 0:
            pytest.skip("No messages in log")
        
        # Step 3: Simulate selections
        selected_commit_idx = 1  # Select second commit
        selected_message_indices = list(range(min(3, len(chat.messages))))
        
        # Mock the UI state
        app.commit_view.selected_commits = {selected_commit_idx}
        app.message_view.selected_messages = set(selected_message_indices)
        app.message_view.get_selected_messages_content = Mock()
        app.commit_view.clear_selection = Mock()
        app.message_view.clear_selection = Mock()
        app.commit_view.load_commits = Mock()
        
        # Get real commit SHA
        commit_dict = app.commit_view.commits[selected_commit_idx]
        commit_sha = commit_dict['full_sha']
        app.commit_view.get_selected_shas = Mock(return_value=[commit_sha])
        
        # Prepare real YAML content
        app.chat_parser.clear_selection()
        app.chat_parser.select(log_id, selected_message_indices)
        real_yaml = app.chat_parser.compose()
        app.message_view.get_selected_messages_content.return_value = real_yaml
        
        # Step 4: Execute store operation (real Git notes operation)
        app._handle_store_operation(None)
        
        # Step 5: Verify results
        assert git_notes_helper.verify_note_exists(git_repo, commit_sha)
        stored_content = git_notes_helper.get_note_content(git_repo, commit_sha)
        assert git_notes_helper.validate_yaml_schema(stored_content)
        # Verify essential content structure
        stored_data = yaml.safe_load(stored_content)
        expected_data = yaml.safe_load(real_yaml)
        assert stored_data['schema'] == expected_data['schema']
        assert len(stored_data['messages']) == len(expected_data['messages'])
        
        # Step 6: Verify via CLI that content is accessible
        from tigs.cli import main
        from click.testing import CliRunner
        runner = CliRunner()
        
        result = runner.invoke(main, ["--repo", str(git_repo), "show-chat", commit_sha])
        assert result.exit_code == 0
        assert git_notes_helper.validate_yaml_schema(result.output)
    
    def test_tui_app_with_empty_repository(self, tmp_path):
        """Test TUI behavior with repository that has no commits."""
        empty_repo = tmp_path / "empty_repo"
        empty_repo.mkdir()
        
        # Initialize empty Git repo
        subprocess.run(["git", "init"], cwd=empty_repo, check=True, capture_output=True)
        subprocess.run(["git", "config", "user.name", "Test User"], cwd=empty_repo, check=True)
        subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=empty_repo, check=True)
        
        store = TigsStore(empty_repo)
        app = TigsStoreApp(store)
        
        # Should handle empty repo gracefully
        app.commit_view.load_commits()
        assert len(app.commit_view.commits) == 0
        
        # Store operation should fail gracefully with no commits
        app.commit_view = Mock()
        app.message_view = Mock()
        app.commit_view.get_selected_shas.return_value = []
        app.message_view.selected_messages = set([0])
        
        app._handle_store_operation(None)
        assert "No commits selected" in app.status_message


class TestTUIDynamicLayout:
    """Test dynamic layout and resize functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.git_repo = None
        self.store = None
    
    def test_cursor_immediate_visibility_after_navigation(self):
        """Test that cursor is immediately visible after navigation.
        
        This comprehensive e2e test simulates user navigation and verifies
        that the cursor remains visible at all times.
        """
        mock_store = Mock()
        mock_store.repo_path = '/test/repo'
        mock_store.list_chats.return_value = []
        
        # Create enough commits to require scrolling
        commits_data = []
        for i in range(30):
            commits_data.append(f"sha{i:02d}|Commit {i}|Author{i}|{1234567890 + i}")
        
        with patch('subprocess.run') as mock_run:
            mock_run.return_value.returncode = 0
            mock_run.return_value.stdout = "\n".join(commits_data)
            
            app = TigsStoreApp(mock_store)
            
            # Focus on commits pane
            app.focused_pane = 0
            
            # Test navigation scenarios
            test_cases = [
                (10, "Move to middle"),
                (20, "Move to later position"),
                (5, "Move back up"),
                (25, "Move near end"),
                (0, "Move to beginning"),
            ]
            
            for target_pos, description in test_cases:
                # Navigate to target position
                while app.commit_view.commit_cursor_idx < target_pos:
                    app.commit_view.handle_input(curses.KEY_DOWN)
                while app.commit_view.commit_cursor_idx > target_pos:
                    app.commit_view.handle_input(curses.KEY_UP)
                
                # Get display lines
                lines = app.commit_view.get_display_lines(20, 80)
                
                # Verify cursor is visible
                cursor_visible = any(line.startswith('>') for line in lines)
                assert cursor_visible, f"{description}: Cursor at position {target_pos} is not visible!"
    
    def test_resize_behavior(self):
        """Test TUI handles resize correctly."""
        # Create a mock git repo
        from unittest.mock import Mock
        mock_store = Mock()
        mock_store.repo_path = '/test/repo'
        mock_store.list_chats.return_value = []
        
        with patch('subprocess.run') as mock_run:
            mock_run.return_value.returncode = 0
            mock_run.return_value.stdout = "abc123|Test commit|Author|1234567890"
            
            app = TigsStoreApp(mock_store)
            
            # Mock stdscr for testing
            mock_stdscr = Mock()
            
            # Test resize to different sizes
            for height, width in [(24, 80), (40, 120), (20, 60)]:
                mock_stdscr.getmaxyx.return_value = (height, width)
                
                # Handle resize
                app._handle_resize(mock_stdscr)
                
                # After resize, cached_widths should be None (forcing recalculation)
                assert app.layout_manager.cached_widths is None
                
                # Should reset message view init
                assert app.message_view._needs_message_view_init == True
    
    def test_commit_title_soft_wrap(self):
        """Test soft wrapping of long commit titles."""
        mock_store = Mock()
        mock_store.repo_path = '/test/repo'
        mock_store.list_chats.return_value = []
        
        with patch('subprocess.run') as mock_run:
            mock_run.return_value.returncode = 0
            mock_run.return_value.stdout = "abc123|" + ("A" * 100) + "|Author|1234567890"
            
            view = CommitView(mock_store)
            
            # Should have a very long commit subject
            assert len(view.commits[0]['subject']) == 100
            
            # Test that long titles wrap instead of scroll
            display_lines = view.get_display_lines(height=10, width=60)
            
            # Should have multiple lines for the long commit title
            assert len(display_lines) > 1
            
            # First line should contain cursor, selection, and datetime
            first_line = display_lines[0]
            assert "02-14" in first_line  # Timestamp 1234567890 = 02-14 07:31 (MM-DD format)
            
            # Navigation should still work (up/down, not left/right for scrolling)
            result = view.handle_input(curses.KEY_DOWN)
            # Result depends on if there are more commits, but shouldn't crash
    
    def test_commit_title_format_spacing(self):
        """Test that commit title format has exactly one space between [] and datetime."""
        mock_store = Mock()
        mock_store.repo_path = '/test/repo'
        mock_store.list_chats.return_value = []
        
        with patch('subprocess.run') as mock_run:
            mock_run.return_value.returncode = 0
            mock_run.return_value.stdout = "abc123|Short title|TestAuthor|1734567890"
            
            view = CommitView(mock_store)
            
            # Test normal commit (no note, not selected)
            display_lines = view.get_display_lines(height=10, width=80)
            first_line = display_lines[0]
            
            # Should have format: ">[ ] 12-19 08:24 TestAuthor Short title"
            # Check that there's exactly one space between ] and the datetime
            assert "] 12-19" in first_line  # One space between ] and MM-DD
            assert "]  12-19" not in first_line  # Not two spaces
            
            # Test with note indicator
            view.commits_with_notes = {"abc123"}  # Add note
            view.commits[0]['has_note'] = True
            display_lines = view.get_display_lines(height=10, width=80)
            first_line = display_lines[0]
            
            # Should have format: ">[ ]*12-19 08:24 TestAuthor Short title"
            # With note indicator (*), format is ">[ ]*" then datetime
            assert "]*" in first_line  # Note indicator after checkbox
            
            # Test selected item
            view.selected_commits.add(0)
            display_lines = view.get_display_lines(height=10, width=80)
            first_line = display_lines[0]
            
            # Should have format: ">[x]*12-19 08:24 TestAuthor Short title"
            # Selected with note should have both indicators (x and *) with no extra space
            assert "[x]*" in first_line  # Selected checkbox with note indicator

    def test_dynamic_width_calculation(self):
        """Test dynamic width calculation with various scenarios."""
        mock_store = Mock()
        mock_store.repo_path = '/test/repo'
        mock_store.list_chats.return_value = []
        
        with patch('subprocess.run') as mock_run:
            mock_run.return_value.returncode = 0
            mock_run.return_value.stdout = "abc123|Short subject|Author|1234567890\ndef456|Very long subject that should affect width calculation|Author|1234567890"
            
            app = TigsStoreApp(mock_store)
            
            # Test normal terminal width
            commit_w, msg_w, log_w = app.layout_manager.calculate_column_widths(
                120, 
                [c['subject'] for c in app.commit_view.commits],
                5
            )
            
            assert commit_w >= app.layout_manager.MIN_COMMIT_WIDTH
            assert msg_w >= app.layout_manager.MIN_MESSAGE_WIDTH
            assert log_w == app.layout_manager.MIN_LOG_WIDTH
            assert commit_w + msg_w + log_w == 120
            
            # Test narrow terminal
            commit_w2, msg_w2, log_w2 = app.layout_manager.calculate_column_widths(
                80, 
                [c['subject'] for c in app.commit_view.commits],
                5
            )
            
            # Should still meet minimums
            assert commit_w2 >= app.layout_manager.MIN_COMMIT_WIDTH or msg_w2 >= app.layout_manager.MIN_MESSAGE_WIDTH
            assert commit_w2 + msg_w2 + log_w2 == 80
            
            # Commit width should be smaller on narrow terminal
            assert commit_w2 <= commit_w
    
    def test_variable_message_heights(self):
        """Test message display with variable heights."""
        mock_store = Mock()
        mock_store.repo_path = '/test/repo'
        mock_store.list_chats.return_value = []
        
        with patch('subprocess.run') as mock_run:
            mock_run.return_value.returncode = 0
            mock_run.return_value.stdout = "abc123|Test commit|Author|1234567890"
            
            app = TigsStoreApp(mock_store)
        
        # Set up messages with different content lengths
        app.message_view.messages = [
            ('user', 'Short message', None),
            ('assistant', 'This is a very long response that should wrap to multiple lines when displayed in a narrow terminal window and take up more vertical space', None),
            ('user', 'Multi\nline\nmessage\nwith\nbreaks', None),
        ]
        
        # Test with narrow width
        heights = app.message_view._calculate_message_heights(app.message_view.messages, 30)
        
        assert heights[0] == 3  # Short message: header + content + separator
        assert heights[1] > 3   # Long message should wrap
        assert heights[2] == 7  # Multi-line: header + 5 lines + separator
        
        # Test visible calculation
        app.message_view.message_cursor_idx = 1
        app.message_view.message_scroll_offset = 0
        
        visible_count, start_idx, end_idx = app.message_view._get_visible_messages_variable(15, heights)
        
        # Should handle variable heights appropriately
        assert visible_count > 0
        assert start_idx <= 1 < end_idx  # Cursor should be visible
    
    def test_extremely_large_message(self):
        """Test handling of message that fills entire window."""
        mock_store = Mock()
        mock_store.repo_path = '/test/repo'
        mock_store.list_chats.return_value = []
        
        with patch('subprocess.run') as mock_run:
            mock_run.return_value.returncode = 0
            mock_run.return_value.stdout = "abc123|Test commit|Author|1234567890"
            
            app = TigsStoreApp(mock_store)
        
        # Create a message with lots of content
        huge_content = "\n".join([f"This is line {i} of a very long message" for i in range(50)])
        app.message_view.messages = [
            ('user', 'Normal message', None),
            ('assistant', huge_content, None),
            ('user', 'Another normal message', None),
        ]
        
        # Focus on huge message
        app.message_view.message_cursor_idx = 1
        app.message_view.message_scroll_offset = 0
        
        heights = app.message_view._calculate_message_heights(app.message_view.messages, 40)
        
        # Huge message should have large height
        assert heights[1] > 20
        
        # With small window, should show only the huge message
        visible_count, start_idx, end_idx = app.message_view._get_visible_messages_variable(15, heights)
        
        assert visible_count == 1
        assert start_idx == 1
        assert end_idx == 2
    
    def test_no_logs_layout(self):
        """Test layout when no logs are available."""
        mock_store = Mock()
        mock_store.repo_path = '/test/repo'
        mock_store.list_chats.return_value = []
        
        with patch('subprocess.run') as mock_run:
            mock_run.return_value.returncode = 0
            mock_run.return_value.stdout = "abc123|Test commit|Author|1234567890"
            
            app = TigsStoreApp(mock_store)
            app.chat_parser = None
            
            # Should handle no logs gracefully
            commit_titles = ["Test commit"]
            commit_w, msg_w, log_w = app.layout_manager.calculate_column_widths(120, commit_titles, 0)
            
            assert log_w == 0
            assert commit_w + msg_w == 120
            assert msg_w >= app.layout_manager.MIN_MESSAGE_WIDTH
    
    def test_commit_display_with_width_parameter(self):
        """Test commit display respects width parameter."""
        mock_store = Mock()
        mock_store.repo_path = '/test/repo'
        mock_store.list_chats.return_value = []
        
        with patch('subprocess.run') as mock_run:
            mock_run.return_value.returncode = 0
            mock_run.return_value.stdout = "abc123|This is a very long commit subject that should be handled properly|Author|1234567890"
            
            view = CommitView(mock_store)
            
            # Test with realistic width (new min is 60)
            lines = view.get_display_lines(20, 70)
            assert len(lines) > 0
            
            # All lines should fit in the specified width (accounting for borders)
            for line in lines:
                if line and not line.startswith("--"):  # Skip visual mode indicators
                    assert len(line) <= 66  # 70 - 4 for borders
            
            # Test with wider width
            lines_wide = view.get_display_lines(20, 100)
            
            # With more width, should show more of the commit subject
            assert len(lines_wide) > 0
            # The wider display should have lines that fit within the wider boundary
            for line in lines_wide:
                if line and not line.startswith("--"):
                    assert len(line) <= 96  # 100 - 4 for borders
