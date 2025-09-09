"""Commit view management for TUI."""

import curses
import subprocess
from typing import List, Tuple, Optional, Set, Dict
from datetime import datetime, timedelta
import re

from .selection import VisualSelectionMixin
from .scrollable import ScrollableMixin
from .indicators import SelectionIndicators
from .text_utils import word_wrap, display_width


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
        self.cursor_idx = 0  # Primary cursor index for scrollable mixin
        self.commit_scroll_offset = 0  # Legacy alias
        self.selected_commits: Set[int] = set()  # Legacy alias
        self.selected_items = self.selected_commits  # Point to same set for mixin
        self.commits_with_notes: Set[str] = set()  # Set of SHAs that have notes
        self.title_scroll_offset = 0  # Horizontal scroll for focused commit
        self.layout_manager = None  # Will be set by app
        
        # Load commits on initialization
        self.load_commits()
    
    @property
    def commit_cursor_idx(self):
        """Legacy property for backward compatibility."""
        return self.cursor_idx
    
    @commit_cursor_idx.setter
    def commit_cursor_idx(self, value):
        """Legacy setter for backward compatibility."""
        self.cursor_idx = value
    
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
                encoding="utf-8",
                errors="replace",  # Handle non-UTF8 gracefully
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
            self.cursor_idx = 0
            self.reset_scroll()  # Use scrollable mixin method
            self.commit_scroll_offset = 0  # Keep legacy alias in sync
            # Update items reference for mixin
            self.items = self.commits
            
        except subprocess.CalledProcessError as e:
            # Handle git errors gracefully
            self.commits = []
            self.items = self.commits
            # Could be: not a git repo, no commits, or other git issue
            # For debugging, we could log: e.stderr
    
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
        
        # Calculate commit heights with current width
        commit_heights = self._calculate_commit_heights(self.commits, width)
        
        # Get visible range using the scrollable mixin's method (now with minimal adjustment)
        visible_count, start_idx, end_idx = self.get_visible_range_variable(height, commit_heights)
        
        # Keep legacy scroll alias for callers that still read it
        self.commit_scroll_offset = self.scroll_offset
        
        # Build display lines
        for i in range(start_idx, end_idx):
            commit = self.commits[i]
            
            
            # Use unified prefix calculation
            prefix, datetime_indent, first_line_width, content_width = self._get_commit_prefix_and_widths(i, commit, width)
            
            # Wrap the commit title
            wrapped_title = self._word_wrap_commit_title(commit['subject'], max(first_line_width, content_width))
            
            if wrapped_title:
                # Try to fit first part of title on same line as author
                first_title_line = wrapped_title[0]
                
                # Check if we can fit at least some of the title on the first line
                if first_line_width >= 10:  # Reasonable minimum space for title
                    # Try to fit as much as possible on first line
                    if display_width(first_title_line) <= first_line_width:
                        # Full first line fits
                        lines.append(f"{prefix}{first_title_line}")
                        start_idx = 1
                    else:
                        # Split the first line to fit what we can
                        words = first_title_line.split()
                        line_words = []
                        line_length = 0
                        
                        for word in words:
                            word_width = display_width(word)
                            space_width = 1 if line_words else 0
                            if line_length + word_width + space_width <= first_line_width:
                                line_words.append(word)
                                line_length += word_width + space_width
                            else:
                                break
                        
                        if line_words:
                            # Put partial title on first line
                            lines.append(f"{prefix}{' '.join(line_words)}")
                            # Rewrap remaining text with rest of wrapped title
                            remaining_words = words[len(line_words):]
                            if remaining_words:
                                # Combine remaining words with rest of wrapped title
                                combined_text = ' '.join(remaining_words)
                                for idx in range(1, len(wrapped_title)):
                                    combined_text += ' ' + wrapped_title[idx]
                                wrapped_remaining = self._word_wrap_commit_title(combined_text, width - datetime_indent - 4)
                                for title_line in wrapped_remaining:
                                    lines.append(f"{' ' * datetime_indent}{title_line}")
                            else:
                                # First line partially fits, add rest of wrapped lines
                                for idx in range(1, len(wrapped_title)):
                                    lines.append(f"{' ' * datetime_indent}{wrapped_title[idx]}")
                        else:
                            # Can't fit any title words, put on next line
                            lines.append(prefix.rstrip())
                            lines.append(f"{' ' * datetime_indent}{first_title_line}")
                            # Add rest of wrapped lines
                            for idx in range(1, len(wrapped_title)):
                                lines.append(f"{' ' * datetime_indent}{wrapped_title[idx]}")
                else:
                    # Not enough space, put all title lines on next lines
                    lines.append(prefix.rstrip())
                    for title_line in wrapped_title:
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
    
    def handle_input(self, key: int, pane_height: int = 30) -> bool:
        """Handle input when commits pane is focused.
        
        Args:
            key: The key pressed
            pane_height: Height of the commits pane (optional, for future consistency)
            
        Returns:
            True if selection changed (might need to update other panes)
        """
        if not self.commits:
            return False
        
        selection_changed = False
        
        # Navigation with Up/Down arrows - just move cursor, scrolling handled by mixin
        if key == curses.KEY_UP:
            if self.cursor_idx > 0:
                self.cursor_idx -= 1
                selection_changed = True
                
        elif key == curses.KEY_DOWN:
            if self.cursor_idx < len(self.commits) - 1:
                self.cursor_idx += 1
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
        if 0 <= self.cursor_idx < len(self.commits):
            return self.commits[self.cursor_idx]['full_sha']
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
        return word_wrap(text, width)
    
    def _get_commit_prefix_and_widths(self, i: int, commit: Dict, width: int, is_cursor: bool = None) -> Tuple[str, int, int, int]:
        """Calculate prefix and widths for a commit - single source of truth.
        
        Args:
            i: Index of commit
            commit: Commit info dict
            width: Available width for display
            is_cursor: Override cursor check (None = auto-detect, True/False = force)
            
        Returns:
            Tuple of (prefix, datetime_indent, first_line_width, content_width)
        """
        # Format indicators
        is_selected = self.is_item_selected(i) if hasattr(self, 'is_item_selected') else False
        
        # Use override if provided, otherwise check actual cursor position
        if is_cursor is not None:
            has_cursor = is_cursor
        else:
            has_cursor = (i == self.cursor_idx)
        
        cursor_indicator = SelectionIndicators.format_cursor(has_cursor, style="arrow")
        selection_indicator = SelectionIndicators.format_selection_box(is_selected)
        note_indicator = "*" if commit.get('has_note') else " "
        
        # Build prefix
        datetime_str = self._format_local_datetime(commit['time'])
        prefix = f"{cursor_indicator}{selection_indicator}{note_indicator}{datetime_str} {commit['author']} "
        
        # visual indent for continuation lines (align with indicators area)
        datetime_indent = display_width(f"{cursor_indicator}{selection_indicator}{note_indicator}")
        # Compute widths using display width (Unicode-aware)
        first_line_width = max(0, width - display_width(prefix) - 4)  # borders/margins
        content_width = max(0, width - 6)  # continuation width
        
        return prefix, datetime_indent, first_line_width, content_width
    
    def _calculate_commit_heights(self, commits: List[Dict], width: int) -> List[int]:
        """Calculate height needed for each commit with word wrapping.
        
        Args:
            commits: List of commit info dicts
            width: Available width for display
        
        Returns:
            List of heights for each commit
        """
        heights = []
        
        for i in range(len(commits)):
            commit = commits[i]
            # Start with basic indicators and datetime line
            height = 1
            
            # Use unified prefix calculation - use actual cursor state for accurate height
            # This ensures height calculation matches rendering exactly
            prefix, datetime_indent, first_line_width, content_width = self._get_commit_prefix_and_widths(i, commit, width)
            
            # Wrap the commit title
            wrapped_title = self._word_wrap_commit_title(commit['subject'], max(first_line_width, content_width))
            
            if wrapped_title:
                # Check if first part fits on same line as author
                first_title_line = wrapped_title[0]
                
                if first_line_width >= 10:  # Reasonable minimum space for title
                    if display_width(first_title_line) <= first_line_width:
                        # Full first line fits on same line as prefix
                        pass  # height stays 1
                    else:
                        # Need to split or move to next line - add extra lines
                        words = first_title_line.split()
                        line_words = []
                        line_length = 0
                        
                        for word in words:
                            word_width = display_width(word)
                            space_width = 1 if line_words else 0
                            if line_length + word_width + space_width <= first_line_width:
                                line_words.append(word)
                                line_length += word_width + space_width
                            else:
                                break
                        
                        if not line_words:
                            # Can't fit any title words, put on next line
                            height += 1
                        # else: partial title fits on first line
                        
                        # Add remaining wrapped lines
                        remaining_words = words[len(line_words):] if line_words else words
                        if remaining_words:
                            # Need to account for the rest of the original wrapped title
                            # Combine remaining words from first line with rest of wrapped title
                            combined_text = ' '.join(remaining_words)
                            for idx in range(1, len(wrapped_title)):
                                combined_text += ' ' + wrapped_title[idx]
                            wrapped_remaining = self._word_wrap_commit_title(combined_text, content_width)
                            height += len(wrapped_remaining)
                        else:
                            # First line partially fits, add rest of wrapped lines
                            if len(wrapped_title) > 1:
                                height += len(wrapped_title) - 1
                else:
                    # Not enough space, put all title lines on next lines
                    height += len(wrapped_title)
            
            heights.append(height)
        
        return heights
    
    
    def _visible_commit_items(self, height: int) -> int:
        """Calculate how many commit items can fit in the given height.
        
        This is a simplified version that estimates based on average item height.
        Similar to MessageView's _visible_message_items.
        
        Args:
            height: Screen height
            
        Returns:
            Number of commit items that can be displayed
        """
        # Rows available for content between borders
        rows = max(0, height - 2)
        
        # Reserve rows for any status footer we append
        if self.visual_mode:
            rows = max(0, rows - 2)  # One blank + "-- VISUAL --"
        
        # Estimate based on average lines per commit
        # Most commits take 1 line, some wrap to 2-8 lines
        AVERAGE_LINES_PER_COMMIT = 2
        return max(1, rows // AVERAGE_LINES_PER_COMMIT)