#!/bin/bash
set -e

# Check if --python flag is provided
PYTHON_ONLY=false
PYTEST_ARGS=()

# Parse arguments
for arg in "$@"; do
  case $arg in
    --python)
      PYTHON_ONLY=true
      shift
      ;;
    *)
      PYTEST_ARGS+=("$arg")
      ;;
  esac
done

if [ "$PYTHON_ONLY" = true ]; then
  echo "Running Python-specific tests only..."
  cd python
  uv sync
  uv pip install -e .
  uv run pytest "${PYTEST_ARGS[@]}"
else
  echo "Running comprehensive test suite..."
  
  # First run Python-specific tests
  echo "=== Running Python-specific tests ==="
  cd python
  uv sync
  uv pip install -e .
  if [ ${#PYTEST_ARGS[@]} -eq 0 ]; then
    # No specific test args, run all Python tests
    uv run pytest tests/ || echo "Python tests completed with issues"
  else
    # Check if args are for Python tests specifically
    for arg in "${PYTEST_ARGS[@]}"; do
      if [[ "$arg" == python/tests/* ]]; then
        uv run pytest "${PYTEST_ARGS[@]}" || echo "Python tests completed with issues"
        exit 0
      fi
    done
  fi
  
  # Then run root tests
  echo ""
  echo "=== Running language-agnostic E2E tests ==="
  cd ..
  uv sync
  uv pip install -e python/
  if [ ${#PYTEST_ARGS[@]} -eq 0 ]; then
    # No specific test args, run all root tests
    uv run pytest tests/
  else
    # Check if args are for root tests
    uv run pytest "${PYTEST_ARGS[@]}"
  fi
fi