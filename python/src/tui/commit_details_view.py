"""Commit details view for displaying full commit information."""

import subprocess
from typing import List, Optional
from .text_utils import word_wrap


class CommitDetailsView:
    """Displays detailed commit information including message and changed files."""
    
    def __init__(self, store):
        """Initialize commit details view.
        
        Args:
            store: TigsStore instance for Git operations
        """
        self.store = store
        self.current_sha = None
        self.details_lines = []
    
    def load_commit_details(self, sha: str) -> None:
        """Load detailed information for a commit.
        
        Args:
            sha: Full SHA of the commit to display
        """
        if sha == self.current_sha:
            return
        
        self.current_sha = sha
        self.details_lines = []
        
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
            
            self.details_lines = formatted_lines
            
        except Exception as e:
            self.details_lines = [f"Error: {str(e)}"]
    
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
        
        if not self.details_lines:
            return ["Loading..."]
        
        # Format lines to fit width
        formatted = []
        for line in self.details_lines:
            if len(line) <= width - 4:
                formatted.append(line)
            else:
                # Word wrap long lines
                wrapped = word_wrap(line, width - 4)
                formatted.extend(wrapped)
        
        # Truncate to available height
        if len(formatted) > height - 2:
            formatted = formatted[:height - 2]
        
        return formatted