"""Global pytest configuration for tigs E2E testing."""

from framework.fixtures import multiline_repo

# Re-export multiline_repo as test_repo for backward compatibility
test_repo = multiline_repo