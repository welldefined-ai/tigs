"""Test coloring for renamed files with 0 changes."""

import pytest
from unittest.mock import Mock, patch

from src.tui.commit_details_view import CommitDetailsView


class TestRenameZeroChanges:
    """Test that renamed files with 0 changes are colored correctly."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.mock_store = Mock()
        self.mock_store.repo_path = '/test/repo'
        self.view = CommitDetailsView(self.mock_store)
    
    def test_rename_zero_changes_are_colored(self):
        """Test that renamed files with 0 changes are properly colored (not black).
        
        This was the reported bug: "python/src/tui/{layout.py => layout_manager.py} | 0"
        appeared in black instead of blue.
        """
        git_output = """commit abc123
Author:     Test <test@test.com>
AuthorDate: Mon Sep 10 14:30:00 2025 +0800

    Refactor directory structure
    
 python/src/tui/{layout.py => layout_manager.py} | 0
 old_name.txt => new_name.txt | 0
 {old_dir => new_dir}/file.py | 0
 3 files changed, 0 insertions(+), 0 deletions(-)"""
        
        with patch('subprocess.run') as mock_run:
            mock_run.return_value.returncode = 0
            mock_run.return_value.stdout = git_output
            
            self.view.load_commit_details('abc123')
            lines = self.view.get_display_lines(height=20, width=80, colors_enabled=True)
            
            # Find rename lines
            rename_lines = []
            for line in lines:
                if isinstance(line, list):
                    text = "".join(t for t, _ in line)
                    if "=>" in text and " | 0" in text:
                        rename_lines.append(line)
                        # Should be multi-colored with blue filename
                        assert line[0][1] == 7, f"Renamed file should have blue filename: {text}"
                elif isinstance(line, tuple):
                    text, color = line
                    if "=>" in text and " | 0" in text:
                        # This was the bug - should not be a plain tuple
                        assert False, f"Rename with 0 changes should be multi-colored, not black: {text}"
            
            assert len(rename_lines) == 3, f"Should find 3 rename lines, found {len(rename_lines)}"
    
    


if __name__ == "__main__":
    pytest.main([__file__, "-v"])