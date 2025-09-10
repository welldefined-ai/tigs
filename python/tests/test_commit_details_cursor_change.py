"""Test that commit details view updates correctly when cursor moves."""

import pytest
from unittest.mock import Mock, patch

from src.tui.commit_details_view import CommitDetailsView


class TestCommitDetailsCursorChange:
    """Test that commit details properly update when cursor moves to different commits."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.mock_store = Mock()
        self.mock_store.repo_path = '/test/repo'
        self.view = CommitDetailsView(self.mock_store)
    
    def test_line_wrapping_updates_on_commit_change(self):
        """Test that line wrapping is recalculated when loading a new commit."""
        # First commit with long lines
        git_output1 = """commit abc123
Author:     John Doe with a very long name that will wrap <john.doe.with.very.long.email@example.com>
AuthorDate: Mon Sep 10 14:30:00 2025 +0800

    First commit with a very long message that will definitely wrap when displayed in narrow width
    
 very_long_filename_that_will_wrap.txt | 10 ++++++++++
 1 file changed, 10 insertions(+)"""
        
        # Second commit with different long lines
        git_output2 = """commit def456
Author:     Jane Smith <jane@example.com>
AuthorDate: Tue Sep 11 10:00:00 2025 +0800

    Second commit with different content
    
 another_extremely_long_filename_that_should_also_wrap_differently.py | 25 ++++++++++++++++---------
 short.txt | 2 ++
 2 files changed, 18 insertions(+), 9 deletions(-)"""
        
        with patch('subprocess.run') as mock_run:
            # Load first commit
            mock_run.return_value.returncode = 0
            mock_run.return_value.stdout = git_output1
            
            self.view.load_commit_details('abc123')
            lines1 = self.view.get_display_lines(height=30, width=40, colors_enabled=True)
            
            # Find the long filename in first commit
            found_first_file = False
            for line in lines1:
                if isinstance(line, list):
                    text = "".join(t for t, _ in line)
                    if "very_long_filename" in text:
                        found_first_file = True
                        break
                elif isinstance(line, tuple):
                    if "very_long_filename" in line[0]:
                        found_first_file = True
                        break
            
            assert found_first_file, "Should find first commit's long filename"
            
            # Now load second commit
            mock_run.return_value.stdout = git_output2
            self.view.load_commit_details('def456')
            lines2 = self.view.get_display_lines(height=30, width=40, colors_enabled=True)
            
            # Should NOT find first commit's filename
            # Should find second commit's filename
            found_first_file = False
            found_second_file = False
            
            for line in lines2:
                if isinstance(line, list):
                    text = "".join(t for t, _ in line)
                    if "very_long_filename" in text:
                        found_first_file = True
                    if "another_extremely_long" in text:
                        found_second_file = True
                elif isinstance(line, tuple):
                    text = line[0]
                    if "very_long_filename" in text:
                        found_first_file = True
                    if "another_extremely_long" in text or "Jane Smith" in text:
                        found_second_file = True
            
            assert not found_first_file, "Should NOT find first commit's filename after switching"
            assert found_second_file, "Should find second commit's content"
    
    def test_colors_remain_correct_after_cursor_movement(self):
        """Test that colors are properly applied after moving cursor to a new commit."""
        git_output1 = """commit abc123
Author:     First Author <first@example.com>
AuthorDate: Mon Sep 10 14:30:00 2025 +0800

    First commit
    
 file1.txt | 5 +++++
 1 file changed, 5 insertions(+)"""
        
        git_output2 = """commit def456
