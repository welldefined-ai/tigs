"""Commit details view for displaying full commit information."""

import curses
import subprocess
from typing import List, Optional
from .text_utils import word_wrap
from .view_scroll_mixin import ViewScrollMixin


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
            
        except Exception as e:
            self.total_lines = [f"Error: {str(e)}"]
    
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
    
    def get_display_lines(self, height: int, width: int) -> List[str]:
        """Get display lines for the details pane.
        
        Args:
            height: Available height for content
            width: Available width for content
            
        Returns:
            List of formatted detail lines
        """
        if not self.current_sha:
            return ["No commit selected"]
        
        if not self.total_lines:
            return ["Loading..."]
        
        # Format lines to fit width if needed
        if not hasattr(self, '_formatted_lines') or self._last_width != width:
            self._formatted_lines = []
            for line in self.total_lines:
                if len(line) <= width - 4:
                    self._formatted_lines.append(line)
                else:
                    # Word wrap long lines
                    wrapped = word_wrap(line, width - 4)
                    self._formatted_lines.extend(wrapped)
            self._last_width = width
            # Update total_lines to use formatted version
            self.total_lines = self._formatted_lines
        
        # Return visible lines based on scroll position
        return self.get_visible_lines(height)