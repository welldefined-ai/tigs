"""Commit view management for TUI."""

import curses
import subprocess
from typing import List, Tuple, Optional, Set, Dict
from datetime import datetime, timedelta
import re

from .selection import VisualSelectionMixin
from .scrollable import ScrollableMixin
from .indicators import SelectionIndicators


class CommitView(VisualSelectionMixin, ScrollableMixin):
    """Manages commit display and interaction."""
    
    def __init__(self, store):
        """Initialize commit view.
        
        Args:
            store: TigsStore instance for Git operations
        """
        VisualSelectionMixin.__init__(self)  # Initialize selection mixin
        ScrollableMixin.__init__(self)  # Initialize scrollable mixin
        self.store = store
        self.commits: List[Dict] = []  # List of commit info dicts
        self.items = self.commits  # Alias for mixin compatibility
        self.commit_cursor_idx = 0
        self.cursor_idx = 0  # Alias for mixin compatibility
        self.commit_scroll_offset = 0  # Legacy alias
        self.selected_commits: Set[int] = set()  # Legacy alias
        self.selected_items = self.selected_commits  # Point to same set for mixin
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
            self.cursor_idx = 0  # Keep mixin alias in sync
            self.reset_scroll()  # Use scrollable mixin method
            self.commit_scroll_offset = 0  # Keep legacy alias in sync
            # Update items reference for mixin
            self.items = self.commits
            
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
        
        # Use scrollable mixin to get visible range
        visible_count, start_idx, end_idx = self.get_visible_range(height)
        self.commit_scroll_offset = self.scroll_offset  # Keep legacy alias in sync
        
        # Build display lines
        for i in range(start_idx, end_idx):
            commit = self.commits[i]
            
            # Check if selected using mixin method
            is_selected = self.is_item_selected(i)
            
            # Format indicators using the indicators module
            cursor_indicator = SelectionIndicators.format_cursor(
                i == self.commit_cursor_idx, style="arrow"
            )
            selection_indicator = SelectionIndicators.format_selection_box(is_selected)
            note_indicator = "*" if commit['has_note'] else " "
            
            # Format relative time
            rel_time = self._format_relative_time(commit['time'])
            
            # Format: >[x]* SHA subject
            # Must fit in ~28 chars (32 width - 4 for borders)
            prefix = f"{cursor_indicator}{selection_indicator}{note_indicator} {commit['sha']} "
            # prefix is ">[x]* 1234567 " = 14 chars, leaving 14 for subject
            max_subject_len = 28 - len(prefix)
            truncated_subject = commit['subject'][:max_subject_len]
            
            line = f"{prefix}{truncated_subject}"
            lines.append(line)
        
        # Add visual mode indicator if active
        if self.visual_mode:
            # Add at bottom if there's room
            if len(lines) < height - 2:
                lines.append("")
                lines.append(SelectionIndicators.VISUAL_MODE)
        
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
                self.cursor_idx = self.commit_cursor_idx  # Keep mixin alias in sync
                
        elif key == curses.KEY_DOWN:
            if self.commit_cursor_idx < len(self.commits) - 1:
                self.commit_cursor_idx += 1
                self.cursor_idx = self.commit_cursor_idx  # Keep mixin alias in sync
        
        # Delegate selection operations to mixin
        else:
            selection_changed = self.handle_selection_input(key)
        
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