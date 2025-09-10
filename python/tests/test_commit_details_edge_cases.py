"""Edge case tests for commit details view to prevent regressions."""

import pytest
from unittest.mock import Mock, patch

from src.tui.commit_details_view import CommitDetailsView


class TestCommitDetailsEdgeCases:
    """Guard tests for edge cases that were previously bugs."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.mock_store = Mock()
        self.mock_store.repo_path = '/test/repo'
        self.view = CommitDetailsView(self.mock_store)
    
    def test_binary_files_are_colored(self):
        """Test that binary files are properly handled and colored.
        
        Binary files don't have +/- but should still have blue filenames.
        """
        git_output = """commit abc123
Author:     Test <test@test.com>
AuthorDate: Mon Sep 10 14:30:00 2025 +0800

    Add binary files
    
 logo.png | Bin 0 -> 1234 bytes
 data.bin | Bin 5678 -> 9012 bytes
 2 files changed"""
        
        with patch('subprocess.run') as mock_run:
            mock_run.return_value.returncode = 0
            mock_run.return_value.stdout = git_output
            
            self.view.load_commit_details('abc123')
            lines = self.view.get_display_lines(height=20, width=80, colors_enabled=True)
            
            # Binary files should be multi-colored with blue filenames
            binary_count = 0
            for line in lines:
                if isinstance(line, list):
                    text = "".join(t for t, _ in line)
                    if "Bin" in text and " | " in text:
                        binary_count += 1
                        # First part should be blue
                        assert line[0][1] == 7, f"Binary file should have blue filename: {text}"
            
            assert binary_count == 2, f"Should find 2 binary files, found {binary_count}"
    
    def test_file_stats_at_view_bottom(self):
        """Test that file stats at the bottom of the view are still colored.
        
        This guards against the issue where only partially visible files lost color.
        """
        # Create many files so some will be at the bottom
        file_lines = []
        for i in range(1, 16):
            file_lines.append(f" file{i:02d}.txt | {i} {'+'*min(i, 10)}")
        
        git_output = f"""commit abc123
Author:     Test <test@test.com>
AuthorDate: Mon Sep 10 14:30:00 2025 +0800

    Many files
    
{chr(10).join(file_lines)}
 15 files changed, 120 insertions(+)"""
        
        with patch('subprocess.run') as mock_run:
            mock_run.return_value.returncode = 0
            mock_run.return_value.stdout = git_output
            
            self.view.load_commit_details('abc123')
            
            # Use small height so not all files fit
            height = 10
            
            # Scroll to bottom
            for _ in range(20):
                self.view.scroll_down(viewport_height=height)
            
            lines = self.view.get_display_lines(height=height, width=80, colors_enabled=True)
            
            # Check that visible file lines are colored
            for line in lines:
                if isinstance(line, list):
                    text = "".join(t for t, _ in line)
                    if " | " in text and "file" in text:
                        # Should be blue
                        assert line[0][1] == 7, f"File at bottom should have blue filename"
    
    def test_wrapped_filename_maintains_color(self):
        """Test that wrapped long filenames maintain blue color on all parts.
        
        Guards against wrapped parts losing color.
        """
        git_output = """commit abc123
Author:     Test <test@test.com>
AuthorDate: Mon Sep 10 14:30:00 2025 +0800

    Test
    
 this_is_an_extremely_long_filename_that_will_definitely_wrap_at_narrow_width.txt | 50 ++++++++++++++++++++++++++++++++++++++++++++++++++
 1 file changed, 50 insertions(+)"""
        
        with patch('subprocess.run') as mock_run:
            mock_run.return_value.returncode = 0
            mock_run.return_value.stdout = git_output
            
            self.view.load_commit_details('abc123')
            
            # Use narrow width to force wrapping
            lines = self.view.get_display_lines(height=20, width=35, colors_enabled=True)
            
            # Find all parts of the wrapped filename
            filename_parts = []
            for line in lines:
                if isinstance(line, list):
                    text = "".join(t for t, _ in line)
                    if any(x in text for x in ["extremely_long", "definitely_wrap", ".txt"]):
                        filename_parts.append(line)
            
            # All parts should have blue first element
            assert len(filename_parts) > 1, "Long filename should wrap"
            for part in filename_parts:
                assert part[0][1] == 7, f"All wrapped filename parts should be blue"
    
    def test_cursor_movement_refreshes_wrapping(self):
        """Test that moving cursor between commits properly refreshes line wrapping.
        
        This was a bug where cached formatting wasn't cleared on commit change.
        """
        git_output1 = """commit abc123
Author:     First <first@test.com>
AuthorDate: Mon Sep 10 14:30:00 2025 +0800

    First commit with specific content
    
 first_file.txt | 10 ++++++++++
 1 file changed, 10 insertions(+)"""
        
        git_output2 = """commit def456
Author:     Second <second@test.com>
AuthorDate: Tue Sep 11 10:00:00 2025 +0800

    Second commit with different content
    
 completely_different_file.py | 20 ++++++++++++++------
 1 file changed, 14 insertions(+), 6 deletions(-)"""
        
        with patch('subprocess.run') as mock_run:
            # Load first commit
            mock_run.return_value.returncode = 0
            mock_run.return_value.stdout = git_output1
            
            self.view.load_commit_details('abc123')
            lines1 = self.view.get_display_lines(height=20, width=40, colors_enabled=True)
            
            # Find first file
            found_first = False
            for line in lines1:
                if isinstance(line, list):
                    text = "".join(t for t, _ in line)
                    if "first_file.txt" in text:
                        found_first = True
            assert found_first, "Should find first file"
            
            # Load second commit
            mock_run.return_value.stdout = git_output2
            self.view.load_commit_details('def456')
            lines2 = self.view.get_display_lines(height=20, width=40, colors_enabled=True)
            
            # Should NOT find first file, should find second
            found_first = False
            found_second = False
            for line in lines2:
                if isinstance(line, list):
                    text = "".join(t for t, _ in line)
                    if "first_file.txt" in text:
                        found_first = True
                    if "completely_different_file.py" in text:
                        found_second = True
                elif isinstance(line, tuple):
                    text = line[0]
                    if "first_file.txt" in text:
                        found_first = True
                    if "Second" in text:
                        found_second = True
            
            assert not found_first, "Should not find first file after commit change"
            assert found_second, "Should find second commit's content"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])