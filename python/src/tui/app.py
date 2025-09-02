"""Main TUI application for tigs store command."""

import curses
import sys
from datetime import datetime, timedelta
from typing import List

from cligent import ChatParser

from .commits import CommitView
from .messages import MessageView
from .logs import LogView


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
        self.focused_pane = 0  # 0=commits, 1=messages, 2=logs
        self.running = True
        self.status_message = ""  # Status message to display
        self.status_message_time = None  # When status was set
        
        # Initialize chat parser
        try:
            self.chat_parser = ChatParser('claude-code')
        except Exception:
            # Handle cligent initialization errors gracefully
            self.chat_parser = None
        
        # Initialize view components
        self.commit_view = CommitView(self.store)
        self.message_view = MessageView(self.chat_parser)
        self.log_view = LogView(self.chat_parser)
        
        # Load initial data
        if self.chat_parser:
            self.log_view.load_logs()
            # Auto-load messages for the first log
            log_id = self.log_view.get_selected_log_id()
            if log_id:
                self.message_view.load_messages(log_id)
        
    def run(self) -> None:
        """Run the TUI application."""
        try:
            curses.wrapper(self._run)
        except KeyboardInterrupt:
            pass  # Exit gracefully on Ctrl+C
        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)
    
    def _run(self, stdscr) -> None:
        """Main TUI loop.
        
        Args:
            stdscr: The curses standard screen
        """
        # Set up curses
        curses.curs_set(0)  # Hide cursor
        stdscr.keypad(True)  # Enable special keys
        curses.noecho()
        
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
            
            # Get commit display lines
            commit_lines = self.commit_view.get_display_lines(pane_height)
            
            # DEBUG: Add status to see if commits are loading
            if not commit_lines:
                commit_lines = [f"DEBUG: {len(self.commit_view.commits)} commits"]
            
            # Draw panes directly on stdscr
            self._draw_pane(stdscr, 0, 0, pane_height, commit_width, 
                           "Commits", self.focused_pane == 0,
                           commit_lines)
            
            # Get message display lines
            message_lines = self.message_view.get_display_lines(pane_height)
            
            self._draw_pane(stdscr, 0, commit_width, pane_height, message_width,
                           "Messages", self.focused_pane == 1,
                           message_lines)
            
            # Get log display lines
            log_lines = self.log_view.get_display_lines(pane_height)
            
            self._draw_pane(stdscr, 0, commit_width + message_width, pane_height, session_width,
                           "Logs", self.focused_pane == 2,
                           log_lines)
            
            # Draw status bar
            self._draw_status_bar(stdscr, height - 1, width)
            
            # Refresh to show everything
            stdscr.refresh()
            
            # Handle input
            key = stdscr.getch()
            if key == ord('q') or key == ord('Q'):
                self.running = False
            elif key == ord('\n') or key == 10:  # Enter key
                self._handle_store_operation(stdscr)
            elif key == ord('\t'):  # Tab
                self.focused_pane = (self.focused_pane + 1) % 3
            elif key == curses.KEY_BTAB or key == 353:  # Shift-Tab
                self.focused_pane = (self.focused_pane - 1) % 3
            elif key == curses.KEY_RESIZE:
                pass  # Will redraw on next iteration
            elif self.focused_pane == 0:  # Commits pane focused
                self.commit_view.handle_input(key)
            elif self.focused_pane == 1:  # Messages pane focused
                self.message_view.handle_input(stdscr, key, pane_height)
            elif self.focused_pane == 2:  # Logs pane focused
                if self.log_view.handle_input(key):
                    # Log selection changed, reload messages
                    log_id = self.log_view.get_selected_log_id()
                    if log_id:
                        self.message_view.load_messages(log_id)
                
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
                title_text = f" {title} "
                title_x = x + (width - len(title_text)) // 2
                stdscr.addstr(y, title_x, title_text)
                
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
        # Show status message if recent (within 5 seconds)
        if self.status_message and self.status_message_time:
            elapsed = datetime.now() - self.status_message_time
            if elapsed < timedelta(seconds=5):
                status_text = self.status_message
            else:
                self.status_message = ""  # Clear old message
                status_text = "Tab: switch | Enter: store | q: quit"
        else:
            status_text = "Tab: switch | Enter: store | q: quit"
        
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
    
    def _handle_store_operation(self, stdscr) -> None:
        """Handle the store operation when Enter is pressed.
        
        Args:
            stdscr: The curses screen for prompts
        """
        # Get selected commits
        selected_commits = self.commit_view.get_selected_shas()
        
        # Validate that both commits and messages are selected
        if not selected_commits:
            self.status_message = "Error: No commits selected"
            self.status_message_time = datetime.now()
            return
        
        if not self.message_view.selected_messages:
            self.status_message = "Error: No messages selected"
            self.status_message_time = datetime.now()
            return
        
        # Get the content in cligent's export format
        chat_content = self.message_view.get_selected_messages_content()
        num_messages = len(self.message_view.selected_messages)
        
        # Store to each selected commit
        stored_count = 0
        overwrite_count = 0
        errors = []
        
        for sha in selected_commits:
            try:
                # Try to add the chat
                self.store.add_chat(sha, chat_content)
                stored_count += 1
            except ValueError as e:
                if "already has a chat" in str(e):
                    # Offer to overwrite
                    if self._prompt_overwrite(stdscr, sha):
                        try:
                            # Remove existing and add new
                            self.store.remove_chat(sha)
                            self.store.add_chat(sha, chat_content)
                            stored_count += 1
                            overwrite_count += 1
                        except Exception as ex:
                            errors.append(f"{sha[:7]}: {str(ex)}")
                else:
                    errors.append(f"{sha[:7]}: {str(e)}")
        
        # Update status message
        if errors:
            self.status_message = f"Errors: {'; '.join(errors)}"
        else:
            msg = f"Stored {num_messages} messages → {stored_count} commits"
            if overwrite_count > 0:
                msg += f" ({overwrite_count} overwritten)"
            self.status_message = msg
        
        self.status_message_time = datetime.now()
        
        # Clear selections after successful storage
        if stored_count > 0:
            self.commit_view.clear_selection()
            self.message_view.clear_selection()
            
            # Update commit indicators (reload to get updated notes status)
            self.commit_view.load_commits()
    
    def _prompt_overwrite(self, stdscr, sha: str) -> bool:
        """Prompt user to overwrite existing note.
        
        Args:
            stdscr: The curses screen
            sha: The commit SHA
            
        Returns:
            True if user wants to overwrite
        """
        # Simple implementation - always overwrite for now
        # Could be enhanced with actual prompt dialog
        return True