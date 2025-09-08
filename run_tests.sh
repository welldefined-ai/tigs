#!/bin/bash
set -e

# Parse test scope flags and collect test arguments
INCLUDE_PYTHON=false
INCLUDE_E2E=false
TEST_FILES=()

# Parse arguments
while [[ $# -gt 0 ]]; do
  case $1 in
    --python)
      INCLUDE_PYTHON=true
      shift
      ;;
    --e2e)
      INCLUDE_E2E=true
      shift
      ;;
    *)
      TEST_FILES+=("$1")
      shift
      ;;
  esac
done

# If no scope flags, default to running everything
if [ "$INCLUDE_PYTHON" = false ] && [ "$INCLUDE_E2E" = false ] && [ ${#TEST_FILES[@]} -eq 0 ]; then
  INCLUDE_PYTHON=true
  INCLUDE_E2E=true
fi

# Collect all test targets
ALL_TARGETS=()

# Add python tests if requested
if [ "$INCLUDE_PYTHON" = true ]; then
  ALL_TARGETS+=("python/tests/")
fi

# Add E2E tests if requested
if [ "$INCLUDE_E2E" = true ]; then
  ALL_TARGETS+=("tests/")
fi

# Add specific test files
for file in "${TEST_FILES[@]}"; do
  ALL_TARGETS+=("$file")
done

# Set up environment
echo "Setting up test environment..."
uv sync
uv pip install -e python/  # Install implementation for E2E tests

# Run collected test targets
if [ ${#ALL_TARGETS[@]} -eq 0 ]; then
  echo "No tests to run"
  exit 0
fi

echo "Running test targets: ${ALL_TARGETS[*]}"
uv run pytest "${ALL_TARGETS[@]}" --tb=short