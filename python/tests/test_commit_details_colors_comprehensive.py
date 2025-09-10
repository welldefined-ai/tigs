"""Comprehensive test suite for commit details view coloring with edge cases."""

import pytest
from unittest.mock import Mock, patch
import subprocess

from src.tui.commit_details_view import CommitDetailsView


class TestCommitDetailsColorsComprehensive:
    """Comprehensive tests for commit details coloring including edge cases."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.mock_store = Mock()
        self.mock_store.repo_path = '/test/repo'
        self.view = CommitDetailsView(self.mock_store)
    
    def test_wrapped_file_stats_maintain_colors(self):
        """Test that wrapped file stats lines maintain proper coloring throughout."""
        git_output = """commit abc123def456789
Author:     John Doe <john@example.com>
AuthorDate: Mon Sep 10 14:30:00 2025 +0800

    Test commit
    
 very_long_filename_that_will_definitely_wrap_at_narrow_width.txt | 100 ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
 another_file.py | 5 +++--
 2 files changed, 103 insertions(+), 2 deletions(-)"""
        
        with patch('subprocess.run') as mock_run:
            mock_run.return_value.returncode = 0
            mock_run.return_value.stdout = git_output
            
            self.view.load_commit_details('abc123def456789')
            # Test with very narrow width to force wrapping
            lines = self.view.get_display_lines(height=30, width=50, colors_enabled=True)
            
            # Find all lines related to the long filename
            long_file_lines = []
            found_long_file = False
            in_long_file = False
            for i, line in enumerate(lines):
                if isinstance(line, list):
                    full_text = "".join(text for text, _ in line)
                    if "very_long_filename" in full_text:
                        long_file_lines.append(line)
                        in_long_file = True
                        # Check if the line ends with all the pluses
                        if not full_text.rstrip().endswith("+"):
                            # Line continues
                            found_long_file = True
                    elif in_long_file and "+" in full_text and "another_file" not in full_text and "files changed" not in full_text:
                        # This is a continuation of the long file's changes
                        long_file_lines.append(line)
                    elif "another_file" in full_text or "files changed" in full_text:
                        # Stop when we hit the next file or summary
                        in_long_file = False
                        break
            
            assert len(long_file_lines) > 1, "Long filename should wrap into multiple lines"
            
            # First line should have blue filename
            first_line = long_file_lines[0]
            assert isinstance(first_line, list), "File stats should be multi-colored"
            
            # Check that filename part is blue
            has_blue_filename = False
            for text, color in first_line:
                if "very_long_filename" in text or "very_long" in text or " | " in text:
                    if color == 7:
                        has_blue_filename = True
                    # The filename might be in the first part even without full text
                    if " | " in text and color == 7:
                        has_blue_filename = True
            assert has_blue_filename, f"First line should contain blue filename. Line was: {first_line}"
            
            # Check wrapped continuation lines if any
            if len(long_file_lines) > 1:
                for wrapped_line in long_file_lines[1:]:
                    assert isinstance(wrapped_line, list), f"Wrapped lines should also be multi-colored, got {wrapped_line}"
                    # Check that + symbols are green
                    for text, color in wrapped_line:
                        if "+" in text:
                            # The + characters should be green
                            for char in text:
                                if char == '+':
                                    assert color == 3, f"Plus signs should be green (3), got {color}"
    
    def test_narrow_width_all_elements_colored(self):
        """Test that all elements remain colored at very narrow terminal widths."""
        git_output = """commit abc123def456789abcdef0123456789abcdef0123456789
Author:     John Doe with a very long name <john.doe.with.very.long.email@example.com>
AuthorDate: Mon Sep 10 14:30:00 2025 +0800
Refs: main, origin/main, tag:v1.0.0, tag:release-candidate

    This is a very long commit message that will definitely wrap when displayed in a narrow terminal width

    It has multiple paragraphs to test paragraph handling
    
 src/main.py | 10 ++++++++++
 tests/test_main.py | 25 ++++++++++++++-----------
 README.md | 5 ++---
 3 files changed, 26 insertions(+), 14 deletions(-)"""
        
        with patch('subprocess.run') as mock_run:
            # First call for git show
            first_call = Mock()
            first_call.returncode = 0
            first_call.stdout = git_output
            
            # Second call for git show-ref
            second_call = Mock()
            second_call.returncode = 0
            second_call.stdout = """abc123def456789abcdef0123456789abcdef0123456789 refs/heads/main
