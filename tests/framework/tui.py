"""Minimal TUI testing utilities using pexpect + pyte.

This module provides a thin wrapper around pexpect and pyte for testing
terminal user interface applications like tigs.
"""

import os
import time
from pathlib import Path
from typing import Dict, List, Optional, Union

import pexpect
import pyte


class TUI:
    """Thin wrapper around pexpect + pyte for TUI testing."""
    
    def __init__(
        self, 
        command: Union[str, List[str]], 
        cwd: Optional[Path] = None,
        env: Optional[Dict[str, str]] = None,
        dimensions: tuple = (30, 120),
        timeout: float = 10.0
    ):
        """Initialize TUI session.
        
        Args:
            command: Command to run (string or list)
            cwd: Working directory
            env: Environment variables (extends current env)
            dimensions: Terminal size (rows, cols)
            timeout: Default timeout for operations
        """
        self.timeout = timeout
        self.rows, self.cols = dimensions
        
        # Set up environment
        full_env = os.environ.copy()
        full_env.update({
            'LC_ALL': 'C',
            'LANG': 'C', 
            'TERM': 'xterm-256color',
            'NCURSES_NO_UTF8_ACS': '1',  # Force ASCII line drawing
        })
        if env:
            full_env.update(env)
        
        # Parse command
        if isinstance(command, str):
            cmd_parts = command.split()
        else:
            cmd_parts = list(command)
        
        # Launch with pexpect
        self.child = pexpect.spawn(
            cmd_parts[0],
            cmd_parts[1:] if len(cmd_parts) > 1 else [],
            cwd=str(cwd) if cwd else None,
            env=full_env,
            dimensions=dimensions,
            timeout=timeout,
            encoding=None  # Handle bytes directly
        )
        
        # Set up pyte for clean terminal display
        self.screen = pyte.Screen(self.cols, self.rows)
        self.stream = pyte.ByteStream()
        self.stream.attach(self.screen)
        
        # Track terminal mode for proper arrow key handling
        self._decckm = None  # None/True/False
        
        # Initial drain to capture startup output
        self._drain()
    
    def _drain(self, max_wait: float = 0.4, idle_gap: float = 0.06) -> None:
        """Drain output until idle, feeding to pyte for display processing."""
        deadline = time.time() + max_wait
        idle_start = None
        
        while time.time() < deadline:
            got_data = False
            try:
                data = self.child.read_nonblocking(8192, timeout=0.02)
                if data:
                    # Track DECCKM mode changes
                    if b"\x1b[?1h" in data:
                        self._decckm = True
                    if b"\x1b[?1l" in data:
                        self._decckm = False
                    
                    # Feed to pyte for processing
                    self.stream.feed(data)
                    got_data = True
                    idle_start = None  # Reset idle timer
                    
            except pexpect.TIMEOUT:
                pass
            except pexpect.EOF:
                break
                
            if not got_data:
                if idle_start is None:
                    idle_start = time.time()
                elif time.time() - idle_start >= idle_gap:
                    break  # Been idle long enough
                    
            time.sleep(0.01)  # Small sleep to prevent busy loop
    
    def capture(self) -> List[str]:
        """Capture current display as clean text lines."""
        self._drain()
        
        # Get clean lines from pyte screen
        lines = []
        for row in range(self.rows):
            line = "".join(
                char.data for char in self.screen.buffer[row].values()
            ).rstrip()
            lines.append(line)
        
        # Remove trailing empty lines
        while lines and not lines[-1]:
            lines.pop()
            
        return lines
    
    def send_arrow(self, direction: str) -> None:
        """Send arrow key with proper DECCKM handling."""
        arrow_keys = {
            "up": (b"\x1bOA", b"\x1b[A"),      # SS3, CSI
            "down": (b"\x1bOB", b"\x1b[B"), 
            "right": (b"\x1bOC", b"\x1b[C"),
            "left": (b"\x1bOD", b"\x1b[D"),
        }
        
        if direction not in arrow_keys:
            raise ValueError(f"Invalid arrow direction: {direction}")
            
        ss3_seq, csi_seq = arrow_keys[direction]
        
        if self._decckm is True:
            # Application mode: send SS3 sequence
            self.child.write(ss3_seq)
        elif self._decckm is False:
            # Normal mode: send CSI sequence  
            self.child.write(csi_seq)
        else:
            # Unknown mode: send both (SS3 first, then CSI)
            self.child.write(ss3_seq)
            self._drain(max_wait=0.06)
            self.child.write(csi_seq)
        
        self._drain()
    
    def send(self, text: str) -> None:
        """Send text or special keys."""
        # Handle special keys
        if text.startswith('<') and text.endswith('>'):
            key = text[1:-1].lower()
            if key in ['up', 'down', 'left', 'right']:
                self.send_arrow(key)
                return
            elif key == 'enter':
                self.child.write(b'\r')
            elif key == 'escape':
                self.child.write(b'\x1b')
            elif key == 'tab':
                self.child.write(b'\t')
            elif key == 'space':
                self.child.write(b' ')
            else:
                # Unknown special key, send as text
                self.child.write(text.encode('utf-8'))
        else:
            # Regular text
            self.child.write(text.encode('utf-8'))
        
        self._drain()
    
    def wait_for(self, pattern: str, timeout: Optional[float] = None) -> None:
        """Wait for pattern to appear in output."""
        if timeout is None:
            timeout = self.timeout
            
        deadline = time.time() + timeout
        
        while time.time() < deadline:
            lines = self.capture()
            display_text = "\n".join(lines)
            
            if pattern in display_text:
                return
        
        # Timeout - show current display
        lines = self.capture()
        display = "\n".join(f"{i:02d}: {line}" for i, line in enumerate(lines[:20]))
        raise AssertionError(f"Timeout waiting for '{pattern}'.\nCurrent display:\n{display}")
    
    def quit(self) -> None:
        """Quit the application gracefully."""
        try:
            self.send('q')
            self.child.expect(pexpect.EOF, timeout=2.0)
        except (pexpect.TIMEOUT, pexpect.EOF):
            pass
        finally:
            if self.child.isalive():
                self.child.terminate()
                if self.child.isalive():
                    self.child.kill()
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.quit()


