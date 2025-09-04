"""True end-to-end test for cursor visibility that detects the frame delay bug.

This test verifies what the user actually SEES, frame by frame.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from unittest.mock import Mock, patch, MagicMock
import curses

# Set curses constants if not in a real terminal
if not hasattr(curses, 'KEY_DOWN'):
    curses.KEY_DOWN = 258
    curses.KEY_UP = 259


def test_cursor_frame_by_frame():
    """Test that simulates frame-by-frame user experience.
    
    The bug: When user presses a key at frame N, they see:
    - Frame N: Display captured BEFORE their key press
    - Frame N+1: Display shows result of their key press
    
    In buggy code, there's a delay where user's action doesn't appear immediately.
    """
    
    # Mock cligent only for this test
    with patch.dict('sys.modules', {'cligent': MagicMock()}):
        from src.tui.app import TigsStoreApp
        
        # Setup
        mock_store = Mock()
        mock_store.repo_path = '/test/repo'  
        mock_store.list_chats.return_value = []
        
        commits_data = [f"sha{i:02d}|Commit {i}|Author{i}|{1234567890 + i}" for i in range(30)]
        
        with patch('subprocess.run') as mock_run:
            mock_run.return_value.returncode = 0
            mock_run.return_value.stdout = "\n".join(commits_data)
            
            app = TigsStoreApp(mock_store)
            
            # Track what user sees each frame
            frames = []
            
            def capture_frame(frame_num, user_action=None):
                """Capture what user sees in one frame."""
                
                # Get current cursor position BEFORE any action
                cursor_before = app.commit_view.commit_cursor_idx
                
                # Get display (in buggy code, this happens BEFORE input handling)
                display_lines = app.commit_view.get_display_lines(12, 60)
                
                # Find cursor in display
                cursor_in_display = None
                for line in display_lines:
                    if line.startswith('>'):
                        import re
                        match = re.search(r'Commit (\d+)', line)
                        if match:
                            cursor_in_display = int(match.group(1))
                        break
                
                # Now handle user action (in buggy code, this happens AFTER display)
                if user_action == 'DOWN':
                    app.commit_view.handle_input(curses.KEY_DOWN)
                
                cursor_after = app.commit_view.commit_cursor_idx
                
                frame_info = {
                    'frame': frame_num,
                    'action': user_action,
                    'cursor_before_action': cursor_before,
                    'cursor_after_action': cursor_after,
                    'cursor_shown_to_user': cursor_in_display,
                    'display_lines': display_lines[:3]  # Just first few for debug
                }
                
                frames.append(frame_info)
                return frame_info
            
            # Simulate user interaction
            print("\n=== Frame-by-frame User Experience ===\n")
            
            # Initial frame
            f = capture_frame(0)
            print(f"Frame 0 (initial): User sees cursor at Commit {f['cursor_shown_to_user']}")
            
            # User navigates down several times
            for i in range(10):
                f = capture_frame(i+1, 'DOWN')
                
                # Check what user sees vs reality
                if f['cursor_shown_to_user'] != f['cursor_after_action']:
                    # User sees wrong position!
                    print(f"Frame {f['frame']}: USER SEES WRONG CURSOR!")
                    print(f"  User pressed DOWN, cursor moved to {f['cursor_after_action']}")
                    print(f"  But display shows cursor at {f['cursor_shown_to_user']}")
                    print(f"  This is a {f['cursor_after_action'] - f['cursor_shown_to_user']} frame delay!")
                    
                    # This is the bug!
                    raise AssertionError(
                        f"FRAME DELAY BUG DETECTED!\n"
                        f"At frame {f['frame']}, after pressing DOWN:\n"
                        f"  - Cursor actually moved to Commit {f['cursor_after_action']}\n"
                        f"  - But user sees cursor at Commit {f['cursor_shown_to_user']}\n"
                        f"User experiences a visual delay where their action doesn't appear immediately!\n"
                        f"This happens because display is captured BEFORE input is processed."
                    )
                else:
                    print(f"Frame {f['frame']}: Cursor at Commit {f['cursor_shown_to_user']} (correct)")
            
            print("\n✓ No frame delay detected - cursor updates immediately")


if __name__ == "__main__":
    try:
        test_cursor_frame_by_frame()
        print("\n✅ Frame-by-frame test PASSED")
    except AssertionError as e:
        print(f"\n❌ Frame-by-frame test FAILED:\n{e}")