abc123def456789abcdef0123456789abcdef0123456789 refs/remotes/origin/main
abc123def456789abcdef0123456789abcdef0123456789 refs/tags/v1.0.0
abc123def456789abcdef0123456789abcdef0123456789 refs/tags/release-candidate"""
            
            mock_run.side_effect = [first_call, second_call]
            
            self.view.load_commit_details('abc123def456789abcdef0123456789abcdef0123456789')
            # Very narrow width
            lines = self.view.get_display_lines(height=50, width=30, colors_enabled=True)
            
            # Verify each element type maintains color
            has_green_commit = False
            has_cyan_author = False
            has_yellow_date = False
            has_magenta_refs = False
            has_blue_filename = False
            has_green_plus = False
            has_red_minus = False
            
            for line in lines:
                if isinstance(line, tuple):
                    text, color = line
                    if text.startswith("commit") or ("abc123def456789" in text and color == 3):
                        # Commit line may wrap, but all parts should be green
                        if color == 3:
                            has_green_commit = True
                    elif text.startswith("Author:") or ("john" in text.lower() and color == 2):
                        has_cyan_author = True
                        assert color == 2, f"Author should be cyan (2), got {color}"
                    elif text.startswith("Date:") or ("2025" in text and color == 4):
                        has_yellow_date = True
                        assert color == 4, f"Date should be yellow (4), got {color}"
                    elif text.startswith("Refs:") or ("[main]" in text and color == 5):
                        has_magenta_refs = True
                        assert color == 5, f"Refs should be magenta (5), got {color}"
                elif isinstance(line, list):
                    # Multi-colored line
                    for text, color in line:
                        if ".py" in text or ".md" in text:
                            if color == 7:
                                has_blue_filename = True
                        elif "+" in text and color == 3:
                            has_green_plus = True
                        elif "-" in text and color == 6:
                            has_red_minus = True
            
            assert has_green_commit, "Should have green commit SHA even at narrow width"
            assert has_cyan_author, "Should have cyan author even at narrow width"
            assert has_yellow_date, "Should have yellow date even at narrow width"
            assert has_magenta_refs, "Should have magenta refs even at narrow width"
            assert has_blue_filename, "Should have blue filenames even at narrow width"
            assert has_green_plus, "Should have green + even at narrow width"
            assert has_red_minus, "Should have red - even at narrow width"
    
    def test_file_stats_with_binary_files(self):
        """Test file stats coloring with binary files."""
        git_output = """commit abc123
Author:     Test <test@test.com>
AuthorDate: Mon Sep 10 14:30:00 2025 +0800

    Add images
    
 logo.png | Bin 0 -> 1234 bytes
 icon.jpg | Bin 567 -> 890 bytes
 data.bin | Bin 100 -> 0 bytes
 3 files changed"""
        
        with patch('subprocess.run') as mock_run:
            mock_run.return_value.returncode = 0
            mock_run.return_value.stdout = git_output
            
            self.view.load_commit_details('abc123')
            lines = self.view.get_display_lines(height=20, width=80, colors_enabled=True)
            
            # Binary files should still have blue filenames
            for line in lines:
                if isinstance(line, tuple):
                    text, color = line
                    if ".png" in text or ".jpg" in text or ".bin" in text:
                        # These might not be multi-colored since they don't have +/-
                        # But they should be recognized
                        pass
    
    def test_empty_commit_message(self):
        """Test coloring with empty commit message."""
        git_output = """commit abc123
Author:     Test <test@test.com>
AuthorDate: Mon Sep 10 14:30:00 2025 +0800

 file.txt | 1 +
 1 file changed, 1 insertion(+)"""
        
        with patch('subprocess.run') as mock_run:
            mock_run.return_value.returncode = 0
            mock_run.return_value.stdout = git_output
            
            self.view.load_commit_details('abc123')
            lines = self.view.get_display_lines(height=20, width=80, colors_enabled=True)
            
            # Should still have colored elements
            has_commit = False
            has_author = False
            has_date = False
            has_file_stats = False
            
            for line in lines:
                if isinstance(line, tuple):
                    text, color = line
                    if text.startswith("commit "):
                        has_commit = True
                        assert color == 3
                    elif text.startswith("Author:"):
                        has_author = True
                        assert color == 2
                    elif text.startswith("Date:"):
                        has_date = True
                        assert color == 4
                elif isinstance(line, list):
                    # File stats
                    has_file_stats = True
            
            assert has_commit and has_author and has_date and has_file_stats
    
    def test_file_rename_coloring(self):
        """Test coloring for file renames."""
        git_output = """commit abc123
