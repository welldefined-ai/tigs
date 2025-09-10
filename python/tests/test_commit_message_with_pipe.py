"""Test that commit messages containing | are not colored as file stats."""

import pytest
from unittest.mock import Mock, patch

from src.tui.commit_details_view import CommitDetailsView


class TestCommitMessageWithPipe:
    """Test that commit messages with | character are not mistaken for file stats."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.mock_store = Mock()
        self.mock_store.repo_path = '/test/repo'
        self.view = CommitDetailsView(self.mock_store)
    
    def test_commit_message_with_pipe_not_colored_as_file(self):
        """Test that commit message lines with | are not colored blue."""
        git_output = """commit abc123
Author:     Test <test@test.com>
AuthorDate: Mon Sep 10 14:30:00 2025 +0800

    feat(tui): add three-column layout
    
    - Three-column layout: Commits | Details | Chat
    - Support for navigation between panes
    - Added keyboard shortcuts (Tab | Shift-Tab)
    
 file1.txt | 5 +++++
 file2.py | 10 +++---
 2 files changed, 8 insertions(+), 3 deletions(-)"""
        
        with patch('subprocess.run') as mock_run:
            mock_run.return_value.returncode = 0
            mock_run.return_value.stdout = git_output
            
            self.view.load_commit_details('abc123')
            lines = self.view.get_display_lines(height=30, width=80, colors_enabled=True)
            
            # Check each line
            for i, line in enumerate(lines):
                if isinstance(line, list):
                    text = "".join(t for t, _ in line)
                    # File stats lines should be multi-colored
                    if "file1.txt" in text or "file2.py" in text:
                        assert line[0][1] == 7, f"File stats should have blue filename"
                    else:
                        # Commit message lines with | should NOT be multi-colored
                        assert False, f"Line {i} should not be multi-colored: {text}"
                elif isinstance(line, tuple):
                    text, color = line
                    # Commit message lines should be plain tuples with default color
                    if "Three-column layout" in text or "keyboard shortcuts" in text:
                        assert color == 0, f"Commit message should have default color, got {color}: {text}"
                        print(f"✓ Commit message correctly not blue: {text[:50]}...")
    
    def test_various_pipe_contexts(self):
        """Test various contexts where | appears."""
        git_output = """commit abc123
Author:     Test <test@test.com>
AuthorDate: Mon Sep 10 14:30:00 2025 +0800

    Add support for pipes
    
    This commit adds:
    - Unix pipes: ls | grep
    - OR operators: if (a | b)
    - Table syntax: Col1 | Col2 | Col3
    - Bitwise OR: flags |= OPTION
    
 src/parser.c | 25 +++++++++++++++++++------
 1 file changed, 19 insertions(+), 6 deletions(-)"""
        
        with patch('subprocess.run') as mock_run:
            mock_run.return_value.returncode = 0
            mock_run.return_value.stdout = git_output
            
            self.view.load_commit_details('abc123')
            lines = self.view.get_display_lines(height=30, width=80, colors_enabled=True)
            
            message_lines_with_pipe = []
            file_stats_lines = []
            
            for line in lines:
                if isinstance(line, list):
                    text = "".join(t for t, _ in line)
                    if "src/parser.c" in text:
                        file_stats_lines.append(text)
                elif isinstance(line, tuple):
                    text, color = line
                    if "|" in text and not text.strip().startswith("Author"):
                        message_lines_with_pipe.append((text, color))
            
            # All message lines with | should be default color
            for text, color in message_lines_with_pipe:
                assert color == 0, f"Message line should not be colored: {text}"
            
            # File stats should be found and multi-colored
            assert len(file_stats_lines) == 1, f"Should find 1 file stats line"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])