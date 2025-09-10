"""Main TUI application for tigs log command."""

import curses
import os
import sys
from typing import Optional

from .commits_view import CommitView
from .commit_details_view import CommitDetailsView
from .chat_view import ChatView
from .layout_manager import LayoutManager


class TigsLogApp:
    """Main TUI application for exploring commits and their associated chats."""
    
    MIN_WIDTH = 80
    MIN_HEIGHT = 24
    
    def __init__(self, store):
        """Initialize the TUI application.
        
        Args:
            store: TigsStore instance for Git operations
        """
        self.store = store
        self.running = True
        self._colors_enabled = False
        
        # Initialize layout manager
        self.layout_manager = LayoutManager()
        
        # Initialize view components
        self.commit_view = CommitView(self.store, read_only=True)
        self.commit_details_view = CommitDetailsView(self.store)
        self.chat_display_view = ChatView(self.store)
        
        # Give layout manager to commit view for horizontal scrolling
        self.commit_view.layout_manager = self.layout_manager
        
        # Load initial data
        self.commit_view.load_commits()
        
        # Load details for first commit if available
        if self.commit_view.commits:
            sha = self.commit_view.get_cursor_sha()
            if sha:
                self.commit_details_view.load_commit_details(sha)
                self.chat_display_view.load_chat(sha)
    
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
        """Main TUI loop.
        
        Args:
            stdscr: The curses standard screen
        """
        # Set up curses
        try:
            curses.curs_set(0)
        except curses.error:
            pass
        stdscr.keypad(True)
        curses.noecho()
        
        # Initialize colors if available
        self._colors_enabled = False
        if curses.has_colors() and not self._no_color():
            try:
                curses.start_color()
                try:
                    curses.use_default_colors()
                    use_default_ok = True
                except curses.error:
                    use_default_ok = False

                if use_default_ok:
                    curses.init_pair(1, -1, -1)
                else:
                    curses.init_pair(1, curses.COLOR_WHITE, curses.COLOR_BLACK)
                
                curses.init_pair(2, curses.COLOR_CYAN, -1 if use_default_ok else curses.COLOR_BLACK)
                curses.init_pair(3, curses.COLOR_GREEN, -1 if use_default_ok else curses.COLOR_BLACK)
                curses.init_pair(4, curses.COLOR_YELLOW, -1 if use_default_ok else curses.COLOR_BLACK)
                
                self._colors_enabled = True
            except curses.error:
                self._colors_enabled = False
        
        # Main loop
        while self.running:
            height, width = stdscr.getmaxyx()
            
            # Check minimum size
            if width < self.MIN_WIDTH or height < self.MIN_HEIGHT:
                stdscr.clear()
                msg = f"Terminal too small: {width}x{height} (min: {self.MIN_WIDTH}x{self.MIN_HEIGHT})"
                try:
                    stdscr.addstr(height // 2, max(0, (width - len(msg)) // 2), msg)
                except curses.error:
                    pass
                stdscr.refresh()
                key = stdscr.getch()
                if key == ord('q') or key == ord('Q'):
                    self.running = False
                continue
            
            # Clear screen
            stdscr.clear()
            
            # Calculate column widths for three-column layout
            # Commits: 30%, Details: 40%, Chat: 30%
            commit_width = max(30, width * 30 // 100)
            details_width = max(40, width * 40 // 100)
            chat_width = width - commit_width - details_width
            
            pane_height = height - 1  # Leave room for status bar
            
            # Get display lines from each view
            commit_lines = self.commit_view.get_display_lines(pane_height, commit_width)
            details_lines = self.commit_details_view.get_display_lines(pane_height, details_width)
            chat_lines = self.chat_display_view.get_display_lines(pane_height, chat_width)
            
            # Draw panes
            self._draw_pane(stdscr, 0, 0, pane_height, commit_width,
                           "Commits", True, commit_lines)
            self._draw_pane(stdscr, 0, commit_width, pane_height, details_width,
                           "Commit Details", False, details_lines)
            self._draw_pane(stdscr, 0, commit_width + details_width, pane_height, chat_width,
                           "Chat", False, chat_lines)
            
            # Draw status bar
            self._draw_status_bar(stdscr, height - 1, width)
            
            # Refresh to show everything
            stdscr.refresh()
            
            # Handle input
            key = stdscr.getch()
            if key == ord('q') or key == ord('Q'):
                self.running = False
            elif key == curses.KEY_RESIZE:
                continue
            else:
                # Handle navigation in commits view
                if self.commit_view.handle_input(key, pane_height):
                    # Cursor moved, update other views
                    sha = self.commit_view.get_cursor_sha()
                    if sha:
                        self.commit_details_view.load_commit_details(sha)
                        self.chat_display_view.load_chat(sha)
    
    def _draw_pane(self, stdscr, y: int, x: int, height: int, width: int, 
                   title: str, focused: bool, content: list) -> None:
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
        if width < 2 or height < 2:
            return
            
        # Use different border styles for focused vs unfocused
        if focused:
            tl = curses.ACS_ULCORNER
            tr = curses.ACS_URCORNER
            bl = curses.ACS_LLCORNER
            br = curses.ACS_LRCORNER
            hz = curses.ACS_HLINE
            vt = curses.ACS_VLINE
            
            if self._colors_enabled:
                stdscr.attron(curses.color_pair(2))
                stdscr.attron(curses.A_BOLD)
        else:
            tl = curses.ACS_ULCORNER
            tr = curses.ACS_URCORNER
            bl = curses.ACS_LLCORNER
            br = curses.ACS_LRCORNER
            hz = curses.ACS_HLINE
            vt = curses.ACS_VLINE
            
            if self._colors_enabled:
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
                if i + 1 < height - 1:
                    if len(line) > width - 4:
                        line = line[:width - 4]
                    stdscr.addstr(y + i + 1, x + 2, line)
                    
        except curses.error:
            pass
            
        # Reset attributes
        if focused:
            if self._colors_enabled:
                stdscr.attroff(curses.A_BOLD)
                stdscr.attroff(curses.color_pair(2))
        else:
            if self._colors_enabled:
                stdscr.attroff(curses.color_pair(1))
    
    def _draw_status_bar(self, stdscr, y: int, width: int) -> None:
        """Draw the status bar.
        
        Args:
            stdscr: The curses screen
            y: Y position for status bar
            width: Width of screen
        """
        status_text = "↑/↓: navigate | q: quit"
        
        # Use reverse video for status bar
        if self._colors_enabled:
            stdscr.attron(curses.A_REVERSE)
        
        # Clear the line and add status text
        status_line = status_text.ljust(width)[:width - 1]
        try:
            stdscr.addstr(y, 0, status_line)
        except curses.error:
            pass
            
        if self._colors_enabled:
            stdscr.attroff(curses.A_REVERSE)
    
    def _no_color(self) -> bool:
        """Check if NO_COLOR environment variable is set."""
        return os.environ.get("NO_COLOR", "").strip() != ""