"""Chat view for showing chat messages associated with commits."""

import curses
from typing import List
from .text_utils import word_wrap
from .view_scroll_mixin import ViewScrollMixin


class ChatView(ViewScrollMixin):
    """Displays chat messages associated with a commit."""
    
    def __init__(self, store):
        """Initialize chat view.
        
        Args:
            store: TigsStore instance for Git operations
        """
        ViewScrollMixin.__init__(self)
        self.store = store
        self.current_sha = None
    
    def load_chat(self, sha: str) -> None:
        """Load chat content for a commit.
        
        Args:
            sha: Full SHA of the commit
        """
        if sha == self.current_sha:
            return
        
        self.current_sha = sha
        
        try:
            # Try to get chat content
            content = self.store.show_chat(sha)
            if content:
                # Store ALL lines without truncation
                self.total_lines = content.split('\n')
            else:
                self.total_lines = ["(No chat for this commit)"]
        except KeyError:
            # No chat found for this commit
            self.total_lines = ["(No chat for this commit)"]
        except Exception as e:
            self.total_lines = [f"Error loading chat: {str(e)}"]
        
        # Reset view to top when loading new content
        self.reset_view()
    
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
        """Get display lines for the chat pane.
        
        Args:
            height: Available height for content
            width: Available width for content
            
        Returns:
            List of formatted chat lines
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