def find_cursor_row(lines: List[str]) -> int:
    """Find the row containing the cursor (>) in the first pane."""
    for i, line in enumerate(lines):
        pane_content = get_first_pane(line)
        if '>' in pane_content:
            return i
    raise AssertionError(f"Cursor '>' not found in first pane.\nDisplay:\n" + 
                        "\n".join(f"{i:02d}: {line}" for i, line in enumerate(lines[:15])))


def get_first_pane(line: str, width: int = 50) -> str:
    """Extract content from the first pane by finding vertical separators."""
    # Find pane separators (both Unicode │ and ASCII |)
    bars = [i for i, ch in enumerate(line) if ch in ("│", "|")]
    
    if len(bars) >= 2:
        # Return content between first two bars
        start = bars[0] + 1
        end = min(start + width, bars[1])
        return line[start:end].strip()
    
    # Fallback: return beginning of line
    return line[:width].strip()


def get_first_commit(lines: List[str]) -> Optional[str]:
    """Get the first visible commit in the viewport."""
    import re
    for line in lines[1:]:  # Skip header line
        pane_content = get_first_pane(line)
        # Look for commit patterns - handles both short SHA and Change X format
        match = re.search(r'Change (\d+)', pane_content)
        if match:
            return match.group(1)
        # Also try to match SHA patterns as fallback
        sha_match = re.search(r'([a-f0-9]{7,40})', pane_content)
        if sha_match and len(pane_content.strip()) > 10:  # Likely has commit info
            # Extract commit number from the content after SHA
            change_match = re.search(r'Change (\d+)', pane_content)
            if change_match:
                return change_match.group(1)
    return None


def get_last_commit(lines: List[str]) -> Optional[str]:
    """Get the last visible commit in the viewport."""
    import re
    for line in reversed(lines[1:]):  # Skip header line, search backwards
        pane_content = get_first_pane(line)
        match = re.search(r'Change (\d+)', pane_content)
        if match:
            return match.group(1)
    return None


def get_commit_at_cursor(lines: List[str]) -> Optional[str]:
    """Get the commit number at the current cursor position, handling multi-line commits."""
    import re
    try:
        cursor_row = find_cursor_row(lines)
        
        # Check the cursor line first
        cursor_pane_content = get_first_pane(lines[cursor_row])
        match = re.search(r'Change (\d+)', cursor_pane_content)
        if match:
            return match.group(1)
        
        # If not found on cursor line, search backwards from cursor to find the commit header
        for i in range(cursor_row, max(0, cursor_row - 5), -1):  # Look back up to 5 lines
            if i < len(lines):
                pane_content = get_first_pane(lines[i])
                # Look for a line that starts with a SHA (commit header)
                if re.search(r'^\s*[>*\s]*[a-f0-9]{7,40}\s+Change (\d+)', pane_content):
                    match = re.search(r'Change (\d+)', pane_content)
                    if match:
                        return match.group(1)
        
        return None
    except (AssertionError, IndexError):
        return None


def get_all_visible_commits(lines: List[str]) -> List[str]:
    """Get all commit numbers visible in the viewport."""
    import re
    commits = []
    for line in lines[1:]:  # Skip header line
        pane_content = get_first_pane(line)
        match = re.search(r'Change (\d+)', pane_content)
        if match and match.group(1) not in commits:  # Avoid duplicates
            commits.append(match.group(1))
    return commits


def get_visible_commit_range(lines: List[str]) -> tuple:
    """Return tuple of (first_commit_num, last_commit_num) or (None, None)."""
    first = get_first_commit(lines)
    last = get_last_commit(lines)
    
    try:
        return (int(first) if first else None, int(last) if last else None)
    except (ValueError, TypeError):
        return (None, None)


def save_screenshot(tui: TUI, test_name: str) -> str:
    """Save display screenshot for debugging."""
    lines = tui.capture()
    
    # Save to file
    try:
        with open(f'{test_name}_screenshot.txt', 'w') as f:
            f.write("=== TUI SCREENSHOT ===\n")
            f.write("(Captured via pyte terminal emulator)\n\n")
            for i, line in enumerate(lines):
                f.write(f"{i:02d}: {line}\n")
    except Exception:
        pass  # Don't fail test due to file write issues
    
    # Return formatted display for error messages
    return "\n".join(f"{i:02d}: {line}" for i, line in enumerate(lines[:20]))