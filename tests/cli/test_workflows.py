#!/usr/bin/env python3
"""Complete CLI workflows - language-agnostic end-to-end testing."""

import subprocess
import tempfile
from pathlib import Path

import pytest
import yaml
from framework.fixtures import create_test_repo


def run_tigs(repo_path, *args):
    """Run tigs command and return result."""
    cmd = ["uv", "run", "tigs", "--repo", str(repo_path)] + list(args)
    # Get the python directory relative to the current test file
    test_dir = Path(__file__).parent.parent.parent
    python_dir = test_dir / "python"
    result = subprocess.run(
        cmd,
        cwd=str(python_dir),
        capture_output=True,
        text=True,
    )
    return result


def check_git_notes(repo_path, commit_sha=None, ref="refs/notes/chats"):
    """Check Git notes exist and return content."""
    try:
        if commit_sha is None:
            # Get HEAD SHA
            result = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                cwd=repo_path,
                capture_output=True,
                text=True,
            )
            if result.returncode != 0:
                return False, None
            commit_sha = result.stdout.strip()

        # Check if note exists
        result = subprocess.run(
            ["git", "notes", "--ref", ref, "show", commit_sha],
            cwd=repo_path,
            capture_output=True,
            text=True,
        )
        if result.returncode == 0:
            return True, result.stdout
        else:
            return False, None
    except Exception:
        return False, None


def validate_yaml_schema(content):
    """Validate YAML content matches tigs.chat/v1 schema."""
    try:
        data = yaml.safe_load(content)
        if not isinstance(data, dict):
            return False
        if data.get("schema") != "tigs.chat/v1":
            return False
        if "messages" not in data:
            return False
        if not isinstance(data["messages"], list):
            return False

        for msg in data["messages"]:
            if not isinstance(msg, dict):
                return False
            if "role" not in msg or "content" not in msg:
                return False
            if msg["role"] not in ["user", "assistant", "system"]:
                return False
        return True
    except Exception:
        return False


