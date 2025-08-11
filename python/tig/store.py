"""Core storage implementation for Tig objects."""

import hashlib
import subprocess
from pathlib import Path
from typing import List, Optional


class TigStore:
    """Store and retrieve text objects in Git repositories."""
    
    def __init__(self, repo_path: Optional[Path] = None):
        """Initialize TigStore.
        
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
    
    def store(self, content: str, object_id: Optional[str] = None) -> str:
        """Store text content as a Git object.
        
        Args:
            content: Text content to store.
            object_id: Optional ID for the object. Generated from content hash if not provided.
            
        Returns:
            The object ID used to store the content.
        """
        # Generate object ID from content hash if not provided
        if object_id is None:
            object_id = hashlib.sha1(content.encode('utf-8')).hexdigest()
        
        # Store content as blob
        process = subprocess.Popen(
            ["git", "hash-object", "-w", "--stdin"],
            cwd=self.repo_path,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        stdout, stderr = process.communicate(input=content)
        if process.returncode != 0:
            raise subprocess.CalledProcessError(process.returncode, "git hash-object", stderr)
        blob_sha = stdout.strip()
        
        # Create ref
        ref_name = f"refs/tig/{object_id}"
        self._run_git(["update-ref", ref_name, blob_sha])
        
        return object_id
    
    def retrieve(self, object_id: str) -> str:
        """Retrieve content by object ID.
        
        Args:
            object_id: The ID of the object to retrieve.
            
        Returns:
            The content of the object.
            
        Raises:
            KeyError: If object_id doesn't exist.
        """
        ref_name = f"refs/tig/{object_id}"
        
        # Get blob SHA from ref
        try:
            result = self._run_git(["rev-parse", ref_name])
            blob_sha = result.stdout.strip()
        except subprocess.CalledProcessError:
            raise KeyError(f"Object not found: {object_id}")
        
        # Get content
        result = self._run_git(["cat-file", "blob", blob_sha])
        return result.stdout
    
    def list(self) -> List[str]:
        """List all object IDs.
        
        Returns:
            List of object IDs.
        """
        result = self._run_git(["for-each-ref", "--format=%(refname:short)", "refs/tig"])
        if not result.stdout.strip():
            return []
        
        refs = result.stdout.strip().split("\n")
        # Extract object IDs from refs (remove "tig/" prefix)
        return [ref.split("/", 1)[1] for ref in refs]
    
    def delete(self, object_id: str) -> None:
        """Delete an object by removing its ref.
        
        The blob will be garbage collected later by Git.
        
        Args:
            object_id: The ID of the object to delete.
            
        Raises:
            KeyError: If object_id doesn't exist.
        """
        ref_name = f"refs/tig/{object_id}"
        
        # First check if the ref exists
        try:
            self._run_git(["rev-parse", "--verify", ref_name])
        except subprocess.CalledProcessError:
            raise KeyError(f"Object not found: {object_id}")
        
        # Delete the ref
        self._run_git(["update-ref", "-d", ref_name])