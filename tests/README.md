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
./run_python.sh tests/store/messages/ -v
./run_python.sh tests/store/logs/ -v
```

## Test Structure (Command → View → Aspect)

```
tests/
├── framework/              # Shared testing infrastructure
│   ├── tui.py             # TUI interaction framework (pexpect + pyte)
│   └── fixtures.py        # Repository fixtures
├── store/                 # `tigs store` command tests
│   ├── commits/           # Commit list view tests
│   │   ├── test_display.py      # Commit rendering & multi-line handling
│   │   ├── test_navigation.py   # Cursor movement & scrolling behavior
│   │   ├── test_selection.py    # Selection operations (space/c/a/v)
│   │   └── test_edge_cases.py   # Extreme commit scenarios
│   ├── messages/          # Message pane view tests
│   │   ├── test_display.py      # Message formatting & anchoring  
│   │   └── test_selection.py    # Message selection operations
│   ├── logs/              # Log management tests
│   │   └── test_navigation.py   # Log lifecycle & navigation
│   ├── test_boot.py       # App initialization & 3-pane layout
│   ├── test_repo_edge_cases.py  # Repository edge cases
│   ├── test_storage.py    # Store operations & confirmation
│   ├── test_validation.py # Input validation scenarios
│   └── test_overwrite.py  # Overwrite prompt handling
└── conftest.py           # Global test configuration
```

## Test Categories

### Store Command - Commits View

**Display (`commits/test_display.py`)**
- Multi-line commit message rendering
- Varied commit message lengths 
- Cursor detection with wrapped text

**Navigation (`commits/test_navigation.py`)**  
- Cursor movement through commits
- Viewport scrolling when reaching edges
- Lazy loading behavior

**Selection (`commits/test_selection.py`)**
- Basic selection operations (space/c/a)
- Visual mode selection (v)
- Selection persistence during scrolling

**Edge Cases (`commits/test_edge_cases.py`)**
- 500+ character commit messages
- Unicode and special characters  
- Control characters and newlines

### Store Command - Messages View

**Display (`messages/test_display.py`)**
- Message formatting and indicators
- Bottom-anchored display behavior

**Selection (`messages/test_selection.py`)**
- Message selection with space/v/c/a keys
- Visual mode operations

### Store Command - Logs View

**Navigation (`logs/test_navigation.py`)**
- Log lifecycle operations
- Log navigation triggers reload
- Empty log state handling

### Store Command - App Level

**Boot (`test_boot.py`)**
- 3-pane layout initialization
- Initial commit lazy loading

**Storage (`test_storage.py`)**
- Store operations create notes
- Confirmation messages
- Selection state clearing

**Validation (`test_validation.py`)**
- No commits/messages selected scenarios
- Input validation preserves state

## Future Expansion

This structure supports adding:
- `tests/show/` - Show command tests  
- `tests/blame/` - Blame command tests
- `tests/integration/` - Cross-command tests