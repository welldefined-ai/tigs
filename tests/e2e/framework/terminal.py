"""Terminal application control for E2E testing.

This module provides the core TerminalApp class that manages the lifecycle
of a terminal application under test, similar to how Tig's test harness works.
"""

import fcntl
import os
import pty
import select
import signal
import struct
import subprocess
import sys
import termios
import time
import tty
from pathlib import Path
from typing import Dict, List, Optional, Union, Any

from .display import DisplayCapture


class TerminalApp:
    """Manages a terminal application for E2E testing.
    
    This class launches the application in a pseudo-terminal (PTY) and provides
    methods to interact with it as if a user were typing commands and keys.
    
    Based on Tig's testing approach but adapted for Python.
    """
    
    def __init__(
        self,
        command: Union[str, List[str]],
        args: Optional[List[str]] = None,
        cwd: Optional[Path] = None,
        env: Optional[Dict[str, str]] = None,
        timeout: float = 10.0,
        lines: int = 30,
        columns: int = 80
    ):
        """Initialize the terminal application.
        
        Args:
            command: Command to run (e.g., "tigs" or ["python", "-m", "tigs"])
            args: Additional arguments to pass to the command
            cwd: Working directory for the process
            env: Environment variables (extends current env if provided)
            timeout: Default timeout for operations in seconds
            lines: Terminal height in lines
            columns: Terminal width in columns
        """
        if isinstance(command, str):
            self.command = [command]
        else:
            self.command = command[:]
        
        if args:
            self.command.extend(args)
            
        self.cwd = cwd
        self.timeout = timeout
        self.lines = lines
        self.columns = columns
        
        # Set up environment
        self.env = os.environ.copy()
        if env:
            self.env.update(env)
            
        # Force consistent terminal environment (like Tig tests)
        self.env.update({
            'TERM': 'xterm-256color',
            'LINES': str(lines),
            'COLUMNS': str(columns),
            'LANG': 'en_US.UTF-8',
            'LC_ALL': 'en_US.UTF-8',
            'TZ': 'UTC',
            'PAGER': 'cat',
            'HOME': str(cwd) if cwd else os.environ.get('HOME', '/tmp'),
        })
        
        # Remove potentially problematic env vars
        for var in ['CDPATH', 'VISUAL', 'INPUTRC', 'GIT_EDITOR', 'GIT_PAGER']:
            self.env.pop(var, None)
        
        # Process state
        self.process: Optional[subprocess.Popen] = None
        self.master_fd: Optional[int] = None
        self.slave_fd: Optional[int] = None
        self.display_capture = DisplayCapture(lines, columns)
        self._output_buffer = b""
        self._running = False
        
    def start(self) -> None:
        """Start the terminal application."""
        if self._running:
            raise RuntimeError("Application is already running")
            
        # Create PTY
        self.master_fd, self.slave_fd = pty.openpty()
        
        # Set terminal attributes (like Tig tests expect)
        attrs = termios.tcgetattr(self.slave_fd)
        lflag = attrs[3]  # LFLAG is at index 3 in the termios tuple
        lflag &= ~termios.TOSTOP  # clear TOSTOP like `stty -tostop`
        attrs = list(attrs)
        attrs[3] = lflag
        termios.tcsetattr(self.slave_fd, termios.TCSANOW, attrs)
        
        # Set window size via ioctl (environment variables are not sufficient)
        fcntl.ioctl(self.slave_fd, termios.TIOCSWINSZ, 
                   struct.pack('HHHH', self.lines, self.columns, 0, 0))
        
        # Start the process
        try:
            self.process = subprocess.Popen(
                self.command,
                stdin=self.slave_fd,
                stdout=self.slave_fd,
                stderr=self.slave_fd,
                cwd=self.cwd,
                env=self.env,
                start_new_session=True  # Critical: gives it a new session/ctty
            )
        except Exception as e:
            self._cleanup()
            raise RuntimeError(f"Failed to start process: {e}")
            
        # Close slave fd in parent (process has its own copy)
        os.close(self.slave_fd)
        self.slave_fd = None
        
        self._running = True
        
        # Give the application time to initialize
        time.sleep(0.1)
        self._drain()
        
    def stop(self) -> None:
        """Stop the terminal application."""
        if not self._running:
            return
            
        self._running = False
        
        if self.process:
            # Try graceful shutdown first - send 'q' for applications that support it
            try:
                if self.master_fd is not None:
                    os.write(self.master_fd, b'q')
                    self._drain(max_wait=1.0)  # Capture final frame
            except (OSError, ValueError):
                pass  # FD might be closed already
                
            # Then try SIGTERM
            try:
                self.process.terminate()
                self.process.wait(timeout=2.0)
            except subprocess.TimeoutExpired:
                # Force kill if needed
                self.process.kill()
                self.process.wait()
            
        self._cleanup()
        
    def _cleanup(self) -> None:
        """Clean up file descriptors."""
        if self.master_fd is not None:
            os.close(self.master_fd)
            self.master_fd = None
            
        if self.slave_fd is not None:
            os.close(self.slave_fd)
            self.slave_fd = None
            
        self.process = None
        
    def send_keys(self, keys: Union[str, List[str]]) -> None:
        """Send keystrokes to the application.
        
        Args:
            keys: String or list of keys to send. Special keys can be:
                  '<Enter>', '<Escape>', '<Tab>', '<Up>', '<Down>', '<Left>', '<Right>',
                  '<Home>', '<End>', '<PageUp>', '<PageDown>', etc.
        """
        if not self._running or self.master_fd is None:
            raise RuntimeError("Application is not running")
            
        if isinstance(keys, str):
            keys = [keys]
            
        for key in keys:
            key_bytes = self._convert_key_to_bytes(key)
            os.write(self.master_fd, key_bytes)
            time.sleep(0.02)  # Small debounce after key send
            
        # Drain all output once after sending all keys
        self._drain()
            
    def _convert_key_to_bytes(self, key: str) -> bytes:
        """Convert key description to bytes."""
        # Special key mappings (ANSI escape sequences)
        special_keys = {
            '<Enter>': b'\r',
            '<Return>': b'\r',
            '<Escape>': b'\x1b',
            '<Tab>': b'\t',
            '<Backspace>': b'\x7f',
            '<Delete>': b'\x1b[3~',
            '<Up>': b'\x1b[A',
            '<Down>': b'\x1b[B', 
            '<Right>': b'\x1b[C',
            '<Left>': b'\x1b[D',
            '<Home>': b'\x1b[H',
            '<End>': b'\x1b[F',
            '<PageUp>': b'\x1b[5~',
            '<PageDown>': b'\x1b[6~',
            '<F1>': b'\x1bOP',
            '<F2>': b'\x1bOQ',
            '<F3>': b'\x1bOR',
            '<F4>': b'\x1bOS',
            '<Space>': b' ',
        }
        
        # Control characters  
        if key.startswith('<C-') and key.endswith('>'):
            char = key[3:-1].lower()
            if len(char) == 1 and 'a' <= char <= 'z':
                return bytes([ord(char) - ord('a') + 1])
                
        # Special keys
        if key in special_keys:
            return special_keys[key]
            
        # Regular character(s)
        if key.startswith('<') and key.endswith('>'):
            # Unknown special key - just use the content
            return key[1:-1].encode('utf-8')
        else:
            return key.encode('utf-8')
            
    def _drain(self, max_wait: Optional[float] = None, idle_gap: Optional[float] = None) -> None:
        """Drain all available output with idle-aware loop.
        
        Reads until no data for idle_gap seconds (max max_wait total).
        This prevents capturing mid-frame renders.
        
        Args:
            max_wait: Maximum time to wait (default: 0.4s, or E2E_MAX_WAIT env var)
            idle_gap: Idle time before giving up (default: 0.06s, or E2E_IDLE_GAP env var)
        """
        if max_wait is None:
            max_wait = float(os.environ.get('E2E_MAX_WAIT', '0.4'))
        if idle_gap is None:
            idle_gap = float(os.environ.get('E2E_IDLE_GAP', '0.06'))
        if not self._running or self.master_fd is None:
            return
            
        deadline = time.time() + max_wait
        while True:
            got_data = False
            try:
                # Read all immediately available data
                while True:
                    ready, _, _ = select.select([self.master_fd], [], [], 0.02)
                    if not ready:
                        break
                    data = os.read(self.master_fd, 8192)
                    if not data:
                        break
                    self._output_buffer += data
                    self.display_capture.process_output(data)
                    got_data = True
            except (OSError, ValueError):
                break
                
            # If we got no data, check if we should wait more or we're done
            if not got_data:
                if time.time() + idle_gap > deadline:
                    break
                time.sleep(idle_gap)
            # If we did get data, continue immediately (don't sleep)
            
    def wait_for_output(self, pattern: Optional[str] = None, timeout: Optional[float] = None) -> str:
        """Wait for output to appear, optionally matching a pattern.
        
        Args:
            pattern: Optional regex pattern to wait for
            timeout: Timeout in seconds (uses default if None)
            
        Returns:
            The captured output as a string
            
        Raises:
            TimeoutError: If timeout expires
        """
        import re
        
        if timeout is None:
            timeout = self.timeout
            
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            self._drain(max_wait=0.1)  # Short drain for polling
            
            if pattern is None:
                # Just wait for any output
                if self._output_buffer:
                    break
            else:
                # Wait for pattern match
                current_output = self._output_buffer.decode('utf-8', errors='ignore')
                if re.search(pattern, current_output):
                    break
                    
            time.sleep(0.1)
        else:
            raise TimeoutError(f"Timeout waiting for output" + (f" matching '{pattern}'" if pattern else ""))
            
        return self._output_buffer.decode('utf-8', errors='ignore')
        
    def capture_display(self) -> str:
        """Capture the current terminal display.
        
        Returns:
            The terminal display as a string (similar to Tig's :save-display)
        """
        self._drain()  # Make sure we have latest output
        return self.display_capture.get_display()
        
    def send_command(self, command: str) -> None:
        """Send a command (like Tig's :command syntax).
        
        Args:
            command: Command to send (without the ':' prefix)
        """
        if command.startswith(':'):
            command = command[1:]
        self.send_keys([f':{command}', '<Enter>'])
        
    def is_running(self) -> bool:
        """Check if the application is still running."""
        if not self._running or self.process is None:
            return False
        return self.process.poll() is None
        
    def get_exit_code(self) -> Optional[int]:
        """Get the exit code of the process (None if still running)."""
        if self.process is None:
            return None
        return self.process.poll()
        
    def __enter__(self):
        """Context manager entry."""
        self.start()
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.stop()