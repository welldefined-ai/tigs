"""Main TUI application for tigs store command."""

import curses
import sys
from datetime import datetime, timedelta
from typing import List, Tuple, Optional

try:
    from cligent import ChatParser
    CLIGENT_AVAILABLE = True
except ImportError:
    CLIGENT_AVAILABLE = False


class TigsStoreApp:
    """Main TUI application for selecting and storing commits/messages."""
    
    MIN_WIDTH = 80
    MIN_HEIGHT = 24
    
    def __init__(self, store):
        """Initialize the TUI application.
        
        Args:
            store: TigsStore instance for Git operations
        """
        self.store = store
        self.focused_pane = 0  # 0=commits, 1=messages, 2=sessions
        self.running = True
        
        # Session management
        self.sessions = []
        self.selected_session_idx = 0
        self.session_scroll_offset = 0
        self.chat_parser = None
        
        # Message management
        self.messages = []  # List of (role, content) tuples
        self.message_scroll_offset = 0
        self.message_cursor_idx = 0  # Current cursor position in message list
        self.selected_messages = set()  # Set of selected message indices
        self.visual_mode = False  # Visual selection mode
        self.visual_start_idx = None  # Start of visual selection
        self._needs_message_view_init = True  # Flag to init cursor position on first draw
        
        # Initialize cligent if available
        if CLIGENT_AVAILABLE:
            try:
                self.chat_parser = ChatParser('claude-code')
                self._load_sessions()
                # Load messages for the first session if available
                if self.sessions:
                    self._load_messages()
            except Exception as e:
                # Handle cligent initialization errors gracefully
                self.chat_parser = None
        
    def run(self) -> None:
        """Run the TUI application."""
        try:
            curses.wrapper(self._run)
        except KeyboardInterrupt:
            pass
        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)
            
    def _run(self, stdscr) -> None:
        """Internal run method wrapped by curses.
        
        Args:
            stdscr: Standard screen from curses
        """
        # Hide cursor
        try:
            curses.curs_set(0)
        except:
            pass
            
        # Initialize colors if available
        if curses.has_colors():
            curses.start_color()
            curses.use_default_colors()
            # Define color pairs
            curses.init_pair(1, curses.COLOR_WHITE, curses.COLOR_BLACK)  # Normal
            curses.init_pair(2, curses.COLOR_YELLOW, curses.COLOR_BLACK)  # Focused
        
        # Main loop
        while self.running:
            height, width = stdscr.getmaxyx()
            
            # Check minimum size
            if width < self.MIN_WIDTH or height < self.MIN_HEIGHT:
                # Don't exit, just show message and wait
                stdscr.clear()
                
                # Show size warning
                try:
                    stdscr.addstr(0, 0, f"Terminal too small!")
                    stdscr.addstr(2, 0, f"Required: {self.MIN_WIDTH}x{self.MIN_HEIGHT}")
                    stdscr.addstr(3, 0, f"Current:  {width}x{height}")
                    stdscr.addstr(5, 0, "Please resize terminal")
                    stdscr.addstr(6, 0, "or press 'q' to quit")
                except curses.error:
                    # Terminal is really small, just show what we can
                    try:
                        stdscr.addstr(0, 0, f"Resize: {self.MIN_WIDTH}x{self.MIN_HEIGHT}")
                    except:
                        pass
                
                stdscr.refresh()
                
                # Handle input while too small
                stdscr.timeout(100)  # Non-blocking with 100ms timeout
                key = stdscr.getch()
                
                if key == ord('q') or key == ord('Q'):
                    self.running = False
                elif key == curses.KEY_RESIZE:
                    # Terminal was resized, loop will check size again
                    pass
                    
                continue  # Skip normal drawing, check size again
            
            # Reset to blocking input for normal operation
            stdscr.timeout(-1)
            
            # Clear screen
            stdscr.clear()
            
            # Calculate pane dimensions
            pane_height = height - 1  # Reserve bottom for status bar
            commit_width = int(width * 0.4)
            message_width = int(width * 0.4)
            session_width = width - commit_width - message_width
            
            # Draw panes directly on stdscr
            self._draw_pane(stdscr, 0, 0, pane_height, commit_width, 
                           "Commits", self.focused_pane == 0,
                           ["(Commits will appear here)"])
            
            # Get message display lines
            message_lines = self._get_message_display_lines(pane_height)
            
            self._draw_pane(stdscr, 0, commit_width, pane_height, message_width,
                           "Messages", self.focused_pane == 1,
                           message_lines)
            
            # Get session display lines
            session_lines = self._get_session_display_lines(pane_height)
            
            self._draw_pane(stdscr, 0, commit_width + message_width, pane_height, session_width,
                           "Sessions", self.focused_pane == 2,
                           session_lines)
            
            # Draw status bar
            self._draw_status_bar(stdscr, height - 1, width)
            
            # Refresh to show everything
            stdscr.refresh()
            
            # Handle input
            key = stdscr.getch()
            if key == ord('q') or key == ord('Q'):
                self.running = False
            elif key == ord('\t'):  # Tab
                self.focused_pane = (self.focused_pane + 1) % 3
            elif key == curses.KEY_BTAB or key == 353:  # Shift-Tab
                self.focused_pane = (self.focused_pane - 1) % 3
            elif key == curses.KEY_RESIZE:
                pass  # Will redraw on next iteration
            elif self.focused_pane == 1:  # Messages pane focused
                self._handle_message_input(stdscr, key)
            elif self.focused_pane == 2:  # Sessions pane focused
                if key == curses.KEY_UP and self.sessions:
                    if self.selected_session_idx > 0:
                        self.selected_session_idx -= 1
                        self._load_messages()
                elif key == curses.KEY_DOWN and self.sessions:
                    if self.selected_session_idx < len(self.sessions) - 1:
                        self.selected_session_idx += 1
                        self._load_messages()
                
    def _draw_pane(self, stdscr, y: int, x: int, height: int, width: int, 
                   title: str, focused: bool, content: List[str]) -> None:
        """Draw a pane directly on stdscr.
        
        Args:
            stdscr: The curses screen
            y: Top position
            x: Left position
            height: Pane height
            width: Pane width
            title: Pane title
            focused: Whether this pane has focus
            content: Lines of content to display
        """
        if width < 3 or height < 3:
            return
            
        # Use different border styles for focused vs unfocused
        if focused:
            # Double-line box characters for focused pane
            tl = curses.ACS_ULCORNER  # Top-left
            tr = curses.ACS_URCORNER  # Top-right
            bl = curses.ACS_LLCORNER  # Bottom-left
            br = curses.ACS_LRCORNER  # Bottom-right
            hz = curses.ACS_HLINE     # Horizontal
            vt = curses.ACS_VLINE     # Vertical
            
            # Use color if available
            if curses.has_colors():
                stdscr.attron(curses.color_pair(2))
                stdscr.attron(curses.A_BOLD)
        else:
            # Single-line for unfocused
            tl = curses.ACS_ULCORNER
            tr = curses.ACS_URCORNER
            bl = curses.ACS_LLCORNER
            br = curses.ACS_LRCORNER
            hz = curses.ACS_HLINE
            vt = curses.ACS_VLINE
            
            if curses.has_colors():
                stdscr.attron(curses.color_pair(1))
        
        # Draw corners
        try:
            stdscr.addch(y, x, tl)
            stdscr.addch(y, x + width - 1, tr)
            stdscr.addch(y + height - 1, x, bl)
            stdscr.addch(y + height - 1, x + width - 1, br)
            
            # Draw horizontal lines
            for i in range(1, width - 1):
                stdscr.addch(y, x + i, hz)
                stdscr.addch(y + height - 1, x + i, hz)
            
            # Draw vertical lines
            for i in range(1, height - 1):
                stdscr.addch(y + i, x, vt)
                stdscr.addch(y + i, x + width - 1, vt)
            
            # Draw title
            if title and len(title) + 4 < width:
                title_str = f" {title} "
                title_x = x + (width - len(title_str)) // 2
                stdscr.addstr(y, title_x, title_str)
            
            # Draw content
            for i, line in enumerate(content):
                if i + 1 < height - 1:  # Leave room for border
                    if len(line) > width - 4:
                        line = line[:width - 4]
                    stdscr.addstr(y + i + 1, x + 2, line)
                    
        except curses.error:
            pass  # Ignore errors from drawing outside screen
            
        # Reset attributes
        if focused:
            if curses.has_colors():
                stdscr.attroff(curses.A_BOLD)
                stdscr.attroff(curses.color_pair(2))
        else:
            if curses.has_colors():
                stdscr.attroff(curses.color_pair(1))
                
    def _draw_status_bar(self, stdscr, y: int, width: int) -> None:
        """Draw the status bar.
        
        Args:
            stdscr: The curses screen
            y: Y position for status bar
            width: Width of screen
        """
        status_text = "Tab: switch | q: quit"
        
        # Add size warning if getting close to minimum
        height = stdscr.getmaxyx()[0]
        if width < self.MIN_WIDTH + 10 or height < self.MIN_HEIGHT + 5:
            status_text += f" | Size: {width}x{height} (min: {self.MIN_WIDTH}x{self.MIN_HEIGHT})"
        
        # Use reverse video for status bar
        stdscr.attron(curses.A_REVERSE)
        
        # Clear the line and add status text
        status_line = status_text.ljust(width)[:width - 1]
        try:
            stdscr.addstr(y, 0, status_line)
        except curses.error:
            pass
            
        stdscr.attroff(curses.A_REVERSE)
    
    def _load_sessions(self) -> None:
        """Load sessions from cligent."""
        if not self.chat_parser:
            return
            
        try:
            logs = self.chat_parser.list_logs()
            # Sort by modification time (newest first)
            self.sessions = sorted(logs, key=lambda x: x[1]['modified'], reverse=True)
            
            # Auto-select the latest session
            if self.sessions and self.selected_session_idx == 0:
                self.selected_session_idx = 0
        except Exception:
            self.sessions = []
    
    def _format_timestamp(self, timestamp_str: str) -> str:
        """Format timestamp to relative time.
        
        Args:
            timestamp_str: ISO format timestamp string
            
        Returns:
            Formatted relative time string
        """
        try:
            # Parse the timestamp
            ts = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
            now = datetime.now(ts.tzinfo) if ts.tzinfo else datetime.now()
            
            # Calculate difference
            diff = now - ts
            
            # Format based on time difference
            if diff < timedelta(minutes=1):
                return "just now"
            elif diff < timedelta(hours=1):
                mins = int(diff.total_seconds() / 60)
                return f"{mins}m ago"
            elif diff < timedelta(hours=24):
                hours = int(diff.total_seconds() / 3600)
                return f"{hours}h ago"
            elif diff < timedelta(days=2):
                return "yesterday"
            elif diff < timedelta(days=7):
                return f"{diff.days}d ago"
            else:
                # Show time for older sessions
                return ts.strftime("%m/%d %H:%M")
        except:
            # Fallback to showing part of the timestamp
            return timestamp_str[:10] if len(timestamp_str) > 10 else timestamp_str
    
    def _get_session_display_lines(self, height: int) -> List[str]:
        """Get display lines for sessions pane.
        
        Args:
            height: Available height for content
            
        Returns:
            List of formatted session lines
        """
        lines = []
        
        if not self.sessions:
            if self.chat_parser:
                lines.append("No sessions found")
            else:
                lines.append("Cligent not available")
            return lines
        
        # Calculate visible range with scrolling
        visible_count = min(height - 2, len(self.sessions))  # -2 for borders
        
        # Adjust scroll offset if needed
        if self.selected_session_idx < self.session_scroll_offset:
            self.session_scroll_offset = self.selected_session_idx
        elif self.selected_session_idx >= self.session_scroll_offset + visible_count:
            self.session_scroll_offset = self.selected_session_idx - visible_count + 1
        
        # Build display lines
        for i in range(self.session_scroll_offset, min(self.session_scroll_offset + visible_count, len(self.sessions))):
            session_id, metadata = self.sessions[i]
            timestamp = self._format_timestamp(metadata.get('modified', ''))
            
            # Format: "• timestamp" for selected, "  timestamp" for others
            if i == self.selected_session_idx:
                lines.append(f"• {timestamp}")
            else:
                lines.append(f"  {timestamp}")
        
        return lines
    
    def _load_messages(self) -> None:
        """Load messages for the currently selected session."""
        if not self.chat_parser or not self.sessions:
            self.messages = []
            return
            
        if self.selected_session_idx >= len(self.sessions):
            self.messages = []
            return
            
        try:
            session_id = self.sessions[self.selected_session_idx][0]
            # Parse the session to get messages
            conversation = self.chat_parser.parse(session_id)
            
            # Extract messages
            self.messages = []
            for msg in conversation.messages:
                # Convert role to string (it might be an enum)
                role = str(msg.role).lower()
                # Handle enum format like "Role.USER" -> "user"
                if '.' in role:
                    role = role.split('.')[-1].lower()
                content = msg.content if hasattr(msg, 'content') else str(msg)
                self.messages.append((role, content))
            
            # Clear selections when loading new messages
            self.selected_messages.clear()
            self.visual_mode = False
            self.visual_start_idx = None
            
            # Defer cursor positioning until first draw when we have screen height
            self._needs_message_view_init = True
        except Exception:
            self.messages = []
    
    def _get_message_display_lines(self, height: int) -> List[str]:
        """Get display lines for messages pane with bottom-anchored display.
        
        Args:
            height: Available height for content
            
        Returns:
            List of formatted message lines
        """
        lines = []
        
        if not self.messages:
            lines.append("(No messages to display)")
            return lines
        
        # Initialize message view on first draw when we have screen height
        if self._needs_message_view_init:
            self._init_message_view(height)
            self._needs_message_view_init = False
        
        # Get message view parameters (single source of truth)
        visible_items, start_idx, end_idx = self._message_view(height)

        # Build display lines
        for i in range(start_idx, end_idx):
            role, content = self.messages[i]
            
            # Check if selected
            is_selected = i in self.selected_messages
            
            # In visual mode, check if in range
            if self.visual_mode and self.visual_start_idx is not None:
                visual_min = min(self.visual_start_idx, self.message_cursor_idx)
                visual_max = max(self.visual_start_idx, self.message_cursor_idx)
                if visual_min <= i <= visual_max:
                    is_selected = True
            
            # Format selection indicator
            if is_selected:
                selection_indicator = "[x]"
            else:
                selection_indicator = "[ ]"
            
            # Format cursor indicator
            if i == self.message_cursor_idx:
                cursor_indicator = "▶"
            else:
                cursor_indicator = " "
            
            # Format message header
            if role == 'user':
                header = f"{cursor_indicator}{selection_indicator} User:"
            else:
                header = f"{cursor_indicator}{selection_indicator} Assistant:"
            
            lines.append(header)
            
            # Add first line of content (truncated if needed)
            content_lines = content.split('\n')
            if content_lines:
                first_line = content_lines[0][:37] + "..." if len(content_lines[0]) > 37 else content_lines[0]
                lines.append(f"    {first_line}")
        
        # Add status line if in visual mode
        if self.visual_mode:
            lines.append("")
            lines.append("-- VISUAL MODE --")
        
        return lines
    
    def _handle_message_input(self, stdscr, key: int) -> None:
        """Handle input when messages pane is focused.
        
        Args:
            stdscr: The curses screen
            key: The key pressed
        """
        if not self.messages:
            return
            
        # Get current screen dimensions for scrolling calculations
        height, _ = stdscr.getmaxyx()
        visible_items = self._visible_message_items(height)
        
        # Navigation with Up/Down arrows - move cursor and adjust scroll immediately
        if key == curses.KEY_UP:
            if self.message_cursor_idx > 0:
                self.message_cursor_idx -= 1
                # If cursor moved above visible area, scroll up
                if self.message_cursor_idx < self.message_scroll_offset:
                    self.message_scroll_offset = self.message_cursor_idx
                    
        elif key == curses.KEY_DOWN:
            if self.message_cursor_idx < len(self.messages) - 1:
                self.message_cursor_idx += 1
                # If cursor moved below visible area, scroll down to keep cursor visible
                if self.message_cursor_idx >= self.message_scroll_offset + visible_items:
                    # Calculate new scroll to keep cursor at bottom edge of visible area
                    new_scroll = self.message_cursor_idx - visible_items + 1
                    # Clamp to valid range
                    max_scroll = max(0, len(self.messages) - visible_items)
                    self.message_scroll_offset = min(new_scroll, max_scroll)
                    
                    # Double-check: if cursor is still outside after clamping, adjust cursor
                    if self.message_cursor_idx >= self.message_scroll_offset + visible_items:
                        self.message_cursor_idx = self.message_scroll_offset + visible_items - 1
        
        # Selection operations
        elif key == ord(' '):  # Space - toggle selection at cursor position
            if self.message_cursor_idx in self.selected_messages:
                self.selected_messages.remove(self.message_cursor_idx)
            else:
                self.selected_messages.add(self.message_cursor_idx)
            # Exit visual mode when using space
            self.visual_mode = False
            self.visual_start_idx = None
        
        elif key == ord('v'):  # Start visual selection mode
            if not self.visual_mode:
                self.visual_mode = True
                self.visual_start_idx = self.message_cursor_idx
            else:
                # Exit visual mode and confirm selection
                if self.visual_start_idx is not None:
                    visual_min = min(self.visual_start_idx, self.message_cursor_idx)
                    visual_max = max(self.visual_start_idx, self.message_cursor_idx)
                    for i in range(visual_min, visual_max + 1):
                        if i < len(self.messages):
                            self.selected_messages.add(i)
                self.visual_mode = False
                self.visual_start_idx = None
        
        elif key == ord('c'):  # Clear all selections
            self.selected_messages.clear()
            self.visual_mode = False
            self.visual_start_idx = None
        
        elif key == ord('a'):  # Select all messages
            for i in range(len(self.messages)):
                self.selected_messages.add(i)
            self.visual_mode = False
            self.visual_start_idx = None
        
        elif key == 27:  # Escape - cancel visual mode
            self.visual_mode = False
            self.visual_start_idx = None
    
    def _visible_message_items(self, height: int) -> int:
        """Calculate how many message items can fit in the given height.
        
        Args:
            height: Screen height
            
        Returns:
            Number of message items that can be displayed
        """
        # Rows available for content between borders
        rows = max(0, height - 2)
        
        # Reserve rows for any status footer we append
        if self.visual_mode:
            rows = max(0, rows - 2)  # One blank + "-- VISUAL MODE --"
        
        LINES_PER_MESSAGE = 2  # Header + first content line
        return max(1, rows // LINES_PER_MESSAGE)
    
    def _message_view(self, height: int):
        """Get message view parameters - single source of truth.
        
        Args:
            height: Screen height
            
        Returns:
            Tuple of (visible_items, start_idx, end_idx)
        """
        visible_items = self._visible_message_items(height)
        start_idx = self.message_scroll_offset
        end_idx = min(start_idx + visible_items, len(self.messages))
        return visible_items, start_idx, end_idx
    
    def _init_message_view(self, height: int) -> None:
        """Initialize cursor and scroll position based on actual screen height.
        
        Args:
            height: Screen height
        """
        if not self.messages:
            self.message_cursor_idx = 0
            self.message_scroll_offset = 0
            return
        
        visible_items = self._visible_message_items(height)
        
        # Show last visible_items messages, with cursor at bottom of visible area
        self.message_scroll_offset = max(0, len(self.messages) - visible_items)
        # Position cursor at bottom of visible area, ensuring room to scroll down
        self.message_cursor_idx = min(
            len(self.messages) - 1,
            self.message_scroll_offset + visible_items - 1
        )
    
    def _adjust_scroll_for_cursor(self, height: int) -> None:
        """Adjust scroll position to ensure cursor is visible.
        
        Args:
            height: Screen height to calculate visible items
        """
        if not self.messages:
            return
            
        visible_items = self._visible_message_items(height)
        
        # Ensure cursor is in visible range
        if self.message_cursor_idx < self.message_scroll_offset:
            # Cursor above visible area - scroll up
            self.message_scroll_offset = self.message_cursor_idx
        elif self.message_cursor_idx >= self.message_scroll_offset + visible_items:
            # Cursor below visible area - scroll down
            self.message_scroll_offset = max(0, self.message_cursor_idx - visible_items + 1)
        
        # Clamp scroll when list shrinks or pane resizes
        max_scroll = max(0, len(self.messages) - visible_items)
        self.message_scroll_offset = min(self.message_scroll_offset, max_scroll)