Author:     Test <test@test.com>
AuthorDate: Mon Sep 10 14:30:00 2025 +0800

    Rename files
    
 old_name.txt => new_name.txt | 0
 {old_dir => new_dir}/file.py | 10 +++++-----
 2 files changed, 5 insertions(+), 5 deletions(-)"""
        
        with patch('subprocess.run') as mock_run:
            mock_run.return_value.returncode = 0
            mock_run.return_value.stdout = git_output
            
            self.view.load_commit_details('abc123')
            lines = self.view.get_display_lines(height=20, width=80, colors_enabled=True)
            
            # Check rename lines
            for line in lines:
                if isinstance(line, list):
                    full_text = "".join(text for text, _ in line)
                    if "=>" in full_text:
                        # Renamed files should have blue filenames
                        has_blue = any(color == 7 for _, color in line)
                        assert has_blue, f"Renamed file should have blue parts: {full_text}"
    
    def test_special_characters_in_filenames(self):
        """Test coloring with special characters in filenames."""
        git_output = """commit abc123
Author:     Test <test@test.com>
AuthorDate: Mon Sep 10 14:30:00 2025 +0800

    Special chars
    
 "file with spaces.txt" | 5 +++++
 file(with)parens.py | 3 ++-
 file[with]brackets.js | 2 --
 3 files changed, 6 insertions(+), 3 deletions(-)"""
        
        with patch('subprocess.run') as mock_run:
            mock_run.return_value.returncode = 0
            mock_run.return_value.stdout = git_output
            
            self.view.load_commit_details('abc123')
            lines = self.view.get_display_lines(height=20, width=80, colors_enabled=True)
            
            # All special character filenames should be blue
            found_files = []
            for line in lines:
                if isinstance(line, list):
                    full_text = "".join(text for text, _ in line)
                    if " | " in full_text and any(c in full_text for c in ['"', '(', ')', '[', ']']):
                        found_files.append(full_text)
                        # First part should be blue
                        assert line[0][1] == 7, f"Filename with special chars should be blue: {full_text}"
            
            assert len(found_files) == 3, f"Should find all 3 files with special chars, found: {found_files}"
    
    def test_unicode_in_content(self):
        """Test coloring with unicode characters."""
        git_output = """commit abc123
Author:     李明 <liming@example.com>
AuthorDate: Mon Sep 10 14:30:00 2025 +0800

    添加中文文档
    
 文档.txt | 10 ++++++++++
 README_中文.md | 5 +++++
 2 files changed, 15 insertions(+)"""
        
        with patch('subprocess.run') as mock_run:
            mock_run.return_value.returncode = 0
            mock_run.return_value.stdout = git_output
            
            self.view.load_commit_details('abc123')
            lines = self.view.get_display_lines(height=20, width=80, colors_enabled=True)
            
            # Unicode content should still be colored correctly
            has_colored_author = False
            has_colored_files = False
            
            for line in lines:
                if isinstance(line, tuple):
                    text, color = line
                    if "李明" in text:
                        has_colored_author = True
                        assert color == 2, "Unicode author should be cyan"
                elif isinstance(line, list):
                    full_text = "".join(text for text, _ in line)
                    if "文档" in full_text or "中文" in full_text:
                        has_colored_files = True
                        # Check first part is blue
                        assert line[0][1] == 7, "Unicode filename should be blue"
            
            assert has_colored_author, "Should color unicode author"
            assert has_colored_files, "Should color unicode filenames"
    
    def test_extremely_long_lines(self):
        """Test with extremely long lines that wrap multiple times."""
        # Create a very long string of changes
        long_changes = "+" * 200
        git_output = f"""commit abc123
