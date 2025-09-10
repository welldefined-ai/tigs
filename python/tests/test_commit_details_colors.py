"""Test commit details view coloring."""

import pytest
from unittest.mock import Mock, patch
import subprocess

from src.tui.commit_details_view import CommitDetailsView


class TestCommitDetailsColors:
    """Test that commit details are colored correctly according to tig's scheme."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.mock_store = Mock()
        self.mock_store.repo_path = '/test/repo'
        self.view = CommitDetailsView(self.mock_store)
    
    def test_commit_sha_coloring(self):
        """Test that commit SHA is colored green."""
        # Mock git show output with actual format
        git_output = """commit abc123def456789
Author:     John Doe <john@example.com>
AuthorDate: Mon Sep 10 14:30:00 2025 +0800
Commit:     John Doe <john@example.com>
CommitDate: Mon Sep 10 14:30:00 2025 +0800

    Test commit message
    
 file.txt | 2 ++
 1 file changed, 2 insertions(+)"""
        
        with patch('subprocess.run') as mock_run:
            mock_run.return_value.returncode = 0
            mock_run.return_value.stdout = git_output
            
            self.view.load_commit_details('abc123def456789')
            lines = self.view.get_display_lines(height=20, width=80, colors_enabled=True)
            
            # First line should be commit SHA with green color (pair 3)
            assert len(lines) > 0
            assert isinstance(lines[0], tuple)
            text, color = lines[0]
            assert text.startswith("commit ")
            assert "abc123def456789" in text
            assert color == 3, f"Commit SHA should be green (3), got {color}"
    
    def test_author_and_email_coloring(self):
        """Test that both author name and email are colored cyan."""
        git_output = """commit abc123def456789
Author:     John Doe <john@example.com>
AuthorDate: Mon Sep 10 14:30:00 2025 +0800
Commit:     John Doe <john@example.com>
CommitDate: Mon Sep 10 14:30:00 2025 +0800

    Test commit"""
        
        with patch('subprocess.run') as mock_run:
            mock_run.return_value.returncode = 0
            mock_run.return_value.stdout = git_output
            
            self.view.load_commit_details('abc123def456789')
            lines = self.view.get_display_lines(height=20, width=80, colors_enabled=True)
            
            # Find author line
            author_line = None
            for line in lines:
                if isinstance(line, tuple):
                    text, color = line
                    if "Author:" in text:
                        author_line = (text, color)
                        break
            
            assert author_line is not None, "Author line not found"
            text, color = author_line
            assert "John Doe" in text
            assert "<john@example.com>" in text
            assert color == 2, f"Author line should be cyan (2), got {color}"
    
    def test_full_datetime_coloring(self):
        """Test that the entire date line including time is colored yellow."""
        git_output = """commit abc123def456789
Author:     John Doe <john@example.com>
AuthorDate: Mon Sep 10 14:30:00 2025 +0800
Commit:     John Doe <john@example.com>
CommitDate: Mon Sep 10 14:30:00 2025 +0800

    Test commit"""
        
        with patch('subprocess.run') as mock_run:
            mock_run.return_value.returncode = 0
            mock_run.return_value.stdout = git_output
            
            self.view.load_commit_details('abc123def456789')
            lines = self.view.get_display_lines(height=20, width=80, colors_enabled=True)
            
            # Find date line (converted from AuthorDate to Date)
            date_line = None
            for line in lines:
                if isinstance(line, tuple):
                    text, color = line
                    if text.startswith("Date:"):
                        date_line = (text, color)
                        break
            
            assert date_line is not None, "Date line not found"
            text, color = date_line
            assert "14:30:00" in text, f"Time should be included in date line: {text}"
            assert "2025" in text, f"Year should be included in date line: {text}"
            assert color == 4, f"Date line should be yellow (4), got {color}"
    
    def test_wrapped_lines_maintain_color(self):
        """Test that wrapped continuation lines maintain the same color."""
        git_output = """commit abc123def456789abcdef0123456789abcdef0123456789
Author:     John Doe with a very long name that will wrap <john.doe.with.very.long.email@example.com>
AuthorDate: Mon Sep 10 14:30:00 2025 +0800

    Test commit with a very long message that will definitely wrap when displayed in narrow width
    
 very_long_filename_that_will_wrap.txt | 10 ++++++++++
 1 file changed, 10 insertions(+)"""
        
        with patch('subprocess.run') as mock_run:
            mock_run.return_value.returncode = 0
            mock_run.return_value.stdout = git_output
            
            self.view.load_commit_details('abc123def456789')
            # Test with narrow width to force wrapping
            lines = self.view.get_display_lines(height=30, width=40, colors_enabled=True)
            
            # Check that wrapped lines maintain colors
            commit_lines = []
            author_lines = []
            
            for i, line in enumerate(lines):
                if isinstance(line, tuple):
                    text, color = line
                    # Only check lines that start with "commit " or are continuations
                    if text.startswith("commit ") or (i > 0 and "abc123" in text):
                        commit_lines.append((text, color))
                    elif "Author" in text or ("john" in text.lower() and color == 2) or "example.com" in text:
                        author_lines.append((text, color))
            
            # All commit line parts should be green
            for text, color in commit_lines:
                assert color == 3, f"Commit line part '{text}' should be green (3), got {color}"
            
            # All author line parts should be cyan
            for text, color in author_lines:
                assert color == 2, f"Author line part '{text}' should be cyan (2), got {color}"
    
    def test_file_changes_coloring(self):
        """Test that file changes with additions and deletions are colored."""
        git_output = """commit abc123def456789
