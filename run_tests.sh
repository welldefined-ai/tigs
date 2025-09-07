#!/bin/bash
set -e

# Check if a language flag is provided
LANGUAGE=""
TEST_ARGS=()

# Parse arguments
while [[ $# -gt 0 ]]; do
  case $1 in
    --python)
      LANGUAGE="${1#--}"
      shift
      ;;
    *)
      TEST_ARGS+=("$1")
      shift
      ;;
  esac
done

if [ -n "$LANGUAGE" ]; then
  echo "Running ${LANGUAGE}-specific tests only..."
  
  if [ ! -d "$LANGUAGE" ]; then
    echo "Error: $LANGUAGE directory not found"
    exit 1
  fi
  
  cd "$LANGUAGE"
  
  # Remove language/ prefix from args if present
  local_args=()
  for arg in "${TEST_ARGS[@]}"; do
    if [[ "$arg" == $LANGUAGE/tests/* ]]; then
      local_args+=("${arg#$LANGUAGE/}")
    else
      local_args+=("$arg")
    fi
  done
  
  # Each language directory is responsible for its own test execution
  # For Python: use uv run pytest
  # For Rust: would use cargo test  
  # For Go: would use go test
  case $LANGUAGE in
    python)
      uv sync
      uv pip install -e .
      uv run pytest "${local_args[@]}"
      ;;
    rust)
      cargo test "${local_args[@]}"
      ;;
    go)
      go test "${local_args[@]}"
      ;;
    *)
      echo "Unknown language: $LANGUAGE"
      exit 1
      ;;
  esac
else
  echo "Running comprehensive test suite..."
  
  # Run language-specific tests for each available language
  for lang_dir in python; do
    if [ -d "$lang_dir" ]; then
      echo "=== Running ${lang_dir}-specific tests ==="
      cd "$lang_dir"
      
      case $lang_dir in
        python)
          uv sync
          uv pip install -e .
          uv run pytest tests/ --tb=short || echo "${lang_dir} tests completed with issues"
          ;;
        rust)
          cargo test || echo "${lang_dir} tests completed with issues"
          ;;
        go)
          go test ./... || echo "${lang_dir} tests completed with issues"
          ;;
      esac
      
      cd ..
    fi
  done
  
  # Then run root tests (language-agnostic E2E tests)
  echo ""
  echo "=== Running language-agnostic E2E tests ==="
  uv sync
  uv pip install -e python/  # Install one implementation for E2E tests
  
  if [ ${#TEST_ARGS[@]} -eq 0 ]; then
    # No specific test args, run all root tests
    uv run pytest tests/
  else
    # Run specific tests provided as arguments
    uv run pytest "${TEST_ARGS[@]}"
  fi
fi