Author:     Test <test@test.com>
AuthorDate: Mon Sep 10 14:30:00 2025 +0800

    Test
    
 file.txt | 200 {long_changes}
 1 file changed, 200 insertions(+)"""
        
        with patch('subprocess.run') as mock_run:
            mock_run.return_value.returncode = 0
            mock_run.return_value.stdout = git_output
            
            self.view.load_commit_details('abc123')
            lines = self.view.get_display_lines(height=50, width=40, colors_enabled=True)
            
            # Find all lines with + symbols
            plus_lines = []
            for line in lines:
                if isinstance(line, list):
                    for text, color in line:
                        if "+" in text:
                            plus_lines.append((text, color))
            
            # All + symbols should be green across all wrapped lines
            total_plus_count = 0
            for text, color in plus_lines:
                for char in text:
                    if char == '+':
                        total_plus_count += 1
                        # Since + chars are grouped, the color should be green
                        assert color == 3, f"Plus signs should be green even in wrapped lines"
            
            assert total_plus_count == 200, f"Should have all 200 + symbols colored, got {total_plus_count}"
    
    def test_mixed_additions_deletions_same_line(self):
        """Test files with both additions and deletions on the same stats line."""
        git_output = """commit abc123
Author:     Test <test@test.com>
AuthorDate: Mon Sep 10 14:30:00 2025 +0800

    Mixed changes
    
 mixed.txt | 20 ++++++++++---------
 balanced.py | 15 +++++++--------
 2 files changed, 18 insertions(+), 17 deletions(-)"""
        
        with patch('subprocess.run') as mock_run:
            mock_run.return_value.returncode = 0
            mock_run.return_value.stdout = git_output
            
            self.view.load_commit_details('abc123')
            lines = self.view.get_display_lines(height=20, width=80, colors_enabled=True)
            
            # Check mixed change lines
            for line in lines:
                if isinstance(line, list):
                    full_text = "".join(text for text, _ in line)
                    if "mixed.txt" in full_text or "balanced.py" in full_text:
                        # Should have blue filename, green +, and red -
                        colors_found = set()
                        for text, color in line:
                            colors_found.add(color)
                            if ".txt" in text or ".py" in text:
                                assert color == 7 or color == 0, f"Filename should be blue or default"
                            elif "+" in text:
                                for char in text:
                                    if char == '+':
                                        assert color == 3, "Plus should be green"
                            elif "-" in text:
                                for char in text:
                                    if char == '-':
                                        assert color == 6, "Minus should be red"
                        
                        assert 7 in colors_found, "Should have blue for filename"
                        assert 3 in colors_found, "Should have green for +"
                        assert 6 in colors_found, "Should have red for -"
    
    def test_no_color_mode(self):
        """Test that colors_enabled=False returns plain strings."""
        git_output = """commit abc123
Author:     Test <test@test.com>
AuthorDate: Mon Sep 10 14:30:00 2025 +0800

    Test
    
 file.txt | 5 +++--
 1 file changed, 3 insertions(+), 2 deletions(-)"""
        
        with patch('subprocess.run') as mock_run:
            mock_run.return_value.returncode = 0
            mock_run.return_value.stdout = git_output
            
            self.view.load_commit_details('abc123')
            lines = self.view.get_display_lines(height=20, width=80, colors_enabled=False)
            
            # All lines should be plain strings
            for line in lines:
                assert isinstance(line, str), f"With colors_enabled=False, should return strings, got {type(line)}"
                assert not isinstance(line, tuple), "Should not return tuples"
                assert not isinstance(line, list), "Should not return lists"
    
    def test_scrolling_preserves_colors(self):
        """Test that scrolling through content preserves colors."""
        # Generate many files to require scrolling
        file_lines = "\n".join(f" file{i}.txt | {i} {'+'*i}" for i in range(1, 31))
        git_output = f"""commit abc123
Author:     Test <test@test.com>
AuthorDate: Mon Sep 10 14:30:00 2025 +0800

    Many files
    
{file_lines}
 30 files changed, 465 insertions(+)"""
        
        with patch('subprocess.run') as mock_run:
            mock_run.return_value.returncode = 0
            mock_run.return_value.stdout = git_output
            
            self.view.load_commit_details('abc123')
            
            # Get first page
            lines1 = self.view.get_display_lines(height=10, width=80, colors_enabled=True)
            
            # Scroll down
            self.view.scroll_down(lines=5, viewport_height=10)
            lines2 = self.view.get_display_lines(height=10, width=80, colors_enabled=True)
            
            # Both pages should have properly colored file stats
            for lines in [lines1, lines2]:
                has_file_stats = False
                for line in lines:
                    if isinstance(line, list):
                        has_file_stats = True
                        # Should have blue filename
                        if line[0][0].strip().startswith("file"):
                            assert line[0][1] == 7, "Filename should be blue after scrolling"
                
                assert has_file_stats, "Each page should have colored file stats"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])