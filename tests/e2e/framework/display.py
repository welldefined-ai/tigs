"""Display capture functionality for terminal applications.

This module handles capturing and parsing terminal output, including
ANSI escape sequences, to provide a clean representation of what the
user would see on screen.
"""

import re
from typing import List, Optional, Tuple


class Display:
    """Represents a terminal display state.
    
    This is similar to Tig's terminal buffer capture, storing the current
    state of what would be visible on the terminal screen.
    """
    
    def __init__(self, lines: int = 30, columns: int = 80):
        """Initialize display with given dimensions.
        
        Args:
            lines: Number of lines in the terminal
            columns: Number of columns in the terminal
        """
        self.lines = lines
        self.columns = columns
        self.buffer: List[str] = [' ' * columns for _ in range(lines)]
        self.cursor_row = 0
        self.cursor_col = 0
        
    def clear(self) -> None:
        """Clear the display buffer."""
        self.buffer = [' ' * self.columns for _ in range(self.lines)]
        self.cursor_row = 0
        self.cursor_col = 0
        
    def set_cursor(self, row: int, col: int) -> None:
        """Set cursor position.
        
        Args:
            row: Row number (0-based)
            col: Column number (0-based)
        """
        self.cursor_row = max(0, min(row, self.lines - 1))
        self.cursor_col = max(0, min(col, self.columns - 1))
        
    def write_char(self, char: str) -> None:
        """Write a character at the current cursor position.
        
        Args:
            char: Character to write
        """
        if self.cursor_row < self.lines and self.cursor_col < self.columns:
            # Convert buffer line to list for mutation
            line = list(self.buffer[self.cursor_row])
            line[self.cursor_col] = char
            self.buffer[self.cursor_row] = ''.join(line)
            
            # Advance cursor
            self.cursor_col += 1
            if self.cursor_col >= self.columns:
                self.cursor_col = 0
                self.cursor_row += 1
                self._clamp_and_scroll_cursor()
                
    def write_text(self, text: str) -> None:
        """Write text starting at current cursor position.
        
        Args:
            text: Text to write
        """
        for char in text:
            if char == '\n':
                self.cursor_col = 0
                self.cursor_row += 1
                self._clamp_and_scroll_cursor()
            elif char == '\r':
                self.cursor_col = 0
            elif char == '\b':
                if self.cursor_col > 0:
                    self.cursor_col -= 1
            elif char == '\t':
                # Tab to next 8-character boundary
                self.cursor_col = ((self.cursor_col // 8) + 1) * 8
                if self.cursor_col >= self.columns:
                    self.cursor_col = 0
                    self.cursor_row += 1
                    self._clamp_and_scroll_cursor()
            else:
                self.write_char(char)
                
    def _clamp_and_scroll_cursor(self) -> None:
        """Clamp cursor row and scroll if needed."""
        if self.cursor_row >= self.lines:
            # Scroll up and clamp cursor to bottom line
            lines_to_scroll = self.cursor_row - self.lines + 1
            self.scroll_up(lines_to_scroll)
            self.cursor_row = self.lines - 1
                
    def scroll_up(self, lines: int = 1) -> None:
        """Scroll the display up by the specified number of lines.
        
        Args:
            lines: Number of lines to scroll
        """
        for _ in range(lines):
            # Remove top line and add blank line at bottom
            self.buffer.pop(0)
            self.buffer.append(' ' * self.columns)
            
    def get_line(self, line_num: int) -> str:
        """Get a specific line from the display.
        
        Args:
            line_num: Line number (0-based)
            
        Returns:
            The line content, right-stripped of whitespace
        """
        if 0 <= line_num < len(self.buffer):
            return self.buffer[line_num].rstrip()
        return ""
        
    def get_display(self) -> str:
        """Get the entire display as a string.
        
        Returns:
            Multi-line string representation of the display
        """
        # Right-strip each line and join with newlines
        lines = [line.rstrip() for line in self.buffer]
        
        # Remove trailing empty lines (like Tig output)
        while lines and not lines[-1]:
            lines.pop()
            
        return '\n'.join(lines)
        
    def find_text(self, pattern: str, start_line: int = 0) -> Optional[Tuple[int, int]]:
        """Find text pattern in the display.
        
        Args:
            pattern: Text pattern to find
            start_line: Line to start searching from
            
        Returns:
            Tuple of (line, column) if found, None otherwise
        """
        for i in range(start_line, len(self.buffer)):
            line = self.buffer[i]
            col = line.find(pattern)
            if col != -1:
                return (i, col)
        return None


class DisplayCapture:
    """Captures and processes terminal output to maintain display state.
    
    This class parses ANSI escape sequences and maintains a virtual
    terminal display, similar to how Tig's test harness captures
    screen content.
    """
    
    def __init__(self, lines: int = 30, columns: int = 80):
        """Initialize display capture.
        
        Args:
            lines: Terminal height in lines  
            columns: Terminal width in columns
        """
        self.display = Display(lines, columns)
        self._buffer = b""
        
        # ANSI escape sequence patterns
        self._ansi_escape = re.compile(rb'\x1b\[[0-9;]*[a-zA-Z]')
        self._cursor_pos = re.compile(rb'\x1b\[(\d+);(\d+)H')
        self._cursor_up = re.compile(rb'\x1b\[(\d*)A')
        self._cursor_down = re.compile(rb'\x1b\[(\d*)B') 
        self._cursor_forward = re.compile(rb'\x1b\[(\d*)C')
        self._cursor_backward = re.compile(rb'\x1b\[(\d*)D')
        self._clear_screen = re.compile(rb'\x1b\[2J')
        self._clear_line = re.compile(rb'\x1b\[K')
        
    def process_output(self, data: bytes) -> None:
        """Process new output data and update display state.
        
        Args:
            data: Raw bytes from terminal output
        """
        self._buffer += data
        text = data.decode('utf-8', errors='ignore')
        
        # Process the text, handling ANSI escape sequences
        self._process_text(text)
        
    def _process_text(self, text: str) -> None:
        """Process text with ANSI escape sequences.
        
        Args:
            text: Text to process (may contain ANSI sequences)
        """
        # Convert back to bytes for regex processing
        text_bytes = text.encode('utf-8', errors='ignore')
        
        i = 0
        while i < len(text_bytes):
            # Look for ANSI escape sequences
            if text_bytes[i:i+1] == b'\x1b':
                # Try to match various escape sequences
                
                # Cursor position: ESC[row;colH or ESC[row;colf
                match = self._cursor_pos.match(text_bytes, i)
                if match:
                    row = int(match.group(1)) - 1  # Convert to 0-based
                    col = int(match.group(2)) - 1
                    self.display.set_cursor(row, col)
                    i = match.end()
                    continue
                
                # Handle alternate cursor position formats
                if i + 1 < len(text_bytes) and text_bytes[i+1:i+2] == b'[':
                    # Look for other cursor positioning sequences
                    seq_match = re.match(rb'\x1b\[(\d+);(\d+)[Hf]', text_bytes[i:])
                    if seq_match:
                        row = int(seq_match.group(1)) - 1
                        col = int(seq_match.group(2)) - 1
                        self.display.set_cursor(row, col)
                        i += seq_match.end()
                        continue
                    
                    # Clear entire screen: ESC[2J
                    if text_bytes[i:i+4] == b'\x1b[2J':
                        self.display.clear()
                        i += 4
                        continue
                        
                    # Clear line: ESC[K or ESC[0K
                    if text_bytes[i:i+3] == b'\x1b[K' or text_bytes[i:i+4] == b'\x1b[0K':
                        self._clear_line_from_cursor()
                        i += 3 if text_bytes[i:i+3] == b'\x1b[K' else 4
                        continue
                        
                    # Clear from cursor to end of screen: ESC[0J or ESC[J
                    if text_bytes[i:i+4] == b'\x1b[0J' or text_bytes[i:i+3] == b'\x1b[J':
                        self._clear_from_cursor_to_end()
                        i += 4 if text_bytes[i:i+4] == b'\x1b[0J' else 3
                        continue
                        
                    # Clear from beginning of screen to cursor: ESC[1J
                    if text_bytes[i:i+4] == b'\x1b[1J':
                        self._clear_from_beginning_to_cursor()
                        i += 4
                        continue
                
                # Cursor movement sequences
                match = self._cursor_up.match(text_bytes, i)
                if match:
                    n = int(match.group(1)) if match.group(1) else 1
                    self.display.cursor_row = max(0, self.display.cursor_row - n)
                    i = match.end()
                    continue
                    
                match = self._cursor_down.match(text_bytes, i)
                if match:
                    n = int(match.group(1)) if match.group(1) else 1
                    self.display.cursor_row = min(self.display.lines - 1, 
                                                self.display.cursor_row + n)
                    i = match.end()
                    continue
                    
                match = self._cursor_forward.match(text_bytes, i)
                if match:
                    n = int(match.group(1)) if match.group(1) else 1
                    self.display.cursor_col = min(self.display.columns - 1,
                                                self.display.cursor_col + n)
                    i = match.end()
                    continue
                    
                match = self._cursor_backward.match(text_bytes, i)
                if match:
                    n = int(match.group(1)) if match.group(1) else 1
                    self.display.cursor_col = max(0, self.display.cursor_col - n)
                    i = match.end()
                    continue
                
                # Generic ANSI escape sequence - skip it (this catches color codes, etc.)
                match = self._ansi_escape.match(text_bytes, i)
                if match:
                    i = match.end()
                    continue
                    
                # Single ESC character - skip it
                i += 1
            else:
                # Regular character - write it
                char = chr(text_bytes[i])
                if char == '\r':
                    # Carriage return - move to beginning of line
                    self.display.cursor_col = 0
                elif char == '\n':
                    # Line feed - move to next line
                    self.display.cursor_col = 0
                    self.display.cursor_row += 1
                    if self.display.cursor_row >= self.display.lines:
                        # Scroll up if we've gone past the bottom
                        self.display.scroll_up(1)
                        self.display.cursor_row = self.display.lines - 1
                elif char == '\b':
                    # Backspace
                    if self.display.cursor_col > 0:
                        self.display.cursor_col -= 1
                elif char == '\t':
                    # Tab to next 8-character boundary
                    self.display.cursor_col = ((self.display.cursor_col // 8) + 1) * 8
                    if self.display.cursor_col >= self.display.columns:
                        self.display.cursor_col = 0
                        self.display.cursor_row += 1
                        if self.display.cursor_row >= self.display.lines:
                            self.display.scroll_up(1)
                            self.display.cursor_row = self.display.lines - 1
                elif ord(char) >= 32:  # Printable character
                    self.display.write_char(char)
                # Skip other control characters
                i += 1
    
    def _clear_line_from_cursor(self) -> None:
        """Clear from cursor to end of current line."""
        row = self.display.cursor_row
        col = self.display.cursor_col
        if row < self.display.lines:
            line = list(self.display.buffer[row])
            for j in range(col, len(line)):
                line[j] = ' '
            self.display.buffer[row] = ''.join(line)
    
    def _clear_from_cursor_to_end(self) -> None:
        """Clear from cursor to end of screen."""
        # Clear current line from cursor
        self._clear_line_from_cursor()
        
        # Clear all lines below current line
        for row in range(self.display.cursor_row + 1, self.display.lines):
            self.display.buffer[row] = ' ' * self.display.columns
            
    def _clear_from_beginning_to_cursor(self) -> None:
        """Clear from beginning of screen to cursor."""
        # Clear all lines above current line
        for row in range(0, self.display.cursor_row):
            self.display.buffer[row] = ' ' * self.display.columns
            
        # Clear current line from beginning to cursor
        row = self.display.cursor_row
        col = self.display.cursor_col
        if row < self.display.lines:
            line = list(self.display.buffer[row])
            for j in range(0, min(col + 1, len(line))):
                line[j] = ' '
            self.display.buffer[row] = ''.join(line)
                
    def get_display(self) -> str:
        """Get current display state as string.
        
        Returns:
            String representation of current display
        """
        return self.display.get_display()
        
    def save_display(self, filename: str) -> None:
        """Save current display to a file.
        
        Args:
            filename: Path to save the display content
        """
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(self.get_display())
            
    def get_line(self, line_num: int) -> str:
        """Get specific line from display.
        
        Args:
            line_num: Line number (0-based)
            
        Returns:
            Content of the specified line
        """
        return self.display.get_line(line_num)
        
    def find_text(self, pattern: str) -> Optional[Tuple[int, int]]:
        """Find text in the display.
        
        Args:
            pattern: Text to search for
            
        Returns:
            Tuple of (line, column) if found, None otherwise
        """
        return self.display.find_text(pattern)