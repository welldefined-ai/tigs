"""Utility functions for E2E terminal testing."""

import time
from typing import List, Union, Optional
from pathlib import Path


def send_keys(terminal_app, keys: Union[str, List[str]], delay: float = 0.05) -> None:
    """Send keys to terminal app with optional delay between keystrokes.
    
    Args:
        terminal_app: TerminalApp instance
        keys: Keys to send (string or list)
        delay: Delay between keystrokes in seconds
    """
    if isinstance(keys, str):
        keys = [keys]
        
    for key in keys:
        terminal_app.send_keys(key)
        if delay > 0:
            time.sleep(delay)


def wait_for_output(
    terminal_app,
    pattern: Optional[str] = None,
    timeout: float = 5.0,
    interval: float = 0.1
) -> str:
    """Wait for output to appear in terminal.
    
    Args:
        terminal_app: TerminalApp instance
        pattern: Optional regex pattern to wait for
        timeout: Maximum time to wait in seconds
        interval: Check interval in seconds
        
    Returns:
        Current display content
        
    Raises:
        TimeoutError: If timeout expires
    """
    return terminal_app.wait_for_output(pattern, timeout)


def create_test_repo(repo_path: Path, commits: Optional[List[str]] = None) -> None:
    """Create a test Git repository with optional commits.
    
    Args:
        repo_path: Path where to create the repository
        commits: List of commit messages to create
    """
    import subprocess
    import os
    
    repo_path.mkdir(parents=True, exist_ok=True)
    
    # Initialize git repo
    subprocess.run(['git', 'init'], cwd=repo_path, check=True)
    subprocess.run(['git', 'config', 'user.email', 'test@example.com'], 
                   cwd=repo_path, check=True)
    subprocess.run(['git', 'config', 'user.name', 'Test User'], 
                   cwd=repo_path, check=True)
    
    if commits:
        for i, commit_msg in enumerate(commits):
            # Create a test file for each commit
            test_file = repo_path / f'file_{i}.txt'
            test_file.write_text(f'Content for commit: {commit_msg}\\n')
            
            subprocess.run(['git', 'add', test_file.name], cwd=repo_path, check=True)
            subprocess.run(['git', 'commit', '-m', commit_msg], cwd=repo_path, check=True)


def cleanup_test_repo(repo_path: Path) -> None:
    """Clean up a test repository.
    
    Args:
        repo_path: Path to repository to remove
    """
    import shutil
    
    if repo_path.exists():
        shutil.rmtree(repo_path)


def normalize_display_content(content: str) -> str:
    """Normalize display content for comparison.
    
    This function strips trailing whitespace from each line and removes
    trailing empty lines, similar to how Tig processes display content.
    
    Args:
        content: Raw display content
        
    Returns:
        Normalized content
    """
    lines = [line.rstrip() for line in content.split('\\n')]
    
    # Remove trailing empty lines
    while lines and not lines[-1]:
        lines.pop()
        
    return '\\n'.join(lines)


def extract_status_line(content: str) -> str:
    """Extract the status line (last non-empty line) from display content.
    
    Args:
        content: Display content
        
    Returns:
        Status line content, or empty string if none found
    """
    lines = content.split('\\n')
    
    # Find last non-empty line
    for line in reversed(lines):
        if line.strip():
            return line.strip()
            
    return ""


def get_display_lines(content: str) -> List[str]:
    """Get display content as a list of lines.
    
    Args:
        content: Display content
        
    Returns:
        List of lines (right-stripped)
    """
    return [line.rstrip() for line in content.split('\\n')]


def wait_for_stable_display(
    terminal_app,
    stable_duration: float = 0.5,
    max_wait: float = 10.0
) -> str:
    """Wait for the display to become stable (no changes for a period).
    
    This is useful when waiting for the application to finish loading
    or processing.
    
    Args:
        terminal_app: TerminalApp instance
        stable_duration: How long display must be stable (seconds)
        max_wait: Maximum total wait time (seconds)
        
    Returns:
        Final stable display content
        
    Raises:
        TimeoutError: If display doesn't stabilize within max_wait
    """
    start_time = time.time()
    last_display = ""
    stable_since = None
    
    while time.time() - start_time < max_wait:
        current_display = terminal_app.capture_display()
        
        if current_display == last_display:
            # Display hasn't changed
            if stable_since is None:
                stable_since = time.time()
            elif time.time() - stable_since >= stable_duration:
                # Display has been stable long enough
                return current_display
        else:
            # Display changed - reset stability timer
            last_display = current_display
            stable_since = None
            
        time.sleep(0.1)
        
    raise TimeoutError(f"Display did not stabilize within {max_wait} seconds")


def find_line_containing(content: str, pattern: str) -> Optional[int]:
    """Find the line number containing a specific pattern.
    
    Args:
        content: Display content
        pattern: Text pattern to search for
        
    Returns:
        Line number (0-based) if found, None otherwise
    """
    lines = content.split('\\n')
    for i, line in enumerate(lines):
        if pattern in line:
            return i
    return None


def extract_highlighted_line(content: str, marker: str = "►") -> Optional[str]:
    """Extract the highlighted/selected line from display content.
    
    This looks for a line containing a marker character (like cursor or selection).
    
    Args:
        content: Display content
        marker: Marker character to look for
        
    Returns:
        The highlighted line content, or None if not found
    """
    lines = content.split('\\n')
    for line in lines:
        if marker in line:
            return line.strip()
    return None


def simulate_user_session(terminal_app, actions: List[dict]) -> List[str]:
    """Simulate a user session with a sequence of actions.
    
    Args:
        terminal_app: TerminalApp instance
        actions: List of action dictionaries with keys:
                - 'action': 'keys', 'wait', 'capture', 'command'
                - 'value': action-specific value
                - 'delay': optional delay after action
                
    Returns:
        List of display captures taken during the session
        
    Example:
        actions = [
            {'action': 'keys', 'value': ['j', 'j']},
            {'action': 'wait', 'value': 0.5},
            {'action': 'capture'},
            {'action': 'keys', 'value': '<Enter>'},
            {'action': 'capture'}
        ]
    """
    captures = []
    
    for action in actions:
        action_type = action.get('action')
        value = action.get('value')
        delay = action.get('delay', 0.0)
        
        if action_type == 'keys':
            terminal_app.send_keys(value)
        elif action_type == 'wait':
            time.sleep(value)
        elif action_type == 'capture':
            captures.append(terminal_app.capture_display())
        elif action_type == 'command':
            terminal_app.send_command(value)
        else:
            raise ValueError(f"Unknown action type: {action_type}")
            
        if delay > 0:
            time.sleep(delay)
            
    return captures