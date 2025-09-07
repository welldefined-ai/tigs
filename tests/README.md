# Tigs E2E Testing

## Quick Start

```bash
# Run all tests (installs Python tigs first)
./run_python.sh

# Run with verbose output
./run_python.sh -v

# Run specific command tests
./run_python.sh tests/store/ -v

# Run specific view tests  
./run_python.sh tests/store/commits/ -v
```

## Test Structure (Command → View → Aspect)

```
tests/
├── framework/              # Shared testing infrastructure
│   ├── tui.py             # TUI interaction framework
│   └── fixtures.py        # Repository fixtures
├── store/                 # `tigs store` command tests
│   └── commits/           # Commit list view tests
│       ├── test_display.py      # How commits render
│       ├── test_navigation.py   # Cursor movement & scrolling
│       └── test_edge_cases.py   # Extreme scenarios
└── conftest.py           # Global test configuration
```

## Test Categories

### Store Command - Commit View

**Display (`test_display.py`)**
- Multi-line commit message rendering
- Long commit titles that wrap
- Mixed commit message lengths

**Navigation (`test_navigation.py`)**  
- Cursor movement through commits
- Viewport scrolling when reaching edges
- Uses simple commits for reliable testing

**Edge Cases (`test_edge_cases.py`)**
- 500+ character commit messages
- Unicode and special characters  
- Control characters and newlines
- Reveals display corruption issues

## Future Expansion

This structure supports adding:
- `tests/store/files/` - File tree view tests
- `tests/show/` - Show command tests  
- `tests/blame/` - Blame command tests
- `tests/integration/` - Cross-command tests