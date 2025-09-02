"""Commit view management for TUI."""

import curses
import subprocess
from typing import List, Tuple, Optional, Set, Dict
from datetime import datetime, timedelta
import re


class CommitView:
    """Manages commit display and interaction."""
    
    def __init__(self, store):
        """Initialize commit view.
        
        Args:
            store: TigsStore instance for Git operations
        """
        self.store = store
        self.commits: List[Dict] = []  # List of commit info dicts
        self.commit_cursor_idx = 0
        self.commit_scroll_offset = 0
        self.selected_commits: Set[int] = set()
        self.visual_mode = False
        self.visual_start_idx: Optional[int] = None
        self.commits_with_notes: Set[str] = set()  # Set of SHAs that have notes
        
        # Load commits on initialization
        self.load_commits()
    
    def load_commits(self, limit: int = 50) -> None:
        """Load commits from git log.
        
        Args:
            limit: Maximum number of commits to load initially
        """
        try:
            # Get list of commits with notes first
            self.commits_with_notes = set(self.store.list_chats())
            
            # Get commit log with format: SHA|subject|author|timestamp
            result = subprocess.run(
                ["git", "log", "--oneline", "--date-order", 
                 f"-{limit}", "--format=%H|%s|%an|%at"],
                cwd=self.store.repo_path,
                capture_output=True,
                text=True,
                check=True
            )
            
            self.commits = []
            for line in result.stdout.strip().split('\n'):
                if not line:
                    continue
                    
                parts = line.split('|', 3)
                if len(parts) >= 4:
                    sha, subject, author, timestamp = parts
                    
                    # Convert timestamp to datetime
                    commit_time = datetime.fromtimestamp(int(timestamp))
                    
                    self.commits.append({
                        'sha': sha[:7],  # Short SHA
                        'full_sha': sha,
                        'subject': subject[:50],  # Truncate long subjects
                        'author': author,
                        'time': commit_time,
                        'has_note': sha in self.commits_with_notes
                    })
            
            # Reset cursor and scroll position
            self.commit_cursor_idx = 0
            self.commit_scroll_offset = 0
            
        except subprocess.CalledProcessError:
            # No commits or git error
            self.commits = []
    
    def get_display_lines(self, height: int) -> List[str]:
        """Get display lines for commits pane.
        
        Args:
            height: Available height for content
            
        Returns:
            List of formatted commit lines
        """
        lines = []
        
        if not self.commits:
            lines.append("(No commits to display)")
            return lines
        
        # Calculate visible range with scrolling
        visible_count = min(height - 2, len(self.commits))  # -2 for borders
        
        # Adjust scroll offset if needed
        if self.commit_cursor_idx < self.commit_scroll_offset:
            self.commit_scroll_offset = self.commit_cursor_idx
        elif self.commit_cursor_idx >= self.commit_scroll_offset + visible_count:
            self.commit_scroll_offset = self.commit_cursor_idx - visible_count + 1
        
        # Build display lines
        for i in range(self.commit_scroll_offset, 
                      min(self.commit_scroll_offset + visible_count, len(self.commits))):
            commit = self.commits[i]
            
            # Check if selected
            is_selected = i in self.selected_commits
            
            # In visual mode, check if in range
            if self.visual_mode and self.visual_start_idx is not None:
                visual_min = min(self.visual_start_idx, self.commit_cursor_idx)
                visual_max = max(self.visual_start_idx, self.commit_cursor_idx)
                if visual_min <= i <= visual_max:
                    is_selected = True
            
            # Format indicators
            cursor_indicator = ">" if i == self.commit_cursor_idx else " "
            selection_indicator = "[x]" if is_selected else "[ ]"
            note_indicator = "*" if commit['has_note'] else " "
            
            # Format relative time
            rel_time = self._format_relative_time(commit['time'])
            
            # Format: >[x]* SHA subject (author, time)
            # Keep it compact to fit in 40% width
            line = f"{cursor_indicator}{selection_indicator}{note_indicator} {commit['sha']} {commit['subject']}"
            
            # Add author and time on same line if space allows
            # Assuming 40% of 80 chars min = 32 chars available
            if len(line) < 25:  # Leave room for author/time
                author_time = f" ({commit['author'][:8]}, {rel_time})"
                # Truncate if needed
                available = 30 - len(line)
                if len(author_time) > available:
                    author_time = author_time[:available-3] + "..."
                line += author_time
            
            lines.append(line)
        
        # Add visual mode indicator if active
        if self.visual_mode:
            # Add at bottom if there's room
            if len(lines) < height - 2:
                lines.append("")
                lines.append("-- VISUAL --")
        
        return lines
    
    def handle_input(self, key: int) -> bool:
        """Handle input when commits pane is focused.
        
        Args:
            key: The key pressed
            
        Returns:
            True if selection changed (might need to update other panes)
        """
        if not self.commits:
            return False
        
        selection_changed = False
        
        # Navigation with Up/Down arrows
        if key == curses.KEY_UP:
            if self.commit_cursor_idx > 0:
                self.commit_cursor_idx -= 1
                
        elif key == curses.KEY_DOWN:
            if self.commit_cursor_idx < len(self.commits) - 1:
                self.commit_cursor_idx += 1
        
        # Selection operations
        elif key == ord(' '):  # Space - toggle selection at cursor
            if self.commit_cursor_idx in self.selected_commits:
                self.selected_commits.remove(self.commit_cursor_idx)
            else:
                self.selected_commits.add(self.commit_cursor_idx)
            selection_changed = True
            # Exit visual mode when using space
            self.visual_mode = False
            self.visual_start_idx = None
        
        elif key == ord('v'):  # Visual selection mode
            if not self.visual_mode:
                self.visual_mode = True
                self.visual_start_idx = self.commit_cursor_idx
            else:
                # Exit visual mode and confirm selection
                if self.visual_start_idx is not None:
                    visual_min = min(self.visual_start_idx, self.commit_cursor_idx)
                    visual_max = max(self.visual_start_idx, self.commit_cursor_idx)
                    for i in range(visual_min, visual_max + 1):
                        if i < len(self.commits):
                            self.selected_commits.add(i)
                    selection_changed = True
                self.visual_mode = False
                self.visual_start_idx = None
        
        elif key == ord('c'):  # Clear all selections
            if self.selected_commits:
                self.selected_commits.clear()
                selection_changed = True
            self.visual_mode = False
            self.visual_start_idx = None
        
        elif key == ord('a'):  # Select all visible commits
            for i in range(len(self.commits)):
                self.selected_commits.add(i)
            selection_changed = True
            self.visual_mode = False
            self.visual_start_idx = None
        
        elif key == 27:  # Escape - cancel visual mode
            self.visual_mode = False
            self.visual_start_idx = None
        
        return selection_changed
    
    def get_selected_shas(self) -> List[str]:
        """Get the full SHAs of selected commits.
        
        Returns:
            List of full commit SHAs that are selected
        """
        return [self.commits[i]['full_sha'] 
                for i in self.selected_commits 
                if i < len(self.commits)]
    
    def get_cursor_sha(self) -> Optional[str]:
        """Get the full SHA of the commit under cursor.
        
        Returns:
            Full commit SHA or None if no commits
        """
        if 0 <= self.commit_cursor_idx < len(self.commits):
            return self.commits[self.commit_cursor_idx]['full_sha']
        return None
    
    def _format_relative_time(self, commit_time: datetime) -> str:
        """Format commit time as relative to now.
        
        Args:
            commit_time: Datetime of the commit
            
        Returns:
            Formatted relative time string
        """
        now = datetime.now()
        diff = now - commit_time
        
        if diff < timedelta(minutes=1):
            return "now"
        elif diff < timedelta(hours=1):
            mins = int(diff.total_seconds() / 60)
            return f"{mins}m"
        elif diff < timedelta(days=1):
            hours = int(diff.total_seconds() / 3600)
            return f"{hours}h"
        elif diff < timedelta(days=7):
            return f"{diff.days}d"
        elif diff < timedelta(days=30):
            weeks = diff.days // 7
            return f"{weeks}w"
        elif diff < timedelta(days=365):
            months = diff.days // 30
            return f"{months}mo"
        else:
            years = diff.days // 365
            return f"{years}y"