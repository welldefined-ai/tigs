# Test Management

## Running Tests

Ensure a uv virtual environment exists at the project root before running tests; create one with `uv init` if absent.

Run all tests:
```bash
./run_python.sh
```

Run with verbose output:
```bash
./run_python.sh -v
```

Run specific test modules:
```bash
./run_python.sh tests/store/ -v
./run_python.sh tests/store/messages/ -v
```

## Test Structure

Tests are organized by command → view → aspect:

```
tests/
├── framework/              # Shared testing infrastructure
├── store/                  # `tigs store` command tests
│   ├── commits/           # Commit list view
│   ├── messages/          # Message pane view
│   ├── logs/              # Log management
│   └── *.py               # App-level tests
└── conftest.py            # Global configuration
```

## Framework

- **TUI Testing**: `framework/tui.py` (pexpect + pyte)
- **Test Data**: `framework/fixtures.py` (repository fixtures)

## Extension

The structure supports adding new command suites (e.g., `tests/view/`).

## Python Unit Tests

Python unit tests for the tigs Python implementation.

Run all Python unit tests:
```bash
./run_tests.sh python/tests/
```