Author:     John Doe <john@example.com>
AuthorDate: Mon Sep 10 14:30:00 2025 +0800
Commit:     John Doe <john@example.com>
CommitDate: Mon Sep 10 14:30:00 2025 +0800

    Test commit
    
 added.txt    | 10 ++++++++++
 modified.txt |  5 +++--
 deleted.txt  |  3 ---
 3 files changed, 13 insertions(+), 5 deletions(-)"""
        
        with patch('subprocess.run') as mock_run:
            mock_run.return_value.returncode = 0
            mock_run.return_value.stdout = git_output
            
            self.view.load_commit_details('abc123def456789')
            lines = self.view.get_display_lines(height=20, width=80, colors_enabled=True)
            
            # Check file change lines - they should be lists of tuples for multi-color
            file_lines = []
            for line in lines:
                if isinstance(line, list):
                    # Multi-colored line (file stats)
                    # Check if it's a file stats line
                    full_text = "".join(text for text, _ in line)
                    if " | " in full_text and ("+" in full_text or "-" in full_text):
                        file_lines.append(line)
            
            assert len(file_lines) >= 3, f"Should have at least 3 file change lines, got {len(file_lines)}"
            
            # Check specific files
            for parts in file_lines:
                full_text = "".join(text for text, _ in parts)
                
                # First part should be filename in blue
                assert len(parts) > 0, "File stats line should have parts"
                filename_part, filename_color = parts[0]
                assert " | " in filename_part, f"First part should contain filename and separator: {filename_part}"
                assert filename_color == 7, f"Filename should be blue (7), got {filename_color}"
                
                if "added.txt" in full_text:
                    # Check that additions are green
                    for text, color in parts[1:]:
                        if "+" in text:
                            assert color == 3, f"Additions (+) should be green (3), got {color}"
                elif "deleted.txt" in full_text:
                    # Check that deletions are red
                    for text, color in parts[1:]:
                        if "-" in text:
                            assert color == 6, f"Deletions (-) should be red (6), got {color}"
                elif "modified.txt" in full_text:
                    # Check mixed changes
                    has_green = False
                    has_red = False
                    for text, color in parts[1:]:
                        if "+" in text:
                            assert color == 3, f"Additions (+) should be green (3), got {color}"
                            has_green = True
                        elif "-" in text:
                            assert color == 6, f"Deletions (-) should be red (6), got {color}"
                            has_red = True
                    assert has_green and has_red, "Modified file should have both green and red parts"
    
    def test_refs_coloring(self):
        """Test that refs (branches/tags) are colored magenta."""
        git_output = """commit abc123def456789
Author:     John Doe <john@example.com>
AuthorDate: Mon Sep 10 14:30:00 2025 +0800
Commit:     John Doe <john@example.com>
CommitDate: Mon Sep 10 14:30:00 2025 +0800

    Test commit"""
        
        with patch('subprocess.run') as mock_run:
            # First call for git show
            first_call = Mock()
            first_call.returncode = 0
            first_call.stdout = git_output
            
            # Second call for git show-ref
            second_call = Mock()
            second_call.returncode = 0
            second_call.stdout = """abc123def456789 refs/heads/main
abc123def456789 refs/tags/v1.0.0"""
            
            mock_run.side_effect = [first_call, second_call]
            
            self.view.load_commit_details('abc123def456789')
            lines = self.view.get_display_lines(height=20, width=80, colors_enabled=True)
            
            # Find refs line
            refs_line = None
            for line in lines:
                if isinstance(line, tuple):
                    text, color = line
                    if text.startswith("Refs:"):
                        refs_line = (text, color)
                        break
            
            assert refs_line is not None, "Refs line not found"
            text, color = refs_line
            assert "[main]" in text or "<v1.0.0>" in text
            assert color == 5, f"Refs line should be magenta (5), got {color}"
    
    def test_summary_line_coloring(self):
        """Test that the summary line is colored based on content."""
        # Test with only insertions
        git_output_additions = """commit abc123
Author:     Test <test@test.com>
AuthorDate: Mon Sep 10 14:30:00 2025 +0800

    Test
    
 file.txt | 5 +++++
 1 file changed, 5 insertions(+)"""
        
        with patch('subprocess.run') as mock_run:
            mock_run.return_value.returncode = 0
            mock_run.return_value.stdout = git_output_additions
            
            self.view.load_commit_details('abc123')
            lines = self.view.get_display_lines(height=20, width=80, colors_enabled=True)
            
            # Find summary line
            for line in lines:
                if isinstance(line, tuple):
                    text, color = line
                    if "insertions(+)" in text and "deletions(-)" not in text:
                        assert color == 3, f"Insertions-only summary should be green (3), got {color}"
                        break


if __name__ == "__main__":
    pytest.main([__file__, "-v"])