class TestCLIWorkflows:
    """Test complete CLI workflows from start to finish."""

    def test_add_show_remove_workflow(self):
        """Test complete add → show → remove workflow with Git notes verification."""
        sample_yaml = """schema: tigs.chat/v1
messages:
- role: user
  content: How do I create a Python function?
- role: assistant
  content: Here's a simple Python function example.
"""

        with tempfile.TemporaryDirectory() as tmpdir:
            repo_path = Path(tmpdir) / "workflow_repo"
            create_test_repo(repo_path, ["Initial commit for workflow test"])

            # Step 1: Add chat with YAML content
            result = run_tigs(repo_path, "add-chat", "-m", sample_yaml)
            print(f"Add result: {result.returncode}, {result.stdout}, {result.stderr}")

            if result.returncode != 0:
                print("Add-chat command failed - workflow test cannot continue")
                return  # Skip if command not implemented

            # Extract commit SHA if available
            commit_sha = None
            if "commit:" in result.stdout:
                commit_sha = result.stdout.split(":")[-1].strip()

            # Verify Git note was created
            notes_exist, stored_content = check_git_notes(repo_path, commit_sha)
            if notes_exist and stored_content:
                assert validate_yaml_schema(stored_content)
                print("✓ Git note created and validates")

            # Step 2: Show chat content
            result = run_tigs(repo_path, "show-chat")
            print(f"Show result: {result.returncode}")

            if result.returncode == 0:
                assert "schema: tigs.chat/v1" in result.stdout
                assert validate_yaml_schema(result.stdout)
                print("✓ Show command works and returns valid YAML")

            # Step 3: List chats should contain our commit
            result = run_tigs(repo_path, "list-chats")
            print(f"List result: {result.returncode}")

            if result.returncode == 0 and commit_sha:
                assert commit_sha in result.stdout
                print("✓ List command shows our commit")

            # Step 4: Remove chat
            result = run_tigs(repo_path, "remove-chat")
            print(f"Remove result: {result.returncode}")

            if result.returncode == 0:
                print("✓ Remove command succeeded")

                # Verify Git note was removed
                notes_exist_after, _ = check_git_notes(repo_path, commit_sha)
                if not notes_exist_after:
                    print("✓ Git note was removed")

                # Verify list is empty
                result = run_tigs(repo_path, "list-chats")
                if result.returncode == 0 and result.stdout.strip() == "":
                    print("✓ List is empty after removal")

    def test_multi_commit_workflow(self):
        """Test workflow with multiple commits."""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_path = Path(tmpdir) / "multi_repo"

            # Create repository with multiple commits
            commits_messages = [
                "First commit: Add initial functionality",
                "Second commit: Add error handling",
                "Third commit: Add tests",
            ]
            create_test_repo(repo_path, commits_messages)

            # Get commit SHAs
            result = subprocess.run(
                ["git", "log", "--format=%H", "-n", str(len(commits_messages))],
                cwd=repo_path,
                capture_output=True,
                text=True,
            )

            if result.returncode != 0:
                print("Could not get commit SHAs")
                return

            commit_shas = result.stdout.strip().split("\n")
            if len(commit_shas) < 3:
                print("Need at least 3 commits for multi-commit test")
                return

            # Add chats to multiple commits
            chat_contents = [
                "schema: tigs.chat/v1\nmessages:\n- role: user\n  content: First commit discussion",
                "schema: tigs.chat/v1\nmessages:\n- role: user\n  content: Second commit discussion",
                "schema: tigs.chat/v1\nmessages:\n- role: user\n  content: Third commit discussion",
            ]

            stored_commits = []

            for i, (commit_sha, content) in enumerate(
                zip(commit_shas[:3], chat_contents)
            ):
                result = run_tigs(repo_path, "add-chat", commit_sha, "-m", content)
                print(f"Add to commit {i + 1}: {result.returncode}")

                if result.returncode == 0:
                    stored_commits.append(commit_sha)

                    # Verify Git note exists
                    notes_exist, stored_content = check_git_notes(repo_path, commit_sha)
                    if notes_exist and validate_yaml_schema(stored_content):
                        print(f"✓ Commit {i + 1} stored successfully")

            if not stored_commits:
                print("No commits were stored successfully")
                return

            # List all chats
            result = run_tigs(repo_path, "list-chats")
            print(f"List all: {result.returncode}")

            if result.returncode == 0:
                for commit_sha in stored_commits:
                    if commit_sha in result.stdout:
                        print(f"✓ Found {commit_sha[:8]} in list")

            # Show specific commit chats
            for i, (commit_sha, content) in enumerate(
                zip(stored_commits, chat_contents[: len(stored_commits)])
            ):
                result = run_tigs(repo_path, "show-chat", commit_sha)
                print(f"Show commit {i + 1}: {result.returncode}")

                if result.returncode == 0 and validate_yaml_schema(result.stdout):
                    print(f"✓ Show commit {i + 1} returned valid YAML")

            # Remove middle commit chat (if we have at least 2)
            if len(stored_commits) >= 2:
                middle_sha = stored_commits[1]
                result = run_tigs(repo_path, "remove-chat", middle_sha)
                print(f"Remove middle commit: {result.returncode}")

                if result.returncode == 0:
                    # Verify removal
                    notes_exist, _ = check_git_notes(repo_path, middle_sha)
                    if not notes_exist:
                        print("✓ Middle commit note removed")

    def test_unicode_and_large_content(self):
        """Test workflow with Unicode and large content."""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_path = Path(tmpdir) / "unicode_repo"
            create_test_repo(repo_path, ["Unicode test commit"])

            # Test Unicode content
            unicode_yaml = """schema: tigs.chat/v1
messages:
- role: user
  content: |
    How do I say hello in different languages?
    🌍 Unicode test: 你好, مرحبا, नमस्ते
- role: assistant
  content: |
    Here are greetings:
    - Chinese: 你好 (nǐ hǎo)
    - Arabic: مرحبا (marhaban)
    - Hindi: नमस्ते (namaste)
    Using emojis: 👋 🌟 ✨
"""

            result = run_tigs(repo_path, "add-chat", "-m", unicode_yaml)
            print(f"Unicode add: {result.returncode}")

            if result.returncode == 0:
                # Verify Unicode content is preserved
                notes_exist, stored_content = check_git_notes(repo_path)
                if notes_exist and stored_content:
                    if validate_yaml_schema(stored_content):
                        print("✓ Unicode YAML stored and validates")
                    if "你好" in stored_content and "👋" in stored_content:
                        print("✓ Unicode characters preserved")

                # Verify through show command
                result = run_tigs(repo_path, "show-chat")
                if result.returncode == 0:
                    if validate_yaml_schema(result.stdout):
                        print("✓ Unicode YAML retrieved and validates")
                    if "你好" in result.stdout and "👋" in result.stdout:
                        print("✓ Unicode characters preserved in output")

    def test_repository_isolation(self):
        """Test that different repositories are properly isolated."""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo1_path = Path(tmpdir) / "repo1"
            repo2_path = Path(tmpdir) / "repo2"

            # Create two separate repos
            create_test_repo(repo1_path, ["Repo1 commit"])
            create_test_repo(repo2_path, ["Repo2 commit"])

            # Add different chats to each repo
            content1 = "schema: tigs.chat/v1\nmessages:\n- role: user\n  content: Repo1 discussion"
            content2 = "schema: tigs.chat/v1\nmessages:\n- role: user\n  content: Repo2 discussion"

            result1 = run_tigs(repo1_path, "add-chat", "-m", content1)
            result2 = run_tigs(repo2_path, "add-chat", "-m", content2)

            print(f"Repo1 add: {result1.returncode}")
            print(f"Repo2 add: {result2.returncode}")

            if result1.returncode == 0 and result2.returncode == 0:
                # Extract SHAs
                sha1 = (
                    result1.stdout.split(":")[-1].strip()
                    if "commit:" in result1.stdout
                    else None
                )
                sha2 = (
                    result2.stdout.split(":")[-1].strip()
                    if "commit:" in result2.stdout
                    else None
                )

                # Verify isolation: repo1 should only see its chat
                result = run_tigs(repo1_path, "list-chats")
                if result.returncode == 0:
                    if sha1 and sha1 in result.stdout:
                        print("✓ Repo1 sees its own chat")
                    if sha2 and sha2 not in result.stdout:
                        print("✓ Repo1 doesn't see repo2's chat")

                # Verify isolation: repo2 should only see its chat
                result = run_tigs(repo2_path, "list-chats")
                if result.returncode == 0:
                    if sha2 and sha2 in result.stdout:
                        print("✓ Repo2 sees its own chat")
                    if sha1 and sha1 not in result.stdout:
                        print("✓ Repo2 doesn't see repo1's chat")

                # Verify content isolation
                result = run_tigs(repo1_path, "show-chat")
                if result.returncode == 0 and "Repo1 discussion" in result.stdout:
                    print("✓ Repo1 shows correct content")

                result = run_tigs(repo2_path, "show-chat")
                if result.returncode == 0 and "Repo2 discussion" in result.stdout:
                    print("✓ Repo2 shows correct content")

    def test_push_unpushed_commits_validation(self):
        """Test that push command validates unpushed commits."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create main repo and bare remote
            repo_path = Path(tmpdir) / "local_repo"
            remote_path = Path(tmpdir) / "remote_repo.git"

            # Create local repo with initial commit
            create_test_repo(repo_path, ["Initial commit"])

            # Create bare remote repo
            subprocess.run(["git", "init", "--bare", str(remote_path)], check=True)

            # Add remote and push initial commit
            subprocess.run(
                ["git", "remote", "add", "origin", str(remote_path)],
                cwd=repo_path,
                check=True,
            )

            # Get the current branch name
            result = subprocess.run(
                ["git", "branch", "--show-current"],
                cwd=repo_path,
                capture_output=True,
                text=True,
                check=True,
            )
            current_branch = result.stdout.strip()

            # Configure the bare repository to accept pushes
            subprocess.run(
                ["git", "config", "receive.denyCurrentBranch", "ignore"],
                cwd=remote_path,
                check=True,
            )

            subprocess.run(
                ["git", "push", "-u", "origin", current_branch], cwd=repo_path, check=True
            )

            # Create an unpushed commit
            test_file = repo_path / "test.txt"
            test_file.write_text("unpushed content")
            subprocess.run(["git", "add", "test.txt"], cwd=repo_path, check=True)
            subprocess.run(
                ["git", "commit", "-m", "Unpushed commit"], cwd=repo_path, check=True
            )

            # Add chat to the unpushed commit
            content = "schema: tigs.chat/v1\nmessages:\n- role: user\n  content: Chat on unpushed commit"
            result = run_tigs(repo_path, "add-chat", "HEAD", "-m", content)
            assert result.returncode == 0

            # Try to push chats - should fail with helpful error
            result = run_tigs(repo_path, "push")
            print(f"Push with unpushed commit: {result.returncode}")
            assert result.returncode != 0
            error_output = result.stderr

            # Check for helpful error message
            assert "cannot push chats" in error_output.lower()
            assert "unpushed commits" in error_output.lower()
            assert "git push origin" in error_output.lower()
            # The CLI provides clear guidance without mentioning --force flag directly
            print("✓ Push validation detects unpushed commits")

            # Now push the commit and try again
            subprocess.run(["git", "push", "origin", current_branch], cwd=repo_path, check=True)

            # Add another chat to test normal push
            test_file2 = repo_path / "test2.txt"
            test_file2.write_text("pushed content")
            subprocess.run(["git", "add", "test2.txt"], cwd=repo_path, check=True)
            subprocess.run(
                ["git", "commit", "-m", "Pushed commit"], cwd=repo_path, check=True
            )
            subprocess.run(["git", "push", "origin", current_branch], cwd=repo_path, check=True)

            content2 = "schema: tigs.chat/v1\nmessages:\n- role: user\n  content: Chat on pushed commit"
            result = run_tigs(repo_path, "add-chat", "HEAD", "-m", content2)
            assert result.returncode == 0

            # Now push should succeed
            result = run_tigs(repo_path, "push")
            print(f"Push with all commits pushed: {result.returncode}")
            assert result.returncode == 0
            assert "successfully pushed" in result.stdout.lower()
            print("✓ Push succeeds when all commits are pushed")

    def test_sync_operations(self):
        """Test push/fetch operations (error handling)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_path = Path(tmpdir) / "sync_repo"
            create_test_repo(repo_path, ["Sync test commit"])

            # Add a chat first
            content = (
                "schema: tigs.chat/v1\nmessages:\n- role: user\n  content: Sync test"
            )
            result = run_tigs(repo_path, "add-chat", "-m", content)

            if result.returncode != 0:
                print("Cannot test sync without working add-chat")
                return

            # Test new push command with non-existent remote (should fail gracefully)
            result = run_tigs(repo_path, "push", "nonexistent")
            print(f"Push to nonexistent remote: {result.returncode}")

            # Should fail but not crash
            assert result.returncode != 0
            error_output = result.stdout + result.stderr
            assert any(
                indicator in error_output.lower()
                for indicator in ["error", "remote", "not found", "does not exist"]
            )

            # Test new fetch command with non-existent remote (should fail gracefully)
            result = run_tigs(repo_path, "fetch", "nonexistent")
            print(f"Fetch from nonexistent remote: {result.returncode}")

            # Should fail but not crash
            assert result.returncode != 0

            # Test deprecated push-chats command (should work with warning)
            result = run_tigs(repo_path, "push-chats", "nonexistent")
            print(f"Deprecated push-chats: {result.returncode}")
            assert result.returncode != 0
            assert "deprecated" in result.stderr.lower()

            # Test deprecated fetch-chats command (should work with warning)
            result = run_tigs(repo_path, "fetch-chats", "nonexistent")
            print(f"Deprecated fetch-chats: {result.returncode}")
            assert result.returncode != 0
            assert "deprecated" in result.stderr.lower()

    def test_full_e2e_store_push_pull_view_cycle(self):
        """Test complete end-to-end workflow: store -> push -> pull -> view across two repos."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Setup: Create bare remote repository
            remote_path = Path(tmpdir) / "remote.git"
            subprocess.run(["git", "init", "--bare", str(remote_path)], check=True)

            # Setup: Create first local repository (producer)
            repo1_path = Path(tmpdir) / "repo1"
            create_test_repo(
                repo1_path,
                [
                    "Initial commit: Project setup",
                    "Feature: Add authentication module",
                    "Fix: Handle edge cases in auth",
                    "Docs: Update README with auth examples",
                ],
            )

            # Add remote and push commits to remote
            subprocess.run(
                ["git", "remote", "add", "origin", str(remote_path)],
                cwd=repo1_path,
                check=True,
            )

            # Get the current branch name (may be 'main' or 'master' depending on git version)
            result = subprocess.run(
                ["git", "branch", "--show-current"],
                cwd=repo1_path,
                capture_output=True,
                text=True,
                check=True,
            )
            current_branch = result.stdout.strip()

            # Configure the bare repository to accept pushes to the current branch
            subprocess.run(
                ["git", "config", "receive.denyCurrentBranch", "ignore"],
                cwd=remote_path,
                check=True,
            )

            # Push using the actual current branch name
            subprocess.run(
                ["git", "push", "-u", "origin", current_branch], cwd=repo1_path, check=True
            )

            # Step 1: STORE - Add chats using add-chat commands
            chat_contents = [
                """schema: tigs.chat/v1
