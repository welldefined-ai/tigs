"""Assertion functions for E2E terminal testing.

This module provides assertion functions similar to Tig's test harness,
allowing comparison of terminal displays and verification of application behavior.
"""

import difflib
import re
from pathlib import Path
from typing import Optional, Union, List

import pytest


class DisplayMismatchError(AssertionError):
    """Exception raised when display content doesn't match expectations."""
    pass


def assert_display_matches(
    actual: str,
    expected: Union[str, Path],
    whitespace: str = 'ignore',
    message: Optional[str] = None
) -> None:
    """Assert that display content matches expected output.
    
    This is similar to Tig's assert_equals function.
    
    Args:
        actual: Actual display content as string
        expected: Expected content (string) or path to file containing expected content
        whitespace: How to handle whitespace differences:
                   'ignore' - ignore whitespace differences (default)
                   'strict' - whitespace must match exactly
        message: Optional message to include in assertion error
        
    Raises:
        DisplayMismatchError: If actual doesn't match expected
    """
    # Load expected content if it's a file path
    if isinstance(expected, Path):
        if not expected.exists():
            raise FileNotFoundError(f"Expected display file not found: {expected}")
        expected_content = expected.read_text(encoding='utf-8').rstrip('\n')
    else:
        expected_content = expected.rstrip('\n')
        
    # Normalize actual content
    actual_content = actual.rstrip('\n')
    
    # Compare based on whitespace handling
    if whitespace == 'ignore':
        # Compare ignoring whitespace differences
        actual_lines = [line.rstrip() for line in actual_content.split('\n')]
        expected_lines = [line.rstrip() for line in expected_content.split('\n')]
        
        if actual_lines != expected_lines:
            _raise_display_mismatch(actual_content, expected_content, message, whitespace)
    else:
        # Strict comparison
        if actual_content != expected_content:
            _raise_display_mismatch(actual_content, expected_content, message, whitespace)


def assert_display_contains(
    actual: str,
    pattern: Union[str, re.Pattern],
    message: Optional[str] = None
) -> None:
    """Assert that display content contains a pattern.
    
    Args:
        actual: Actual display content
        pattern: Text pattern or compiled regex to search for
        message: Optional message for assertion error
        
    Raises:
        AssertionError: If pattern is not found
    """
    if isinstance(pattern, str):
        found = pattern in actual
        pattern_str = repr(pattern)
    else:
        found = pattern.search(actual) is not None
        pattern_str = pattern.pattern
        
    if not found:
        error_msg = f"Pattern {pattern_str} not found in display"
        if message:
            error_msg = f"{message}: {error_msg}"
        raise AssertionError(error_msg)


def assert_display_not_contains(
    actual: str,
    pattern: Union[str, re.Pattern],
    message: Optional[str] = None
) -> None:
    """Assert that display content does not contain a pattern.
    
    Args:
        actual: Actual display content
        pattern: Text pattern or compiled regex to avoid
        message: Optional message for assertion error
        
    Raises:
        AssertionError: If pattern is found
    """
    if isinstance(pattern, str):
        found = pattern in actual
        pattern_str = repr(pattern)
    else:
        found = pattern.search(actual) is not None
        pattern_str = pattern.pattern
        
    if found:
        error_msg = f"Pattern {pattern_str} unexpectedly found in display"
        if message:
            error_msg = f"{message}: {error_msg}"
        raise AssertionError(error_msg)


def assert_line_matches(
    actual: str,
    line_num: int,
    expected: str,
    message: Optional[str] = None
) -> None:
    """Assert that a specific line matches expected content.
    
    Args:
        actual: Full display content
        line_num: Line number to check (0-based)
        expected: Expected line content
        message: Optional message for assertion error
        
    Raises:
        AssertionError: If line doesn't match
    """
    lines = actual.split('\n')
    
    if line_num >= len(lines):
        error_msg = f"Line {line_num} does not exist (only {len(lines)} lines)"
        if message:
            error_msg = f"{message}: {error_msg}"
        raise AssertionError(error_msg)
        
    actual_line = lines[line_num].rstrip()
    expected_line = expected.rstrip()
    
    if actual_line != expected_line:
        error_msg = (
            f"Line {line_num} mismatch:\n"
            f"  Expected: {repr(expected_line)}\n"
            f"  Actual:   {repr(actual_line)}"
        )
        if message:
            error_msg = f"{message}: {error_msg}"
        raise AssertionError(error_msg)


