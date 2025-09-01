"""Tests for TUI message view functionality."""

import pytest
from unittest.mock import Mock, MagicMock, patch
from datetime import datetime

from src.tui.app import TigsStoreApp


class TestMessageView:
    """Test message display functionality in the TUI."""
    
    @patch('src.tui.app.CLIGENT_AVAILABLE', True)
    @patch('src.tui.app.ChatParser')
    def test_load_messages_basic(self, mock_parser_class):
        """Test that messages are loaded when a session is selected."""
        # Setup mock store
        mock_store = Mock()
        
        # Setup mock ChatParser
        mock_parser = MagicMock()
        mock_parser_class.return_value = mock_parser
        
        # Setup mock sessions
        mock_parser.list_logs.return_value = [
            ('session-1', {'modified': '2024-01-01T10:00:00Z'}),
            ('session-2', {'modified': '2024-01-01T09:00:00Z'})
        ]
        
        # Setup mock conversation with messages
        mock_conversation = Mock()
        mock_message1 = Mock()
        mock_message1.role = 'user'
        mock_message1.content = 'Hello, can you help me?'
        
        mock_message2 = Mock()
        mock_message2.role = 'assistant' 
        mock_message2.content = 'Of course! What do you need help with?'
        
        mock_conversation.messages = [mock_message1, mock_message2]
        mock_parser.parse.return_value = mock_conversation
        
        # Create app and test
        app = TigsStoreApp(mock_store)
        
        # Verify sessions were loaded
        assert len(app.sessions) == 2
        assert app.sessions[0][0] == 'session-1'  # Newest first
        
        # Verify messages were loaded for first session
        assert len(app.messages) == 2
        assert app.messages[0] == ('user', 'Hello, can you help me?')
        assert app.messages[1] == ('assistant', 'Of course! What do you need help with?')
        
        # Verify parse was called with correct session ID
        mock_parser.parse.assert_called_once_with('session-1')
    
    @patch('src.tui.app.CLIGENT_AVAILABLE', True)
    @patch('src.tui.app.ChatParser')
    def test_message_display_lines(self, mock_parser_class):
        """Test that messages are formatted correctly for display."""
        # Setup
        mock_store = Mock()
        mock_parser = MagicMock()
        mock_parser_class.return_value = mock_parser
        mock_parser.list_logs.return_value = []
        
        app = TigsStoreApp(mock_store)
        
        # Manually set messages
        app.messages = [
            ('user', 'This is a test message'),
            ('assistant', 'This is a response that is very long and should be truncated when displayed in the pane')
        ]
        
        # Get display lines
        lines = app._get_message_display_lines(height=10)
        
        # Verify formatting (new format with cursor and selection indicators)
        assert '[ ] User:' in lines[0] or '>[ ] User:' in lines[0]  # May have cursor
        assert 'This is a test message' in lines[1]
        assert '[ ] Assistant:' in lines[2] or '>[ ] Assistant:' in lines[2]
        assert '...' in lines[3]  # Long message should be truncated
    
    @patch('src.tui.app.CLIGENT_AVAILABLE', True)
    @patch('src.tui.app.ChatParser')
    def test_session_selection_triggers_message_load(self, mock_parser_class):
        """Test that changing session selection loads new messages."""
        # Setup
        mock_store = Mock()
        mock_parser = MagicMock()
        mock_parser_class.return_value = mock_parser
        
        # Setup sessions
        mock_parser.list_logs.return_value = [
            ('session-1', {'modified': '2024-01-01T10:00:00Z'}),
            ('session-2', {'modified': '2024-01-01T09:00:00Z'})
        ]
        
        # Setup different messages for each session
        mock_conv1 = Mock()
        mock_msg1 = Mock(role='user', content='Session 1 message')
        mock_conv1.messages = [mock_msg1]
        
        mock_conv2 = Mock()
        mock_msg2 = Mock(role='user', content='Session 2 message')
        mock_conv2.messages = [mock_msg2]
        
        mock_parser.parse.side_effect = [mock_conv1, mock_conv2]
        
        # Create app
        app = TigsStoreApp(mock_store)
        
        # Initial messages should be from session 1
        assert app.messages[0] == ('user', 'Session 1 message')
        
        # Change selection
        app.selected_session_idx = 1
        app._load_messages()
        
        # Messages should now be from session 2
        assert app.messages[0] == ('user', 'Session 2 message')
        assert mock_parser.parse.call_count == 2
        mock_parser.parse.assert_called_with('session-2')
    
    @patch('src.tui.app.CLIGENT_AVAILABLE', True)
    @patch('src.tui.app.ChatParser')
    def test_message_selection_operations(self, mock_parser_class):
        """Test message selection operations."""
        # Setup
        mock_store = Mock()
        mock_parser = MagicMock()
        mock_parser_class.return_value = mock_parser
        mock_parser.list_logs.return_value = []
        
        app = TigsStoreApp(mock_store)
        
        # Set some messages
        app.messages = [
            ('user', 'Message 1'),
            ('assistant', 'Message 2'),
            ('user', 'Message 3')
        ]
        
        # Mock stdscr for screen dimensions
        mock_stdscr = Mock()
        mock_stdscr.getmaxyx.return_value = (24, 80)
        pane_height = 24 - 1  # Terminal height minus status bar
        
        # Set cursor position and test space key toggles selection
        app.message_cursor_idx = 0
        app._handle_message_input(mock_stdscr, ord(' '), pane_height)
        assert 0 in app.selected_messages
        
        app._handle_message_input(mock_stdscr, ord(' '), pane_height)
        assert 0 not in app.selected_messages
        
        # Test cursor movement
        app.message_cursor_idx = 0
        app._handle_message_input(mock_stdscr, 258, pane_height)  # KEY_DOWN
        assert app.message_cursor_idx == 1
        
        app._handle_message_input(mock_stdscr, 259, pane_height)  # KEY_UP  
        assert app.message_cursor_idx == 0
        
        # Test clear selections
        app.selected_messages.add(0)
        app.selected_messages.add(1)
        app._handle_message_input(mock_stdscr, ord('c'), pane_height)
        assert len(app.selected_messages) == 0
        
        # Test select all
        app._handle_message_input(mock_stdscr, ord('a'), pane_height)
        assert len(app.selected_messages) == 3  # All 3 messages selected
    
    @patch('src.tui.app.CLIGENT_AVAILABLE', False)
    def test_no_cligent_available(self):
        """Test app handles missing cligent gracefully."""
        mock_store = Mock()
        app = TigsStoreApp(mock_store)
        
        assert app.chat_parser is None
        assert app.messages == []
        assert app.sessions == []
        
        # Should not crash when getting display lines
        lines = app._get_message_display_lines(height=10)
        assert '(No messages to display)' in lines[0]
    
    def test_role_enum_conversion(self):
        """Test conversion of Role enums to strings."""
        mock_store = Mock()
        
        with patch('src.tui.app.CLIGENT_AVAILABLE', True), \
             patch('src.tui.app.ChatParser') as mock_parser_class:
            
            mock_parser = MagicMock()
            mock_parser_class.return_value = mock_parser
            mock_parser.list_logs.return_value = [
                ('session-1', {'modified': '2024-01-01T10:00:00Z'})
            ]
            
            # Test with Role enum (like Role.USER)
            mock_conv = Mock()
            mock_msg1 = Mock()
            mock_msg1.role = Mock()
            mock_msg1.role.__str__ = Mock(return_value='Role.USER')
            mock_msg1.content = 'Test content'
            
            # Test with Role enum (like Role.ASSISTANT)
            mock_msg2 = Mock()
            mock_msg2.role = Mock()
            mock_msg2.role.__str__ = Mock(return_value='Role.ASSISTANT')
            mock_msg2.content = 'Assistant response'
            
            mock_conv.messages = [mock_msg1, mock_msg2]
            mock_parser.parse.return_value = mock_conv
            
            app = TigsStoreApp(mock_store)
            
            assert app.messages[0] == ('user', 'Test content')
            assert app.messages[1] == ('assistant', 'Assistant response')
    
    def test_real_cligent_integration(self):
        """Test with real cligent if available in current directory."""
        try:
            from cligent import ChatParser
            
            # Test if we can find real sessions in current directory
            cp = ChatParser('claude-code')
            logs = cp.list_logs()
            
            if logs:
                # We have real data - test the full integration
                mock_store = Mock()
                app = TigsStoreApp(mock_store)
                
                # Should have loaded real sessions and messages
                assert len(app.sessions) > 0, "Should find real sessions"
                assert len(app.messages) > 0, "Should load real messages"
                
                # Test display generation
                lines = app._get_message_display_lines(height=20)
                assert len(lines) > 0, "Should generate display lines"
                
                # Verify message format
                for role, content in app.messages:
                    assert role in ['user', 'assistant', 'system']
                    assert isinstance(content, str)
                    assert len(content) > 0
            else:
                pytest.skip("No Claude Code sessions found in current directory")
                
        except ImportError:
            pytest.skip("cligent not available")
    
    def test_cursor_and_selection_indicators(self):
        """Test the new cursor (>) and selection ([x]) indicators."""
        mock_store = Mock()
        
        with patch('src.tui.app.CLIGENT_AVAILABLE', True), \
             patch('src.tui.app.ChatParser') as mock_parser_class:
            
            mock_parser = MagicMock()
            mock_parser_class.return_value = mock_parser
            mock_parser.list_logs.return_value = []
            
            app = TigsStoreApp(mock_store)
            
            # Set up test messages
            app.messages = [
                ('user', 'First message'),
                ('assistant', 'Second message'),
                ('user', 'Third message')
            ]
            
            # Mark that initialization has already been done to prevent override
            app._needs_message_view_init = False
            app.message_scroll_offset = 0  # Show all messages from the top
            app.message_cursor_idx = 1  # Cursor on second message
            app.selected_messages.add(2)  # Third message selected
            
            lines = app._get_message_display_lines(height=20)
            
            # Check that cursor indicator appears on the right message
            cursor_lines = [line for line in lines if line.startswith('▶')]
            assert len(cursor_lines) == 1, "Should have exactly one cursor indicator"
            assert '▶[ ] Assistant:' in cursor_lines[0], "Cursor should be on second message (assistant)"
            
            # Check that selection indicator appears on the right message  
            selected_lines = [line for line in lines if '[x]' in line]
            assert len(selected_lines) == 1, "Should have exactly one selected message"
            assert ' [x] User:' in selected_lines[0], "Third message should be selected (user)"
            
            # Check that unselected messages have [ ] indicator  
            unselected_lines = [line for line in lines if '[ ]' in line and not line.startswith('▶')]
            assert len(unselected_lines) == 1, "Should have one unselected message without cursor"
            assert ' [ ] User:' in unselected_lines[0], "First message should be unselected without cursor"
    
    def test_cursor_scrolling_up_and_down(self):
        """Test that cursor can scroll up then back down to reach all messages."""
        mock_store = Mock()
        
        with patch('src.tui.app.CLIGENT_AVAILABLE', True), \
             patch('src.tui.app.ChatParser') as mock_parser_class:
            
            mock_parser = MagicMock()
            mock_parser_class.return_value = mock_parser
            mock_parser.list_logs.return_value = []
            
            app = TigsStoreApp(mock_store)
            
            # Create many messages to test scrolling
            app.messages = [(f'user', f'Message {i}') for i in range(50)]
            
            # Start with cursor at bottom (like real app)
            visible_count = 18  # height=20 - 2 borders
            app.message_scroll_offset = len(app.messages) - visible_count  # 32
            app.message_cursor_idx = len(app.messages) - 1  # 49
            
            mock_stdscr = Mock()
            mock_stdscr.getmaxyx.return_value = (20, 80)
            pane_height = 20 - 1  # Terminal height minus status bar
            
            print(f"\nTesting scrolling with {len(app.messages)} messages")
            print(f"Initial: cursor={app.message_cursor_idx}, scroll={app.message_scroll_offset}")
            
            # Verify cursor is initially visible
            lines = app._get_message_display_lines(height=20)
            cursor_visible = any(line.startswith('▶') for line in lines)
            assert cursor_visible, "Cursor should be visible at start"
            
            # Phase 1: Scroll UP significantly 
            for i in range(25):  # Move up 25 positions
                app._handle_message_input(mock_stdscr, 259, pane_height)  # KEY_UP
                lines = app._get_message_display_lines(height=20)  # Trigger scrolling logic
                
                # Cursor should always be visible
                cursor_visible = any(line.startswith('▶') for line in lines)
                assert cursor_visible, f"Cursor should be visible after UP movement {i+1}"
            
            middle_cursor = app.message_cursor_idx
            middle_scroll = app.message_scroll_offset
            print(f"After UP: cursor={middle_cursor}, scroll={middle_scroll}")
            
            # Should have moved up significantly
            assert app.message_cursor_idx < len(app.messages) - 10, "Cursor should have moved up significantly"
            
            # Phase 2: Scroll DOWN back to bottom
            for i in range(30):  # Move down 30 positions (more than we moved up)
                old_cursor = app.message_cursor_idx
                old_scroll = app.message_scroll_offset
                
                app._handle_message_input(mock_stdscr, 258, pane_height)  # KEY_DOWN
                lines = app._get_message_display_lines(height=20)  # Trigger scrolling logic
                
                # Cursor should always be visible
                cursor_visible = any(line.startswith('▶') for line in lines)
                assert cursor_visible, f"Cursor should be visible after DOWN movement {i+1}"
                
                # If cursor moved, we should be able to reach the bottom eventually
                if app.message_cursor_idx == len(app.messages) - 1:
                    print(f"Reached bottom at step {i+1}: cursor={app.message_cursor_idx}, scroll={app.message_scroll_offset}")
                    break
            else:
                # This will fail if we can't reach the bottom
                assert False, f"Failed to reach bottom after 30 DOWN moves. Final: cursor={app.message_cursor_idx}, scroll={app.message_scroll_offset}"
            
            # Verify we can reach the bottom
            assert app.message_cursor_idx == len(app.messages) - 1, "Should be able to reach the last message"
            
            final_lines = app._get_message_display_lines(height=20)
            cursor_visible = any(line.startswith('▶') for line in final_lines)
            assert cursor_visible, "Cursor should be visible at the bottom"
            
            print(f"✅ Test passed: Can scroll up then back down to bottom")
    
    def test_cursor_scrolling_with_real_scenario(self):
        """Test scrolling scenario that matches user experience."""
        mock_store = Mock()
        
        with patch('src.tui.app.CLIGENT_AVAILABLE', True), \
             patch('src.tui.app.ChatParser') as mock_parser_class:
            
            mock_parser = MagicMock()
            mock_parser_class.return_value = mock_parser
            mock_parser.list_logs.return_value = []
            
            app = TigsStoreApp(mock_store)
            
            # Create scenario similar to real usage - many messages
            app.messages = [(f'user', f'Message {i}') for i in range(100)]
            
            # Initialize as the real app would - cursor at very last message
            visible_count = 10  # Conservative estimate
            app.message_scroll_offset = max(0, len(app.messages) - visible_count)  # 90
            app.message_cursor_idx = len(app.messages) - 1  # 99
            
            mock_stdscr = Mock()
            mock_stdscr.getmaxyx.return_value = (24, 80)
            pane_height = 24 - 1  # Terminal height minus status bar
            
            print(f"\nReal scenario test with {len(app.messages)} messages")
            print(f"Initial: cursor={app.message_cursor_idx}, scroll={app.message_scroll_offset}")
            
            # Test the specific issue: cursor not visible initially
            lines = app._get_message_display_lines(height=24)
            cursor_lines = [i for i, line in enumerate(lines) if line.startswith('▶')]
            print(f"Cursor visibility at start: {len(cursor_lines) > 0} (found on lines: {cursor_lines})")
            
            # Simulate user pressing UP several times to find cursor
            up_presses_needed = 0
            for i in range(50):  # User keeps pressing UP
                up_presses_needed += 1
                app._handle_message_input(mock_stdscr, 259, pane_height)  # KEY_UP
                lines = app._get_message_display_lines(height=24)
                
                cursor_lines = [j for j, line in enumerate(lines) if line.startswith('▶')]
                if cursor_lines:
                    print(f"Cursor became visible after {up_presses_needed} UP presses")
                    print(f"  Position: cursor={app.message_cursor_idx}, scroll={app.message_scroll_offset}")
                    break
            else:
                assert False, "Cursor never became visible after 50 UP presses"
            
            # Now test if we can scroll back down
            reached_bottom = False
            down_presses = 0
            max_cursor_reached = app.message_cursor_idx
            
            for i in range(200):  # Try many DOWN presses
                old_cursor = app.message_cursor_idx
                down_presses += 1
                
                app._handle_message_input(mock_stdscr, 258, pane_height)  # KEY_DOWN
                lines = app._get_message_display_lines(height=24)
                
                max_cursor_reached = max(max_cursor_reached, app.message_cursor_idx)
                
                # Check if we reached the last message
                if app.message_cursor_idx == len(app.messages) - 1:
                    reached_bottom = True
                    print(f"✅ Reached bottom after {down_presses} DOWN presses")
                    print(f"  Final: cursor={app.message_cursor_idx}, scroll={app.message_scroll_offset}")
                    break
                    
                # If cursor stops moving, we have a problem
                if app.message_cursor_idx == old_cursor:
                    # Allow a few non-movements (cursor might hit boundaries)
                    consecutive_stops = getattr(self, '_stop_count', 0) + 1
                    setattr(self, '_stop_count', consecutive_stops)
                    if consecutive_stops > 5:
                        break
                else:
                    setattr(self, '_stop_count', 0)
            
            # Report results
            print(f"Max cursor position reached: {max_cursor_reached} (target: {len(app.messages)-1})")
            
            if not reached_bottom:
                assert False, f"Could not scroll back to bottom! Max cursor reached: {max_cursor_reached}/{len(app.messages)-1}, final scroll: {app.message_scroll_offset}"
            
            print(f"✅ Successfully scrolled up then back down to bottom")
    
    def test_cursor_visibility_with_mismatched_visible_count(self):
        """Test cursor visibility when initialization visible_count differs from actual height."""
        mock_store = Mock()
        
        with patch('src.tui.app.CLIGENT_AVAILABLE', True), \
             patch('src.tui.app.ChatParser') as mock_parser_class:
            
            mock_parser = MagicMock()
            mock_parser_class.return_value = mock_parser
            mock_parser.list_logs.return_value = []
            
            app = TigsStoreApp(mock_store)
            
            # Create many messages (more than the hardcoded visible_count=10 in initialization)
            app.messages = [(f'user', f'Message {i}') for i in range(50)]
            
            # Simulate the initialization logic manually (this happens in _load_messages)
            visible_count = 10  # This is hardcoded in the initialization
            app.message_scroll_offset = len(app.messages) - visible_count  # 40
            app.message_cursor_idx = len(app.messages) - 1  # 49
            
            print(f"\nTesting cursor visibility mismatch")
            print(f"Messages: {len(app.messages)}")
            print(f"Init scroll: {app.message_scroll_offset} (based on visible_count={visible_count})")
            print(f"Init cursor: {app.message_cursor_idx}")
            
            # Now test with different actual screen heights
            test_heights = [15, 20, 25, 30]  # Different terminal sizes
            
            for height in test_heights:
                mock_stdscr = Mock()
                mock_stdscr.getmaxyx.return_value = (height, 80)
                
                lines = app._get_message_display_lines(height=height)
                actual_visible_count = height - 2  # -2 for borders
                
                # Calculate what the visible range should be
                start_range = app.message_scroll_offset
                end_range = min(start_range + actual_visible_count, len(app.messages))
                
                cursor_visible = any(line.startswith('▶') for line in lines)
                cursor_in_range = start_range <= app.message_cursor_idx < end_range
                
                print(f"  Height {height}: visible_count={actual_visible_count}, range=[{start_range},{end_range}), cursor={app.message_cursor_idx}")
                print(f"    Cursor in range: {cursor_in_range}, Cursor visible: {cursor_visible}")
                
                # The cursor should always be visible after display generation
                if not cursor_visible:
                    print(f"    ❌ PROBLEM: Cursor not visible with height {height}")
                    print(f"    Expected scroll after display: {app.message_scroll_offset}")
                    
                    # This should fail to detect the bug
                    assert cursor_visible, f"Cursor should be visible with height {height}, but wasn't. Range=[{start_range},{end_range}), cursor={app.message_cursor_idx}"
            
            print(f"✅ Cursor visibility test passed for all heights")
    
    def test_user_reported_scrolling_issue(self):
        """Test the specific scrolling issue reported by user."""
        mock_store = Mock()
        
        with patch('src.tui.app.CLIGENT_AVAILABLE', True), \
             patch('src.tui.app.ChatParser') as mock_parser_class:
            
            mock_parser = MagicMock()
            mock_parser_class.return_value = mock_parser
            mock_parser.list_logs.return_value = []
            
            app = TigsStoreApp(mock_store)
            
            # Simulate a realistic conversation with many messages
            app.messages = [(f'user' if i % 3 == 0 else 'assistant', f'Message content {i}') for i in range(200)]
            
            # Initialize cursor position like _load_messages would do
            if app.messages:
                app.message_cursor_idx = len(app.messages) - 1
                app.message_scroll_offset = max(0, len(app.messages) - 15)
            
            mock_stdscr = Mock()
            mock_stdscr.getmaxyx.return_value = (24, 80)  # Standard terminal size
            pane_height = 24 - 1  # Terminal height minus status bar
            
            print(f"\nUser issue reproduction test:")
            print(f"Messages: {len(app.messages)}")
            print(f"Initial: cursor={app.message_cursor_idx}, scroll={app.message_scroll_offset}")
            
            # Test 1: Cursor should be visible immediately
            lines = app._get_message_display_lines(height=24)
            initial_cursor_visible = any(line.startswith('▶') for line in lines)
            print(f"Cursor visible at startup: {initial_cursor_visible}")
            
            if not initial_cursor_visible:
                print(f"❌ ISSUE REPRODUCED: Cursor not visible initially!")
                assert False, "Cursor should be visible at startup"
            
            # Test 2: Scroll up significantly (user's scenario)
            print(f"\\nScrolling UP to simulate user experience...")
            up_count = 0
            for i in range(100):  # Scroll up significantly
                app._handle_message_input(mock_stdscr, 259, pane_height)  # KEY_UP
                up_count += 1
                lines = app._get_message_display_lines(height=24)
                
                cursor_visible = any(line.startswith('▶') for line in lines)
                if not cursor_visible:
                    print(f"❌ Lost cursor after {up_count} UP presses")
                    assert False, f"Cursor should always be visible, lost after {up_count} UP presses"
            
            mid_position = app.message_cursor_idx
            print(f"After {up_count} UP presses: cursor at {mid_position}")
            
            # Test 3: Try to scroll back down (user's main complaint)  
            print(f"\\nScrolling DOWN to test the reported issue...")
            down_count = 0
            last_cursor_position = app.message_cursor_idx
            stuck_count = 0
            
            for i in range(300):  # Try many DOWN presses
                app._handle_message_input(mock_stdscr, 258, pane_height)  # KEY_DOWN
                down_count += 1
                lines = app._get_message_display_lines(height=24)
                
                # Check if cursor is visible
                cursor_visible = any(line.startswith('▶') for line in lines)
                if not cursor_visible:
                    print(f"❌ Lost cursor during DOWN scroll after {down_count} presses")
                    assert False, f"Cursor should always be visible during DOWN scroll"
                
                # Check if we're making progress
                if app.message_cursor_idx == last_cursor_position:
                    stuck_count += 1
                    if stuck_count > 10:  # If stuck for 10 consecutive presses
                        if app.message_cursor_idx < len(app.messages) - 1:
                            print(f"❌ ISSUE REPRODUCED: Cursor stuck at {app.message_cursor_idx}, can't reach bottom!")
                            print(f"   Scroll position: {app.message_scroll_offset}")
                            print(f"   Target: {len(app.messages) - 1}")
                            assert False, f"Cursor stuck at {app.message_cursor_idx}, cannot scroll down to bottom"
                        break  # We reached the bottom
                else:
                    stuck_count = 0
                    last_cursor_position = app.message_cursor_idx
                
                # Check if we reached the bottom successfully
                if app.message_cursor_idx == len(app.messages) - 1:
                    print(f"✅ Successfully reached bottom after {down_count} DOWN presses")
                    break
            
            # Final verification
            final_position = app.message_cursor_idx
            expected_bottom = len(app.messages) - 1
            
            if final_position == expected_bottom:
                print(f"✅ Test passed: Can scroll up then back down to reach all messages")
                print(f"   Final position: {final_position}/{expected_bottom}")
            else:
                print(f"❌ ISSUE CONFIRMED: Cannot reach bottom!")
                print(f"   Reached: {final_position}/{expected_bottom}")
                print(f"   Difference: {expected_bottom - final_position} messages unreachable")
                assert False, f"Cannot reach bottom! Got to {final_position}, expected {expected_bottom}"