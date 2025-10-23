"""Merger for architecture specifications."""

import re
from pathlib import Path
from typing import Dict, List


class ArchitectureMerger:
    """Merges architecture delta changes into main specification."""

    def __init__(self, main_spec_file: Path):
        """Initialize merger with main spec file.

        Args:
            main_spec_file: Path to the main specification file
        """
        self.main_spec_file = main_spec_file
        self.content = main_spec_file.read_text() if main_spec_file.exists() else ""

    def apply_changes(self, delta: Dict[str, List[Dict[str, str]]]) -> str:
        """Apply delta changes to main specification.

        Args:
            delta: Parsed delta from ArchitectureDeltaParser

        Returns:
            Updated specification content
        """
        content = self.content

        # Apply in order: RENAMED → REMOVED → MODIFIED → ADDED
        content = self._apply_renamed(content, delta.get("renamed", []))
        content = self._apply_removed(content, delta.get("removed", []))
        content = self._apply_modified(content, delta.get("modified", []))
        content = self._apply_added(content, delta.get("added", []))

        return content

    def _apply_renamed(self, content: str, renamed: List[Dict[str, str]]) -> str:
        """Apply RENAMED operations."""
        for item in renamed:
            old_name = item.get("old_name", "")
            new_name = item.get("new_name", "")

            if not old_name or not new_name:
                continue

            # Find and replace the component name
            pattern = rf"(###\s+Component:\s+){re.escape(old_name)}(\s|$)"
            replacement = rf"\g<1>{new_name}\g<2>"
            content = re.sub(pattern, replacement, content)

        return content

    def _apply_removed(self, content: str, removed: List[Dict[str, str]]) -> str:
        """Apply REMOVED operations."""
        for item in removed:
            component_name = item.get("name", "")
            if not component_name:
                continue

            # Find and remove the entire component block
            # Match from ### Component: to the next ### Component: or end of Components section
            pattern = rf"###\s+Component:\s+{re.escape(component_name)}.*?(?=###\s+Component:|##\s+(?!#)|$)"
            content = re.sub(pattern, "", content, flags=re.DOTALL)

        return content

    def _apply_modified(self, content: str, modified: List[Dict[str, str]]) -> str:
        """Apply MODIFIED operations."""
        for item in modified:
            component_name = item.get("name", "")
            new_content = item.get("content", "")

            if not component_name or not new_content:
                continue

            # Find and replace the entire component block
            pattern = rf"###\s+Component:\s+{re.escape(component_name)}.*?(?=###\s+Component:|##\s+(?!#)|$)"
            content = re.sub(pattern, new_content + "\n\n", content, flags=re.DOTALL)

        return content

    def _apply_added(self, content: str, added: List[Dict[str, str]]) -> str:
        """Apply ADDED operations."""
        if not added:
            return content

        # Find the Components section
        components_section_match = re.search(r"##\s+Components", content)
        if not components_section_match:
            # No Components section, add one
            content += "\n\n## Components\n\n"
            components_section_match = re.search(r"##\s+Components", content)

        # Find the end of Components section (next ## header or end of file)
        start_pos = components_section_match.end()
        next_section = re.search(r"\n##\s+(?!#)", content[start_pos:])

        if next_section:
            insert_pos = start_pos + next_section.start()
        else:
            insert_pos = len(content)

        # Insert all added components
        added_content = "\n\n".join(
            item.get("content", "") for item in added if item.get("content")
        )
        if added_content:
            content = (
                content[:insert_pos]
                + "\n\n"
                + added_content
                + "\n"
                + content[insert_pos:]
            )

        return content
