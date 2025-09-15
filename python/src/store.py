"""Core storage implementation for Tigs chats using Git notes."""

import subprocess
from pathlib import Path
from typing import List, Optional


class TigsStore:
    """Store and retrieve chat content using Git notes."""

    def __init__(self, repo_path: Optional[Path] = None):
        """Initialize TigsStore.

        Args:
            repo_path: Path to Git repository. Defaults to current directory.
        """
        self.repo_path = Path(repo_path) if repo_path else Path.cwd()
        self._verify_git_repo()

    def _verify_git_repo(self) -> None:
        """Verify that we're in a Git repository."""
        result = subprocess.run(
            ["git", "rev-parse", "--git-dir"],
            cwd=self.repo_path,
            capture_output=True,
            text=True
        )
        if result.returncode != 0:
            raise ValueError(f"Not a Git repository: {self.repo_path}")

    def _run_git(self, args: List[str]) -> subprocess.CompletedProcess:
        """Run a Git command and return the result."""
        return subprocess.run(
            ["git"] + args,
            cwd=self.repo_path,
            capture_output=True,
            text=True,
            check=True
        )

    def add_chat(self, commit_sha: str, content: str) -> str:
        """Add chat content to a commit using Git notes.

        Args:
            commit_sha: The commit SHA to attach the chat to.
            content: Chat content to store.

        Returns:
            The resolved commit SHA.
        """
        # Resolve commit SHA (handles HEAD, branch names, etc.)
        try:
            resolved_sha = self._run_git(["rev-parse", commit_sha]).stdout.strip()
        except subprocess.CalledProcessError:
            raise ValueError(f"Invalid commit: {commit_sha}")

        # Add note using Git notes
        try:
            self._run_git(["notes", "--ref=refs/notes/chats", "add", "-m", content, resolved_sha])
            return resolved_sha
        except subprocess.CalledProcessError as e:
            # Check both stdout and stderr for the "existing notes" message
            error_output = (e.stderr or "") + (e.stdout or "")
            if "found existing notes" in error_output.lower() or "already has a note" in error_output.lower():
                raise ValueError(f"Commit {resolved_sha} already has a chat")
            else:
                raise ValueError(f"Failed to add chat: {error_output.strip()}")

    def show_chat(self, commit_sha: str) -> str:
        """Retrieve chat content for a commit.

        Args:
            commit_sha: The commit SHA to get the chat for.

        Returns:
            The chat content.

        Raises:
            KeyError: If commit doesn't have a chat.
        """
        # Resolve commit SHA
        try:
            resolved_sha = self._run_git(["rev-parse", commit_sha]).stdout.strip()
        except subprocess.CalledProcessError:
            raise ValueError(f"Invalid commit: {commit_sha}")

        # Get note content
        try:
            result = self._run_git(["notes", "--ref=refs/notes/chats", "show", resolved_sha])
            # Git notes adds exactly one trailing newline, remove only that one
            if result.stdout.endswith('\n'):
                return result.stdout[:-1]
            return result.stdout
        except subprocess.CalledProcessError:
            raise KeyError(f"No chat found for commit: {resolved_sha}")

    def list_chats(self) -> List[str]:
        """List all commits that have chats.

        Returns:
            List of commit SHAs that have chats attached.
        """
        try:
            result = self._run_git(["notes", "--ref=refs/notes/chats", "list"])
            if not result.stdout.strip():
                return []
            
            # Parse output: each line is "note_blob_sha commit_sha"
            lines = result.stdout.strip().split("\n")
            return [line.split()[1] for line in lines if line.strip()]
        except subprocess.CalledProcessError:
            return []

    def remove_chat(self, commit_sha: str) -> None:
        """Remove chat from a commit.

        Args:
            commit_sha: The commit SHA to remove the chat from.

        Raises:
            KeyError: If commit doesn't have a chat.
        """
        # Resolve commit SHA
        try:
            resolved_sha = self._run_git(["rev-parse", commit_sha]).stdout.strip()
        except subprocess.CalledProcessError:
            raise ValueError(f"Invalid commit: {commit_sha}")

        # Remove the note
        try:
            self._run_git(["notes", "--ref=refs/notes/chats", "remove", resolved_sha])
        except subprocess.CalledProcessError:
            raise KeyError(f"No chat found for commit: {resolved_sha}")

    def get_current_commit(self) -> str:
        """Get the current HEAD commit SHA.

        Returns:
            Current HEAD commit SHA.
        """
        try:
            return self._run_git(["rev-parse", "HEAD"]).stdout.strip()
        except subprocess.CalledProcessError:
            raise ValueError("No commits in repository")

    def get_unpushed_commits_with_chats(self, remote: str = "origin") -> List[str]:
        """Get list of commits that have chats but are not pushed to remote.

        Args:
            remote: Remote name to check against.

        Returns:
            List of unpushed commit SHAs that have chats.
        """
        try:
            # Get all commits with chats
            commits_with_chats = self.list_chats()
            if not commits_with_chats:
                return []

            # Get all commits on remote branches
            remote_refs_result = self._run_git(["ls-remote", "--heads", remote])
            remote_shas = set()
            for line in remote_refs_result.stdout.strip().split("\n"):
                if line:
                    sha = line.split()[0]
                    # Get all commits reachable from this remote ref
                    try:
                        ancestors_result = self._run_git(["rev-list", sha])
                        remote_shas.update(ancestors_result.stdout.strip().split("\n"))
                    except subprocess.CalledProcessError:
                        # Remote ref might not be fetched locally
                        pass

            # Find commits with chats that are not on remote
            unpushed = []
            for commit_sha in commits_with_chats:
                if commit_sha not in remote_shas:
                    # Verify the commit exists locally
                    try:
                        self._run_git(["cat-file", "-e", commit_sha])
                        unpushed.append(commit_sha)
                    except subprocess.CalledProcessError:
                        # Commit doesn't exist locally (orphaned note)
                        pass

            return unpushed
        except subprocess.CalledProcessError:
            return []

    def push_chats(self, remote: str = "origin", force: bool = False) -> None:
        """Push chat notes to remote repository.

        Args:
            remote: Remote name to push to.
            force: Force push even if there are unpushed commits.

        Raises:
            ValueError: If there are unpushed commits with chats and force is False.
        """
        if not force:
            unpushed = self.get_unpushed_commits_with_chats(remote)
            if unpushed:
                raise ValueError(
                    f"Cannot push chats: {len(unpushed)} commit(s) with chats are not pushed to '{remote}'.\n"
                    f"Unpushed commits:\n" + "\n".join(f"  - {sha[:8]}" for sha in unpushed) + "\n\n"
                    f"To fix this:\n"
                    f"  1. Push your commits first: git push {remote} <branch>\n"
                    f"  2. Then push the chats: tigs push\n\n"
                    f"Or use --force to push chats anyway (not recommended)"
                )

        self._run_git(["push", remote, "refs/notes/chats:refs/notes/chats"])

    # Legacy methods for backward compatibility (will be removed)
    def store(self, content: str, object_id: Optional[str] = None) -> str:
        """Legacy method - use add_chat instead."""
        commit_sha = object_id if object_id else self.get_current_commit()
        return self.add_chat(commit_sha, content)

    def retrieve(self, object_id: str) -> str:
        """Legacy method - use show_chat instead."""
        return self.show_chat(object_id)

    def list(self) -> List[str]:
        """Legacy method - use list_chats instead."""
        return self.list_chats()

    def delete(self, object_id: str) -> None:
        """Legacy method - use remove_chat instead."""
        self.remove_chat(object_id)