def assert_cursor_position(
    display_capture,
    expected_row: int,
    expected_col: int,
    message: Optional[str] = None
) -> None:
    """Assert cursor is at expected position.
    
    Args:
        display_capture: DisplayCapture instance
        expected_row: Expected cursor row (0-based)
        expected_col: Expected cursor column (0-based)
        message: Optional message for assertion error
        
    Raises:
        AssertionError: If cursor position doesn't match
    """
    actual_row = display_capture.display.cursor_row
    actual_col = display_capture.display.cursor_col
    
    if actual_row != expected_row or actual_col != expected_col:
        error_msg = (
            f"Cursor position mismatch:\n"
            f"  Expected: ({expected_row}, {expected_col})\n"
            f"  Actual:   ({actual_row}, {actual_col})"
        )
        if message:
            error_msg = f"{message}: {error_msg}"
        raise AssertionError(error_msg)


def _raise_display_mismatch(
    actual: str,
    expected: str,
    message: Optional[str],
    whitespace: str
) -> None:
    """Raise a DisplayMismatchError with detailed diff information.
    
    Args:
        actual: Actual display content
        expected: Expected display content
        message: Optional message
        whitespace: Whitespace handling mode
    """
    # Generate unified diff
    actual_lines = actual.split('\n')
    expected_lines = expected.split('\n')
    
    diff_lines = list(difflib.unified_diff(
        expected_lines,
        actual_lines,
        fromfile='expected',
        tofile='actual',
        lineterm=''
    ))
    
    error_msg = "Display content mismatch"
    if message:
        error_msg = f"{message}: {error_msg}"
        
    if diff_lines:
        diff_text = '\n'.join(diff_lines)
        error_msg += f"\n\nDiff (whitespace={whitespace}):\n{diff_text}"
    else:
        error_msg += "\nNo differences detected in diff (this shouldn't happen)"
        
    raise DisplayMismatchError(error_msg)


def save_display_on_failure(actual: str, test_name: str, fixtures_dir: Path) -> None:
    """Save actual display content when a test fails.
    
    This function can be called from pytest fixtures to save the actual
    display content when tests fail, making debugging easier.
    
    Args:
        actual: Actual display content
        test_name: Name of the failed test
        fixtures_dir: Directory to save failure artifacts
    """
    fixtures_dir.mkdir(parents=True, exist_ok=True)
    
    failure_file = fixtures_dir / f"{test_name}_failure.txt"
    failure_file.write_text(actual, encoding='utf-8')
    
    print(f"\\nSaved actual display to: {failure_file}")


# Convenience functions for common patterns

def assert_status_line_contains(actual: str, text: str) -> None:
    """Assert that the status line (last line) contains specific text.
    
    Args:
        actual: Full display content
        text: Text that should appear in status line
    """
    lines = actual.split('\n')
    if not lines:
        raise AssertionError("Display is empty, no status line found")
        
    status_line = lines[-1]
    if text not in status_line:
        raise AssertionError(f"Status line does not contain {repr(text)}\\nStatus line: {repr(status_line)}")


def assert_title_line_matches(actual: str, expected: str) -> None:
    """Assert that the first line (title) matches expected content.
    
    Args:
        actual: Full display content  
        expected: Expected title line content
    """
    assert_line_matches(actual, 0, expected, "Title line mismatch")


def assert_empty_display(actual: str) -> None:
    """Assert that the display is empty or contains only whitespace.
    
    Args:
        actual: Display content to check
    """
    if actual.strip():
        raise AssertionError(f"Expected empty display but got:\\n{repr(actual)}")


def assert_display_height(actual: str, expected_lines: int) -> None:
    """Assert that the display has the expected number of lines.
    
    Args:
        actual: Display content
        expected_lines: Expected number of lines
    """
    actual_lines = len(actual.split('\n'))
    if actual_lines != expected_lines:
        raise AssertionError(f"Expected {expected_lines} lines but got {actual_lines}")


def load_expected_display(fixture_path: Path) -> str:
    """Load expected display content from a fixture file.
    
    Args:
        fixture_path: Path to fixture file
        
    Returns:
        Expected display content
        
    Raises:
        FileNotFoundError: If fixture file doesn't exist
    """
    if not fixture_path.exists():
        raise FileNotFoundError(f"Fixture file not found: {fixture_path}")
        
    return fixture_path.read_text(encoding='utf-8').rstrip('\n')