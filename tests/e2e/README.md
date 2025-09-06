# Tigs Cross-Language E2E Testing Framework

This directory contains a cross-language end-to-end testing framework for the Tigs project, inspired by [Tig's testing approach](https://github.com/jonas/tig/tree/master/test). The framework can test any implementation of Tigs (Python, Rust, Go, etc.) using the same test cases and infrastructure.

## Quick Start

### 1. Set up the testing environment

```bash
# From the project root
uv sync  # Install dependencies
```

### 2. Run tests for Python implementation

```bash
# Run all E2E tests
uv run pytest tests/ -v

# Run specific tests
uv run pytest tests/test_basic_navigation.py -v

# Run with specific implementation (default is python)
uv run pytest tests/ --implementation=python -v
```

### 3. Run tests with markers

```bash
# Only E2E tests
uv run pytest -m e2e -v

# Only slow tests
uv run pytest -m slow -v

# Only terminal interaction tests
uv run pytest -m terminal -v

# Exclude slow tests
uv run pytest -m "not slow" -v
```

## Overview

The framework provides:
- **Black-box testing**: Tests interact with the actual compiled application
- **Cross-language support**: Same tests work for Python, Rust, Go implementations
- **Terminal simulation**: Controls the application via PTY (pseudo-terminal)
- **Display capture**: Captures terminal output at any point (like Tig's `:save-display`)
- **User interaction simulation**: Sends keystrokes, commands, and special keys
- **Assertion framework**: Compares actual vs expected terminal output
- **Failure debugging**: Saves terminal screenshots when tests fail

## Project Structure

```
tests/
├── e2e/                     # E2E framework
│   ├── framework/           # Core framework components
│   │   ├── terminal.py      # TerminalApp - process control
│   │   ├── display.py       # Display capture and parsing
│   │   ├── assertions.py    # Test assertions
│   │   └── utils.py         # Helper utilities
│   ├── conftest.py          # E2E-specific pytest configuration
│   ├── verify_framework.py  # Framework verification script
│   └── README.md           # This file
├── conftest.py             # Root-level pytest configuration
└── test_*.py              # Cross-language test files
```

## Core Components

### TerminalApp
Manages the lifecycle of a terminal application under test:
```python
app = TerminalApp("tigs", ["store"], cwd=repo_path)
app.start()
app.send_keys(['j', 'j', 'k'])  # Navigate down twice, up once
display = app.capture_display()
app.stop()
```

### Display Capture
Captures and parses terminal output, handling ANSI escape sequences:
```python
display = app.capture_display()  # Get current screen content
app.display_capture.save_display("output.txt")  # Save to file
```

### Assertions
Provides terminal-specific assertion functions:
```python
from tests.e2e.framework.assertions import assert_display_matches, assert_display_contains

assert_display_contains(display, "commit", "Should show commit info")
assert_display_matches(display, expected_file, whitespace='ignore')
```

## Adding Support for New Implementations

To add support for a new language implementation (e.g., Rust or Go):

### 1. Update `tests/conftest.py`

Add the new implementation to `TIGS_IMPLEMENTATIONS`:

```python
TIGS_IMPLEMENTATIONS = {
    "python": {
        "command": ["uv", "run", "--project", "python", "python", "-c", "from src.cli import main; main()"],
        "cwd": Path(__file__).parent.parent,
        "description": "Python implementation via uv"
    },
    "rust": {
        "command": ["cargo", "run", "--manifest-path", "rust/Cargo.toml", "--"],
        "cwd": Path(__file__).parent.parent, 
        "description": "Rust implementation via cargo"
    },
    # Add more implementations...
}
```

### 2. Run tests with the new implementation

```bash
uv run pytest tests/ --implementation=rust -v
```

### 3. Implementation-specific tests

Create implementation-specific tests if needed:

```python
@pytest.mark.rust
def test_rust_specific_feature(tigs_app):
    # Test something specific to Rust implementation
    pass
```

## Writing Tests

### Basic Test Structure
```python
import pytest
from tests.e2e.framework.assertions import assert_display_contains

@pytest.mark.e2e
def test_basic_functionality(tigs_app):
    """Test basic tigs functionality."""
    # The app is already started by the fixture
    display = tigs_app.capture_display()
    
    # Verify expected content
    assert_display_contains(display, "commit", "Should show commits")
    
    # Simulate user input
    tigs_app.send_keys(['j', 'j'])  # Navigate down twice
    new_display = tigs_app.capture_display()
    
    # Verify changes
    assert new_display != display, "Display should change after navigation"
```

### Available Fixtures

- `tigs_app`: Ready-to-use tigs application with test repository
- `tigs_app_empty_repo`: tigs application with empty repository  
- `test_repo`: Temporary Git repository with sample commits
- `empty_repo`: Empty Git repository
- `terminal_app_factory`: Factory to create custom TerminalApp instances
- `temp_dir`: Temporary directory for test use

### Using Fixtures
```python
def test_with_test_repo(tigs_app, test_repo):
    """Use predefined test repository."""
    display = tigs_app.capture_display()
    assert_display_contains(display, "Initial commit")

def test_with_empty_repo(tigs_app_empty_repo):
    """Use empty repository."""  
    display = tigs_app.capture_display()
    assert_display_contains(display, "empty")
```

### Advanced Scenarios
```python
def test_user_session(tigs_app):
    """Simulate complex user interaction."""
    actions = [
        {'action': 'keys', 'value': ['j', 'j']},
        {'action': 'wait', 'value': 0.5},
        {'action': 'capture'},
        {'action': 'keys', 'value': '<Enter>'},
        {'action': 'capture'}
    ]
    
    captures = simulate_user_session(tigs_app, actions)
    assert len(captures) == 2
```

## Key Mapping

The framework supports standard terminal key sequences:

| Key | Code | Description |
|-----|------|-------------|
| `'j'` | `j` | Regular character |
| `'<Enter>'` | `\\r` | Enter/Return key |
| `'<Escape>'` | `\\x1b` | Escape key |
| `'<Up>'` | `\\x1b[A` | Up arrow |
| `'<Down>'` | `\\x1b[B` | Down arrow |  
| `'<Left>'` | `\\x1b[D` | Left arrow |
| `'<Right>'` | `\\x1b[C` | Right arrow |
| `'<Tab>'` | `\\t` | Tab key |
| `'<C-c>'` | `\\x03` | Ctrl+C |

## Configuration Options

### Command Line Options

- `--implementation=IMPL`: Choose implementation to test (python, rust, go)
- `--tigs-timeout=SECONDS`: Set timeout for tigs operations (default: 10.0)

### pytest Markers

- `@pytest.mark.e2e`: End-to-end integration tests
- `@pytest.mark.slow`: Slow running tests (>5s)
- `@pytest.mark.terminal`: Tests that interact with terminal
- `@pytest.mark.python`: Python implementation specific tests
- `@pytest.mark.rust`: Rust implementation specific tests
- `@pytest.mark.go`: Go implementation specific tests
- `@pytest.mark.cross_lang`: Cross-language compatibility tests

## Environment Setup

Tests run in a controlled environment similar to Tig:
- Terminal size: 80x30 (configurable)
- Locale: `en_US.UTF-8`
- Timezone: `UTC`
- Clean environment variables

## Development Workflow

### 1. Install development environment

```bash
# Install testing dependencies
uv sync

# Verify framework works
uv run python tests/e2e/verify_framework.py
```

### 2. Run tests during development  

```bash
# Run tests with verbose output
uv run pytest tests/ -v -s

# Run single test file
uv run pytest tests/test_navigation.py -v

# Run with live output (useful for debugging)
uv run pytest tests/ -v --capture=no

# Test specific implementation
uv run pytest tests/ --implementation=python -v
```

### 3. Debug failing tests

When tests fail, the framework automatically saves terminal screenshots:
- Check `tests/e2e/failures/` for captured displays (auto-created)
- Use `-s` flag to see live output
- Add `import time; time.sleep(10)` to pause and inspect manually

### 4. Add new test cases

1. Create test files in `tests/` (not in `tests/e2e/`)
2. Use the `@pytest.mark.e2e` marker
3. Follow existing patterns for fixtures and assertions
4. Test against multiple implementations when possible

## Example Usage

```python
@pytest.mark.e2e
@pytest.mark.slow  
def test_large_repository_performance(terminal_app_factory):
    """Test performance with large repository."""
    # Create app with longer timeout
    app = terminal_app_factory(timeout=30.0)
    # ... test code ...

@pytest.mark.cross_lang
def test_cli_compatibility(tigs_app):
    """Test that all implementations have compatible CLI."""
    # This test should pass for all implementations
    pass
```

## Implementation Selection

Tests automatically run against the selected implementation:

```bash
# Test Python implementation (default)
uv run pytest tests/ --implementation=python

# Test Rust implementation (when available)
uv run pytest tests/ --implementation=rust

# Test Go implementation (when available)  
uv run pytest tests/ --implementation=go
```

## Failure Debugging

When tests fail, the framework automatically:
1. Captures the current terminal display
2. Saves it to `failures/{test_name}_failure.txt`
3. Displays the file path in test output

This makes it easy to see exactly what the terminal looked like when the test failed.

## CI/CD Integration

### GitHub Actions Example

```yaml
- name: Run E2E Tests
  run: |
    uv sync
    uv run pytest tests/ -v --implementation=python
    # Add other implementations when available
```

### Local Testing Script

```bash
#!/bin/bash
set -e

echo "Running E2E tests for all implementations..."

# Test Python implementation
echo "Testing Python implementation..."
uv run pytest tests/ --implementation=python -v

# Add other implementations as they become available
# echo "Testing Rust implementation..."  
# uv run pytest tests/ --implementation=rust -v

echo "All tests passed!"
```

## Comparison with Tig's Approach

| Aspect | Tig Tests | This Framework |
|--------|-----------|----------------|
| Language | Shell scripts | Python/pytest |
| Process Control | Shell pipes/redirects | PTY (pseudo-terminal) |
| Display Capture | `:save-display` command | ANSI parser + buffer |
| Assertions | `assert_equals` function | Rich assertion framework |
| Organization | Individual `-test` files | pytest structure |
| CI Integration | `make test` | `pytest` with markers |
| Cross-language | N/A | Multiple implementations |

## Benefits of This Approach

1. **Cross-language compatibility**: Same tests work for all implementations
2. **Centralized testing**: All E2E tests in one place
3. **Implementation independence**: Tests verify behavior, not internal structure  
4. **Easy to extend**: Adding new implementations requires minimal changes
5. **Consistent environment**: All tests use the same controlled environment
6. **Rich debugging**: Automatic failure captures and detailed logging
7. **Modern tooling**: Uses pytest, uv, and Python ecosystem benefits

This framework ensures that all Tigs implementations maintain compatibility and consistent user experience across different programming languages.

## Extending the Framework

### Adding New Assertions
```python
# In framework/assertions.py
def assert_cursor_at_line(display, line_num):
    lines = display.split('\\n')
    cursor_line = find_cursor_line(lines)
    assert cursor_line == line_num
```

### Adding New Utilities  
```python  
# In framework/utils.py
def send_text_with_delay(app, text, delay=0.1):
    for char in text:
        app.send_keys(char)
        time.sleep(delay)
```

### Custom Fixtures
```python
# In conftest.py or test files
@pytest.fixture
def app_with_large_repo(terminal_app_factory):
    repo = create_large_test_repo()  # Your implementation
    app = terminal_app_factory(repo=repo)
    app.start()
    yield app
    app.stop()
```

This framework provides a solid foundation for comprehensive E2E testing of terminal applications, following the battle-tested approach pioneered by Tig while leveraging Python's rich testing ecosystem and supporting multiple language implementations.