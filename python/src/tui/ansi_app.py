"""ANSI-based TUI implementation as fallback for curses issues."""

import sys
import tty
import termios
import select
import os


class AnsiTUI:
    """Simple ANSI-based TUI."""
    
    # ANSI escape sequences
    CLEAR_SCREEN = "\033[2J"
    MOVE_HOME = "\033[H"
    SAVE_CURSOR = "\033[s"
    RESTORE_CURSOR = "\033[u"
    HIDE_CURSOR = "\033[?25l"
    SHOW_CURSOR = "\033[?25h"
    REVERSE = "\033[7m"
    NORMAL = "\033[0m"
    BOLD = "\033[1m"
    
    def __init__(self, store):
        """Initialize ANSI TUI."""
        self.store = store
        self.focused_pane = 0
        self.running = True
        self.old_attrs = None
        
    def run(self) -> None:
        """Run the ANSI TUI."""
        try:
            self._setup()
            self._main_loop()
        except KeyboardInterrupt:
            pass
        finally:
            self._cleanup()
            
    def _setup(self) -> None:
        """Set up terminal for raw input."""
        # Check if we're in an interactive terminal
        if not sys.stdin.isatty() or not sys.stdout.isatty():
            raise OSError("Not running in an interactive terminal")
            
        try:
            self.old_attrs = termios.tcgetattr(sys.stdin.fileno())
            tty.setraw(sys.stdin.fileno())
            print(self.HIDE_CURSOR, end='', flush=True)
        except (termios.error, OSError) as e:
            raise OSError(f"Cannot set up terminal: {e}") from e
        
    def _cleanup(self) -> None:
        """Restore terminal state."""
        print(self.SHOW_CURSOR, end='', flush=True)
        if self.old_attrs:
            termios.tcsetattr(sys.stdin.fileno(), termios.TCSADRAIN, self.old_attrs)
        print()  # Final newline
        
    def _main_loop(self) -> None:
        """Main event loop."""
        while self.running:
            self._draw_screen()
            
            # Check for input
            if select.select([sys.stdin], [], [], 0.1)[0]:
                key = sys.stdin.read(1)
                if key == 'q':
                    self.running = False
                elif key == '\t':
                    self.focused_pane = (self.focused_pane + 1) % 3
                    
    def _draw_screen(self) -> None:
        """Draw the entire screen."""
        # Get terminal size
        rows, cols = os.get_terminal_size()
        
        # Clear screen and move to home
        print(self.CLEAR_SCREEN + self.MOVE_HOME, end='')
        
        # Calculate pane widths
        commit_width = int(cols * 0.4)
        message_width = int(cols * 0.4) 
        session_width = cols - commit_width - message_width
        
        # Draw panes line by line
        for row in range(rows - 1):  # Leave last row for status
            line = ""
            
            # Commit pane
            if row == 0:
                # Top border with title
                title = " Commits "
                border_char = "=" if self.focused_pane == 0 else "-"
                padding = (commit_width - len(title)) // 2
                line += border_char * padding + title + border_char * (commit_width - padding - len(title))
            elif row == 1 and commit_width > 20:
                line += "| (Commits appear here)" + " " * (commit_width - 23) + "|"
            elif row == 1:
                line += "|" + " " * (commit_width - 2) + "|"
            elif 1 < row < rows - 2:
                line += "|" + " " * (commit_width - 2) + "|"
            else:
                line += "-" * commit_width
                
            # Message pane  
            if row == 0:
                title = " Messages "
                border_char = "=" if self.focused_pane == 1 else "-"
                padding = (message_width - len(title)) // 2
                line += border_char * padding + title + border_char * (message_width - padding - len(title))
            elif row == 1 and message_width > 22:
                line += "| (Messages appear here)" + " " * (message_width - 24) + "|"
            elif row == 1:
                line += "|" + " " * (message_width - 2) + "|"
            elif 1 < row < rows - 2:
                line += "|" + " " * (message_width - 2) + "|"
            else:
                line += "-" * message_width
                
            # Session pane
            if row == 0:
                title = " Sessions "
                border_char = "=" if self.focused_pane == 2 else "-"
                padding = (session_width - len(title)) // 2
                line += border_char * padding + title + border_char * (session_width - padding - len(title))
            elif row == 1 and session_width > 22:
                line += "| (Sessions appear here)" + " " * (session_width - 24) + "|"
            elif row == 1:
                line += "|" + " " * (session_width - 2) + "|" 
            elif 1 < row < rows - 2:
                line += "|" + " " * (session_width - 2) + "|"
            else:
                line += "-" * session_width
                
            print(line[:cols])
            
        # Status bar
        status = "Tab: switch | q: quit"
        status_line = self.REVERSE + status.ljust(cols)[:cols] + self.NORMAL
        print(status_line, end='', flush=True)