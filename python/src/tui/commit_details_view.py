"""Commit details view for displaying full commit information."""

import curses
import subprocess
from typing import List, Optional
from .text_utils import word_wrap
from .view_scroll_mixin import ViewScrollMixin
from .color_constants import (
    COLOR_DEFAULT, COLOR_AUTHOR, COLOR_COMMIT, COLOR_DATE,
    COLOR_REFS, COLOR_DELETE, COLOR_METADATA
)


class CommitDetailsView(ViewScrollMixin):
    """Displays detailed commit information including message and changed files."""
    
    def __init__(self, store):
        """Initialize commit details view.
        
        Args:
            store: TigsStore instance for Git operations
        """
        ViewScrollMixin.__init__(self)
        self.store = store
        self.current_sha = None
    
    def load_commit_details(self, sha: str) -> None:
        """Load detailed information for a commit.
        
        Args:
            sha: Full SHA of the commit to display
        """
        if sha == self.current_sha:
            return
        
        self.current_sha = sha
        
        try:
            # Get commit information using git show
            result = subprocess.run(
                ["git", "show", "--stat", "--format=fuller", sha],
                cwd=self.store.repo_path,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace"
            )
            
            if result.returncode != 0:
                self.details_lines = ["Error loading commit details"]
                return
            
            # Parse the output
            lines = result.stdout.split('\n')
            formatted_lines = []
            
            # Process commit header
            in_header = True
            in_message = False
            message_lines = []
            
            for line in lines:
                if in_header:
                    if line.startswith("commit "):
                        # Commit SHA line
                        formatted_lines.append(line)
                    elif line.startswith("Author:"):
                        # Author line
                        formatted_lines.append(line)
                    elif line.startswith("AuthorDate:"):
                        # Extract just the date part
                        date_part = line.replace("AuthorDate:", "Date:")
                        formatted_lines.append(date_part)
                    elif line.startswith("Commit:") or line.startswith("CommitDate:"):
                        # Skip commit/commit date (we show author date)
                        continue
                    elif line == "":
                        if not in_message:
                            # Empty line before commit message
                            in_header = False
                            in_message = True
                            formatted_lines.append("")
                        else:
                            # Empty line in message
                            message_lines.append("")
                    else:
                        # Part of header we want to keep
                        formatted_lines.append(line)
                elif in_message:
                    if line and not line[0].isspace() and '|' in line:
                        # Reached the file stats section
                        in_message = False
                        # Add the collected message
                        for msg_line in message_lines:
                            formatted_lines.append(msg_line)
                        formatted_lines.append("")
                        formatted_lines.append(line)
                    else:
                        # Part of commit message
                        message_lines.append(line)
                else:
                    # File stats section
                    formatted_lines.append(line)
            
            # If we never hit the stats section, add remaining message lines
            if in_message and message_lines:
                for msg_line in message_lines:
                    formatted_lines.append(msg_line)
            
            # Also get refs (branches and tags) for this commit
            refs_result = subprocess.run(
                ["git", "show-ref", "--dereference"],
                cwd=self.store.repo_path,
                capture_output=True,
                text=True
            )
            
            if refs_result.returncode == 0:
                refs = []
                for ref_line in refs_result.stdout.split('\n'):
                    if sha in ref_line:
                        # Extract ref name
                        parts = ref_line.split()
                        if len(parts) >= 2:
                            ref_name = parts[1]
                            if ref_name.startswith("refs/heads/"):
                                refs.append(f"[{ref_name.replace('refs/heads/', '')}]")
                            elif ref_name.startswith("refs/tags/"):
                                refs.append(f"<{ref_name.replace('refs/tags/', '')}>")
                            elif ref_name.startswith("refs/remotes/"):
                                refs.append(f"{{{ref_name.replace('refs/remotes/', '')}}}")
                
                if refs:
                    # Insert refs after commit line
                    for i, line in enumerate(formatted_lines):
                        if line.startswith("commit "):
                            refs_line = f"Refs: {', '.join(refs)}"
                            formatted_lines.insert(i + 1, refs_line)
                            break
            
            # Store all formatted lines without truncation
            self.total_lines = formatted_lines
            # Reset view to top when loading new content
            self.reset_view()
            # Clear cached formatted lines to force re-wrapping
            if hasattr(self, '_formatted_lines'):
                del self._formatted_lines
            if hasattr(self, '_line_colors'):
                del self._line_colors
            if hasattr(self, '_file_stats_info'):
                del self._file_stats_info
            
        except Exception as e:
            self.total_lines = [f"Error: {str(e)}"]
    
    def _is_file_stats_line(self, line: str) -> bool:
        """Check if a line is a file stats line (not a commit message line with |).
        
        File stats lines have the format:
        - Start with single space (not 4 spaces like commit messages)
        - Have " | " separator
        - After separator have numbers, +/-, "Bin", or just 0
        
        Args:
            line: Line to check
            
        Returns:
            True if this is a file stats line, False otherwise
        """
        if " | " not in line:
            return False
        
        # Commit message lines are indented with 4 spaces
        # File stats lines typically have 1 space
        if line.startswith("    "):
            return False
        
        # Check the part after " | "
        pipe_idx = line.index(" | ")
        after_pipe = line[pipe_idx + 3:].strip()
        
        # File stats have numbers, +/-, Bin, or combinations
        if not after_pipe:
            return False
        
        # Check for typical file stats patterns
        # Numbers (including 0 for renames)
        if after_pipe[0].isdigit():
            return True
        # Binary files
        if after_pipe.startswith("Bin"):
            return True
        # Direct +/- (rare but possible)
        if after_pipe[0] in "+-":
            return True
        
        return False
    
    def handle_input(self, key: int, pane_height: int) -> bool:
        """Handle keyboard input for scrolling.
        
        Args:
            key: Key code
            pane_height: Height of the pane
            
        Returns:
            True if handled, False otherwise
        """
        if key == curses.KEY_UP:
            return self.scroll_up()
        elif key == curses.KEY_DOWN:
            return self.scroll_down(viewport_height=pane_height)
        return False
    
    def get_display_lines(self, height: int, width: int, colors_enabled: bool = False) -> List:
        """Get display lines for the details pane with optional color coding.
        
        Args:
            height: Available height for content
            width: Available width for content
            colors_enabled: Whether to return colored output
            
        Returns:
            List of formatted detail lines (strings or (text, color_pair) tuples)
        """
        if not self.current_sha:
            return ["No commit selected"]
        
        if not self.total_lines:
            return ["Loading..."]
        
        # Format lines to fit width and track colors if needed
        if not hasattr(self, '_formatted_lines') or self._last_width != width or not hasattr(self, '_line_colors'):
            self._formatted_lines = []
            self._line_colors = []  # Track color for each formatted line
            self._file_stats_info = []  # Track original file stats info for wrapped lines
            
            for line in self.total_lines:
                # Determine color for this line before wrapping
                color_pair = COLOR_DEFAULT  # Default color
                file_stats_data = None  # Will store (filename, changes) for file stats lines
                
                # Always calculate colors, we'll decide whether to use them later
                line_stripped = line.lstrip()
                
                if line.startswith("commit "):
                    color_pair = COLOR_COMMIT  # Green for entire commit line including SHA
                elif line_stripped.startswith("Author:"):
                    color_pair = COLOR_AUTHOR  # Cyan for entire author line including email
                elif line_stripped.startswith("Date:"):
                    color_pair = COLOR_DATE  # Yellow for entire date line including time
                elif line_stripped.startswith("Refs:"):
                    color_pair = COLOR_REFS  # Magenta for refs
                elif " | " in line and self._is_file_stats_line(line):
                    # File stats line - will need special handling for multi-color
                    # This includes regular changes, binary files, and renames with 0 changes
                    # Mark it with a special color to identify it later
                    color_pair = -1  # Special marker for file stats lines
                    # Store the file stats data for wrapped lines
                    pipe_idx = line.index(" | ")
                    file_stats_data = (line[:pipe_idx + 3], line[pipe_idx + 3:])
                elif "file changed" in line or "files changed" in line:
                    # Summary line
                    if "insertions(+)" in line and "deletions(-)" not in line:
                        color_pair = COLOR_COMMIT  # Green for only insertions
                    elif "deletions(-)" in line and "insertions(+)" not in line:
                        color_pair = COLOR_DELETE  # Red for only deletions
                    else:
                        color_pair = COLOR_DEFAULT  # Default for mixed
                
                # Now wrap the line and apply the same color to all wrapped parts
                if len(line) <= width - 4:
                    self._formatted_lines.append(line)
                    self._line_colors.append(color_pair)
                    self._file_stats_info.append(file_stats_data)
                else:
                    # Word wrap long lines
                    wrapped = word_wrap(line, width - 4)
                    for i, wrapped_line in enumerate(wrapped):
                        self._formatted_lines.append(wrapped_line)
                        self._line_colors.append(color_pair)  # Same color for wrapped parts
                        # For file stats lines, store the original data for all wrapped parts
                        self._file_stats_info.append(file_stats_data if color_pair == -1 else None)
            
            self._last_width = width
            # Update total_lines to use formatted version
            self.total_lines = self._formatted_lines
        
        # Get visible lines based on scroll position
        visible_lines = self.get_visible_lines(height)
        start_idx = self.view_offset
        
        # Apply colors if enabled
        if colors_enabled:
            colored_lines = []
            for i, line in enumerate(visible_lines):
                # Get the color for this line from our pre-calculated colors
                line_idx = start_idx + i
                if line_idx < len(self._line_colors):
                    color_pair = self._line_colors[line_idx]
                else:
                    color_pair = COLOR_DEFAULT
                
                # Check if this is a file stats line (original or wrapped)
                file_stats_data = None
                if line_idx < len(self._file_stats_info):
                    file_stats_data = self._file_stats_info[line_idx]
                
                # Special handling for file stats lines
                if color_pair == -1 and file_stats_data:
                    parts = []
                    filename_part, changes_part = file_stats_data
                    
                    # Check what part of the file stats this line represents
                    if " | " in line:
                        # This is the line with the separator
                        pipe_idx = line.index(" | ")
                        actual_filename = line[:pipe_idx + 3]  # Include " | "
                        parts.append((actual_filename, COLOR_METADATA))  # Blue for filename
                        
                        # Changes part after the pipe
                        actual_changes = line[pipe_idx + 3:]
                    elif "+" in changes_part or "-" in changes_part:
                        # Check if this line is part of the filename or the changes
                        # If the original filename part contains this line, it's filename
                        if line in filename_part:
                            # This is a wrapped part of the filename (before the separator)
                            parts.append((line, COLOR_METADATA))  # Blue for filename part
                            actual_changes = ""
                        else:
                            # This is a wrapped continuation of the changes
                            actual_changes = line
                    else:
                        # No changes, just filename
                        parts.append((line, COLOR_METADATA))
                        actual_changes = ""
                    
                    # Color the changes part
                    if actual_changes:
                        change_chars = []
                        for char in actual_changes:
                            if char == '+':
                                change_chars.append((char, COLOR_COMMIT))  # Green for +
                            elif char == '-':
                                change_chars.append((char, COLOR_DELETE))  # Red for -
                            else:
                                change_chars.append((char, COLOR_DEFAULT))  # Default for other chars
                        
                        # Combine consecutive chars with same color
                        if change_chars:
                            current_text = change_chars[0][0]
                            current_color = change_chars[0][1]
                            for char, color in change_chars[1:]:
                                if color == current_color:
                                    current_text += char
                                else:
                                    parts.append((current_text, current_color))
                                    current_text = char
                                    current_color = color
                            parts.append((current_text, current_color))
                    
                    colored_lines.append(parts)  # Return list of parts
                else:
                    colored_lines.append((line, color_pair))
            return colored_lines
        else:
            return visible_lines