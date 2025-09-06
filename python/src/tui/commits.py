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
        self.title_scroll_offset = 0  # Horizontal scroll for focused commit
        self.layout_manager = None  # Will be set by app
        
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
                        'subject': subject,  # Keep full subject for horizontal scrolling
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
    
    def get_display_lines(self, height: int, width: int = 32) -> List[str]:
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
            
            # Format single line: indicators + datetime + author + title start
            datetime_str = self._format_local_datetime(commit['time'])
            prefix = f"{cursor_indicator}{selection_indicator}{note_indicator}{datetime_str} {commit['author']} "
            
            # Calculate indentation for wrapped lines to align with datetime
            datetime_indent = len(f"{cursor_indicator}{selection_indicator}{note_indicator}")  # Space to align with datetime
            
            # Calculate available width for title on same line and continuation lines
            first_line_width = width - len(prefix) - 4  # Account for borders
            content_width = width - 6  # Width for continuation lines with indentation
            
            # Wrap the commit title
            wrapped_title = self._word_wrap_commit_title(commit['subject'], max(first_line_width, content_width))
            
            if wrapped_title:
                # Try to fit first part of title on same line as author
                first_title_line = wrapped_title[0]
                
                # Check if we can fit at least some of the title on the first line
                if first_line_width >= 10:  # Reasonable minimum space for title
                    # Try to fit as much as possible on first line
                    if len(first_title_line) <= first_line_width:
                        # Full first line fits
                        lines.append(f"{prefix}{first_title_line}")
                        start_idx = 1
                    else:
                        # Split the first line to fit what we can
                        words = first_title_line.split()
                        line_words = []
                        line_length = 0
                        
                        for word in words:
                            if line_length + len(word) + len(line_words) <= first_line_width:
                                line_words.append(word)
                                line_length += len(word)
                            else:
                                break
                        
                        if line_words:
                            # Put partial title on first line
                            lines.append(f"{prefix}{' '.join(line_words)}")
                            # Rewrap remaining text
                            remaining_words = words[len(line_words):]
                            if remaining_words:
                                remaining_text = ' '.join(remaining_words)
                                wrapped_remaining = self._word_wrap_commit_title(remaining_text, width - datetime_indent - 4)
                                for title_line in wrapped_remaining:
                                    lines.append(f"{' ' * datetime_indent}{title_line}")
                        else:
                            # Can't fit any title words, put on next line
                            lines.append(prefix.rstrip())
                            lines.append(f"{' ' * datetime_indent}{first_title_line}")
                        start_idx = 1
                else:
                    # Not enough space, put title on next line
                    lines.append(prefix.rstrip())
                    lines.append(f"{' ' * datetime_indent}{first_title_line}")
                    start_idx = 1
                
                # Add remaining wrapped lines
                for title_line in wrapped_title[start_idx:]:
                    lines.append(f"{' ' * datetime_indent}{title_line}")
            else:
                # No title
                lines.append(prefix.rstrip())
        
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
                selection_changed = True
                
        elif key == curses.KEY_DOWN:
            if self.commit_cursor_idx < len(self.commits) - 1:
                self.commit_cursor_idx += 1
                self.cursor_idx = self.commit_cursor_idx  # Keep mixin alias in sync
                selection_changed = True
        
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
    
    def _format_local_datetime(self, commit_time: datetime) -> str:
        """Format commit time as full local datetime without timezone.
        
        Args:
            commit_time: Datetime of the commit
            
        Returns:
            Formatted local datetime string
        """
        # Full local datetime without seconds: "2024-12-15 14:30"
        return commit_time.strftime("%Y-%m-%d %H:%M")
    
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
    
    def _word_wrap_commit_title(self, text: str, width: int) -> List[str]:
        """Word wrap commit title to specified width.
        
        Args:
            text: Commit title to wrap
            width: Maximum width per line
            
        Returns:
            List of wrapped lines
        """
        if not text or width <= 0:
            return [text]
        
        if len(text) <= width:
            return [text]
        
        words = text.split()
        if not words:
            return [text]
        
        lines = []
        current_line = []
        current_length = 0
        
        for word in words:
            word_length = len(word)
            
            # Check if adding this word would exceed width
            if current_line and current_length + word_length + len(current_line) > width:
                lines.append(' '.join(current_line))
                current_line = [word]
                current_length = word_length
            else:
                current_line.append(word)
                current_length += word_length
        
        if current_line:
            lines.append(' '.join(current_line))
        
        return lines if lines else [text[:width]]