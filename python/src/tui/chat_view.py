"""Chat view for showing chat messages associated with commits."""

from typing import List
from .text_utils import word_wrap


class ChatView:
    """Displays chat messages associated with a commit."""
    
    def __init__(self, store):
        """Initialize chat view.
        
        Args:
            store: TigsStore instance for Git operations
        """
        self.store = store
        self.current_sha = None
        self.chat_lines = []
    
    def load_chat(self, sha: str) -> None:
        """Load chat content for a commit.
        
        Args:
            sha: Full SHA of the commit
        """
        if sha == self.current_sha:
            return
        
        self.current_sha = sha
        self.chat_lines = []
        
        try:
            # Try to get chat content
            content = self.store.show_chat(sha)
            if content:
                # Split content into lines
                self.chat_lines = content.split('\n')
            else:
                self.chat_lines = ["(No chat for this commit)"]
        except KeyError:
            # No chat found for this commit
            self.chat_lines = ["(No chat for this commit)"]
        except Exception as e:
            self.chat_lines = [f"Error loading chat: {str(e)}"]
    
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
        
        if not self.chat_lines:
            return ["Loading..."]
        
        # Format lines to fit width
        formatted = []
        for line in self.chat_lines:
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