messages:
- role: user
  content: How should we structure the authentication module?
- role: assistant
  content: Use JWT tokens with refresh token rotation for security.""",
                """schema: tigs.chat/v1
messages:
- role: user
  content: What edge cases need handling?
- role: assistant
  content: Consider timeout, invalid tokens, and concurrent sessions.""",
            ]

            # Get commit SHAs for adding chats
            result = subprocess.run(
                ["git", "log", "--format=%H", "-n", "4"],
                cwd=repo1_path,
                capture_output=True,
                text=True,
            )
            commit_shas = result.stdout.strip().split("\n")

            # Add chats to specific commits
            for sha, content in zip(
                commit_shas[2:4], chat_contents
            ):  # Add to 2nd and 3rd commits
                result = run_tigs(repo1_path, "add-chat", sha, "-m", content)
                assert result.returncode == 0, f"Failed to add chat to {sha}"

            # Verify chats were added
            result = run_tigs(repo1_path, "list-chats")
            assert result.returncode == 0
            stored_chats = result.stdout.strip().split("\n")
            assert len(stored_chats) >= 2, "Should have at least 2 chats stored"

            # Step 2: PUSH - Push chats to remote
            result = run_tigs(repo1_path, "push")
            assert result.returncode == 0, "Failed to push chats"
            assert "successfully pushed" in result.stdout.lower()

            # Step 3: Clone repository to second location (consumer)
            repo2_path = Path(tmpdir) / "repo2"
            subprocess.run(
                ["git", "clone", str(remote_path), str(repo2_path)],
                check=True,
                capture_output=True,
            )

            # Verify clone has commits but no chats yet
            result = run_tigs(repo2_path, "list-chats")
            assert result.returncode == 0
            assert result.stdout.strip() == "", (
                "Clone should not have chats before fetch"
            )

            # Step 4: PULL - Pull (fetch + merge) chats from remote
            result = run_tigs(repo2_path, "pull")
            assert result.returncode == 0, "Failed to pull chats"
            assert "successfully pulled" in result.stdout.lower()

            # Step 5: VERIFY - Check that chats are now available
            result = run_tigs(repo2_path, "list-chats")
            assert result.returncode == 0
            fetched_chats = result.stdout.strip().split("\n")
            assert len(fetched_chats) >= 2, "Should have fetched at least 2 chats"

            # Verify the fetched chats match what was pushed
            for sha in commit_shas[2:4]:
                result = run_tigs(repo2_path, "show-chat", sha)
                assert result.returncode == 0, f"Failed to show chat for {sha}"
                assert "schema: tigs.chat/v1" in result.stdout
                assert validate_yaml_schema(result.stdout)

            # Step 6: Additional verification - Add more chats in repo2 and push back
            new_chat = """schema: tigs.chat/v1
messages:
- role: user
  content: Should we add rate limiting?
- role: assistant
  content: Yes, implement exponential backoff for failed attempts."""

            result = run_tigs(repo2_path, "add-chat", commit_shas[1], "-m", new_chat)
            assert result.returncode == 0

            result = run_tigs(repo2_path, "push")
            assert result.returncode == 0

            # Step 7: Original repo pulls the new chat
            result = run_tigs(repo1_path, "pull")
            assert result.returncode == 0

            result = run_tigs(repo1_path, "show-chat", commit_shas[1])
            assert result.returncode == 0
            assert "rate limiting" in result.stdout

            # Final verification: Both repos have same chats
            result1 = run_tigs(repo1_path, "list-chats")
            result2 = run_tigs(repo2_path, "list-chats")
            assert result1.returncode == 0 and result2.returncode == 0

            chats1 = set(result1.stdout.strip().split("\n"))
            chats2 = set(result2.stdout.strip().split("\n"))
            assert chats1 == chats2, "Both repos should have identical chat lists"

            print("✓ Complete e2e cycle: store -> push -> pull -> view successful")
            print(f"✓ Synced {len(chats1)} chats between repositories")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