Author:     Second Author <second@example.com>
AuthorDate: Tue Sep 11 10:00:00 2025 +0800

    Second commit
    
 file2.py | 10 +++---
 1 file changed, 6 insertions(+), 4 deletions(-)"""
        
        with patch('subprocess.run') as mock_run:
            # Load first commit
            mock_run.return_value.returncode = 0
            mock_run.return_value.stdout = git_output1
            
            self.view.load_commit_details('abc123')
            lines1 = self.view.get_display_lines(height=30, width=80, colors_enabled=True)
            
            # Check first commit's colors
            found_green_commit1 = False
            found_cyan_author1 = False
            
            for line in lines1:
                if isinstance(line, tuple):
                    text, color = line
                    if "abc123" in text and color == 3:
                        found_green_commit1 = True
                    elif "First Author" in text and color == 2:
                        found_cyan_author1 = True
            
            assert found_green_commit1, "First commit SHA should be green"
            assert found_cyan_author1, "First author should be cyan"
            
            # Load second commit
            mock_run.return_value.stdout = git_output2
            self.view.load_commit_details('def456')
            lines2 = self.view.get_display_lines(height=30, width=80, colors_enabled=True)
            
            # Check second commit's colors
            found_green_commit2 = False
            found_cyan_author2 = False
            found_old_commit = False
            
            for line in lines2:
                if isinstance(line, tuple):
                    text, color = line
                    if "def456" in text and color == 3:
                        found_green_commit2 = True
                    elif "Second Author" in text and color == 2:
                        found_cyan_author2 = True
                    elif "abc123" in text:
                        found_old_commit = True
            
            assert found_green_commit2, "Second commit SHA should be green"
            assert found_cyan_author2, "Second author should be cyan"
            assert not found_old_commit, "Should not find first commit's SHA"
    
    def test_narrow_width_recalculation_on_commit_change(self):
        """Test that narrow width wrapping is recalculated correctly when changing commits."""
        # First commit - will wrap differently
        git_output1 = """commit aaaaaaaabbbbbbbbccccccccddddddddeeeeeeeeffffffff
Author:     Developer One <dev1@example.com>
AuthorDate: Mon Sep 10 14:30:00 2025 +0800

    Message one
    
 path/to/first/file.txt | 100 ++++++++++++++++++++++++++++++++++++++++++++++++++++
 1 file changed, 100 insertions(+)"""
        
        # Second commit - different wrapping pattern
        git_output2 = """commit 111111112222222233333333444444445555555566666666
Author:     Dev Two <dev2@example.com>
AuthorDate: Tue Sep 11 10:00:00 2025 +0800

    Message two
    
 different/path/to/second/file.py | 50 +++++++++++++++++++++++--------------------------
 1 file changed, 25 insertions(+), 25 deletions(-)"""
        
        with patch('subprocess.run') as mock_run:
            # Test with very narrow width (must be narrow enough to force SHA wrapping)
            narrow_width = 20
            
            # Load first commit
            mock_run.return_value.returncode = 0
            mock_run.return_value.stdout = git_output1
            
            self.view.load_commit_details('aaaaaaaabbbbbbbbccccccccddddddddeeeeeeeeffffffff')
            lines1 = self.view.get_display_lines(height=50, width=narrow_width, colors_enabled=True)
            
            # Check that first commit is displayed (may be wrapped)
            found_first_commit = False
            for line in lines1:
                if isinstance(line, tuple):
                    text, color = line
                    if "aaaaaaaa" in text:
                        found_first_commit = True
                        # Check it has the right color
                        if "commit" in text or color == 3:
                            assert color == 3, f"Commit SHA should be green, got {color}"
            
            assert found_first_commit, "Should find first commit SHA"
            
            # Load second commit
            mock_run.return_value.stdout = git_output2
            self.view.load_commit_details('111111112222222233333333444444445555555566666666')
            lines2 = self.view.get_display_lines(height=50, width=narrow_width, colors_enabled=True)
            
            # Check that first commit content is gone
            # Check that second commit content is present
            found_first_sha = False
            found_second_sha = False
            
            for line in lines2:
                if isinstance(line, tuple):
                    text, color = line
                    if "aaaaaaaa" in text:
                        found_first_sha = True
                    if "11111111" in text:
                        found_second_sha = True
                        # Check it has the right color
                        if "commit" in text or color == 3:
                            assert color == 3, f"Second commit SHA should be green, got {color}"
            
            assert not found_first_sha, "First commit SHA should not appear"
            assert found_second_sha, "Second commit SHA should appear"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])