"""Simplified TUI app that draws directly on main screen."""

import curses
import sys
from typing import List


class SimpleTUI:
    """Simplified TUI that draws everything on the main screen."""
    
    def __init__(self, store):
        """Initialize the simple TUI."""
        self.store = store
        self.focused_pane = 0
        self.running = True
        
    def run(self) -> None:
        """Run the TUI."""
        try:
            curses.wrapper(self._run)
        except KeyboardInterrupt:
            pass
        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)
            
    def _run(self, stdscr) -> None:
        """Main TUI logic."""
        curses.curs_set(0)
        stdscr.keypad(True)
        curses.noecho()
        
        while self.running:
            # Get screen dimensions
            height, width = stdscr.getmaxyx()
            
            # Clear screen
            stdscr.clear()
            
            # Calculate pane boundaries
            commit_width = int(width * 0.4)
            message_width = int(width * 0.4)
            session_start = commit_width + message_width
            
            # Draw pane borders directly on main screen
            self._draw_pane_border(stdscr, 0, 0, height - 1, commit_width, "Commits", self.focused_pane == 0)
            self._draw_pane_border(stdscr, 0, commit_width, height - 1, message_width, "Messages", self.focused_pane == 1)
            self._draw_pane_border(stdscr, 0, session_start, height - 1, width - session_start, "Sessions", self.focused_pane == 2)
            
            # Draw content
            if height > 3 and commit_width > 15:
                stdscr.addstr(2, 2, "(Commits appear here)")
            if height > 3 and message_width > 15:
                stdscr.addstr(2, commit_width + 2, "(Messages appear here)")
            if height > 3 and width - session_start > 15:
                stdscr.addstr(2, session_start + 2, "(Sessions appear here)")
            
            # Draw status bar
            status_text = "Tab: switch | q: quit"
            stdscr.attron(curses.A_REVERSE)
            stdscr.addstr(height - 1, 0, status_text.ljust(width - 1)[:width - 1])
            stdscr.attroff(curses.A_REVERSE)
            
            # Refresh
            stdscr.refresh()
            
            # Handle input
            try:
                key = stdscr.getch()
                if key == ord('q'):
                    break
                elif key == ord('\t'):
                    self.focused_pane = (self.focused_pane + 1) % 3
            except curses.error:
                pass
                
    def _draw_pane_border(self, stdscr, y, x, height, width, title, focused):
        """Draw a pane border directly on the main screen."""
        if width <= 0 or height <= 0:
            return
            
        try:
            # Top border
            if focused:
                stdscr.attron(curses.A_BOLD)
                
            # Draw corners and edges
            stdscr.addch(y, x, curses.ACS_ULCORNER)
            stdscr.addch(y, x + width - 1, curses.ACS_URCORNER)
            stdscr.addch(y + height - 1, x, curses.ACS_LLCORNER)
            stdscr.addch(y + height - 1, x + width - 1, curses.ACS_LRCORNER)
            
            # Horizontal lines
            for i in range(1, width - 1):
                stdscr.addch(y, x + i, curses.ACS_HLINE)
                stdscr.addch(y + height - 1, x + i, curses.ACS_HLINE)
            
            # Vertical lines
            for i in range(1, height - 1):
                stdscr.addch(y + i, x, curses.ACS_VLINE)
                stdscr.addch(y + i, x + width - 1, curses.ACS_VLINE)
            
            # Title
            if len(title) + 4 < width:
                title_x = x + (width - len(title) - 2) // 2
                stdscr.addstr(y, title_x, f" {title} ")
            
            if focused:
                stdscr.attroff(curses.A_BOLD)
                
        except curses.error:
            # Ignore errors from drawing outside screen
            pass