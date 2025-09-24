"""Chat view for showing formatted chat messages associated with commits."""

import curses
from typing import List, Union, Tuple
from cligent import ChatParser
from .messages_view import MessageView


class ChatView:
    """Displays formatted chat messages associated with a commit using MessageView."""

    def __init__(self, store):
        """Initialize chat view.

        Args:
            store: TigsRepo instance for Git operations
        """
        self.store = store
        self.current_sha = None

        # Initialize chat parser
        try:
            self.chat_parser = ChatParser("claude-code")
        except Exception:
            # Handle cligent initialization errors gracefully
            self.chat_parser = None

        # Initialize message view for display
        self.message_view = MessageView(self.chat_parser)
        self.message_view.read_only = True  # Make it read-only for view mode

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
            if content and self.chat_parser:
                # Parse the YAML content using cligent with a temporary log ID
                try:
                    # Create a temporary directory and file that cligent can work with
                    import tempfile
                    import os

                    # Create temp directory structure that cligent expects
                    with tempfile.TemporaryDirectory() as temp_dir:
                        # Write the chat content to a temporary log file
                        log_file = os.path.join(temp_dir, f"{sha}.yaml")
                        with open(log_file, "w") as f:
                            f.write(content)

                        # Create a temporary cligent config that points to this directory
                        # Use a different instance to avoid interfering with the main one
                        temp_parser = ChatParser("claude-code")

                        # Parse the file directly using parse_file method
                        chat = temp_parser.parse_file(log_file)

                        # Extract messages and load them into message view
                        self.message_view.messages = []
                        for msg in chat.messages:
                            # Handle cligent Role enum or string exactly like in messages_view.py
                            if hasattr(msg, "role"):
                                role = msg.role
                                # Convert Role enum to string if needed
                                if hasattr(role, "value"):
                                    role = role.value
                                elif hasattr(role, "USER"):  # Check for Role enum
                                    from cligent import Role

                                    if role == Role.USER:
                                        role = "user"
                                    elif role == Role.ASSISTANT:
                                        role = "assistant"
                                    else:
                                        role = str(role).lower()
                                else:
                                    role = str(role).lower()
                            else:
                                role = "unknown"

                            content_text = (
                                msg.content if hasattr(msg, "content") else str(msg)
                            )
                            timestamp = (
                                msg.timestamp if hasattr(msg, "timestamp") else None
                            )
                            self.message_view.messages.append(
                                (role, content_text, timestamp)
                            )

                        # Update items reference and reset cursor
                        self.message_view.items = self.message_view.messages
                        self.message_view.cursor_idx = 0
                        self.message_view.message_cursor_idx = 0
                        self.message_view._internal_scroll_offset = 0
                        self.message_view._needs_message_view_init = True

                except Exception as e:
                    # If parsing fails, fall back to raw content display
                    # Create a debug message to show the error
                    self.message_view.messages = [
                        (
                            "system",
                            f"PARSING ERROR: {str(e)}\n\nRAW CONTENT:\n{content}",
                            None,
                        )
                    ]
                    self.message_view.items = self.message_view.messages
                    self.message_view.cursor_idx = 0
                    self.message_view.message_cursor_idx = 0
                    self.message_view._internal_scroll_offset = 0
                    self.message_view._needs_message_view_init = True
            else:
                # No content or no parser - show empty
                self.message_view.messages = []
                self.message_view.items = []

        except KeyError:
            # No chat found for this commit
            self.message_view.messages = []
            self.message_view.items = []
        except Exception as e:
            # Error loading chat - show debug info
            self.message_view.messages = [("system", f"LOADING ERROR: {str(e)}", None)]
            self.message_view.items = self.message_view.messages
            self.message_view.cursor_idx = 0
            self.message_view.message_cursor_idx = 0
            self.message_view._internal_scroll_offset = 0
            self.message_view._needs_message_view_init = True

    def _show_raw_content(self, content: str) -> None:
        """Fallback to show raw content if parsing fails."""
        # Create a single "raw" message to display the content
        self.message_view.messages = [("system", content, None)]
        self.message_view.items = self.message_view.messages
        self.message_view.cursor_idx = 0
        self.message_view.message_cursor_idx = 0
        self.message_view._internal_scroll_offset = 0
        self.message_view._needs_message_view_init = True

    def handle_input(self, key: int, pane_height: int) -> bool:
        """Handle keyboard input for scrolling.

        Args:
            key: Key code
            pane_height: Height of the pane

        Returns:
            True if handled, False otherwise
        """
        if not self.message_view.messages:
            return False

        # Handle up/down navigation (read-only, no selection)
        if key == curses.KEY_UP:
            self.message_view.handle_input(None, key, pane_height)
            return True
        elif key == curses.KEY_DOWN:
            self.message_view.handle_input(None, key, pane_height)
            return True
        return False

    def get_display_lines(
        self, height: int, width: int, colors_enabled: bool = False
    ) -> List[Union[str, List[Tuple[str, int]]]]:
        """Get display lines for the chat pane.

        Args:
            height: Available height for content
            width: Available width for content
            colors_enabled: Whether to return colored output

        Returns:
            List of formatted message lines
        """
        if not self.current_sha:
            if colors_enabled:
                from .color_constants import COLOR_DEFAULT

                return [[("No commit selected", COLOR_DEFAULT)]]
            return ["No commit selected"]

        if not self.message_view.messages:
            if colors_enabled:
                from .color_constants import COLOR_DEFAULT

                return [[("(No chat for this commit)", COLOR_DEFAULT)]]
            return ["(No chat for this commit)"]

        # Use the message view's display logic with gradual scrolling
        return self.message_view.get_display_lines(height, width, colors_enabled)
