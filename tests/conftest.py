"""Global pytest configuration for tigs E2E testing."""

from framework.fixtures import extreme_repo, multiline_repo

# Re-export fixtures for test discovery
__all__ = ["extreme_repo", "multiline_repo", "test_repo"]

# Re-export multiline_repo as test_repo for backward compatibility
test_repo = multiline_repo
