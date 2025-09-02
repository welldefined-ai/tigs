# Issue #16 Verification

## Goal
Implement commit list with consistent selection operations matching the messages pane

## Implementation Summary

### ✅ Definition of Done

1. **Show `git log --oneline --date-order` (newest commits at top)**
   - ✅ `CommitView.load_commits()` uses `git log --oneline --date-order`
   - ✅ Newest commits appear first (default git behavior)

2. **Lazy load first 50 commits initially**
   - ✅ `load_commits(limit=50)` loads 50 commits by default
   - ✅ Can be extended later for dynamic loading

3. **Display format: `[x] SHA subject (author, relative_time)`**
   - ✅ Format: `>[x]* SHA subject (author, time)`
   - ✅ Short SHA (7 chars), truncated subject (50 chars)
   - ✅ Author and relative time shown when space allows

4. **Selection Operations**
   - ✅ **Space**: Toggle individual commit selection
   - ✅ **v**: Start visual range selection mode  
   - ✅ **c**: Clear all selections in commits pane
   - ✅ **a**: Select all visible commits
   - ✅ **Esc**: Cancel visual mode (if active)

5. **Additional Features**
   - ✅ `*` indicator for commits with existing notes
   - ✅ Selections preserved during scrolling
   - ✅ Cursor movement with Up/Down arrows

## Features Implemented

- **CommitView class**: `src/tui/commits.py`
  - Git log integration
  - Selection management
  - Visual mode support
  - Notes indicator
  - Relative time formatting

- **Integration**: Updated `app.py` to use CommitView
  - Commit pane shows real commits
  - Input handling when focused
  - Consistent with messages pane behavior

## Testing

```bash
# Run the TUI
uv run tigs store

# Expected behavior:
1. Commits appear in left pane (40% width)
2. Shows format: >[x]* SHA subject (author, time)
3. Tab to focus commits pane
4. Space toggles [x] selection
5. 'v' enters visual mode
6. 'c' clears all selections
7. 'a' selects all commits
8. Up/Down arrows navigate
9. '*' shows for commits with notes
```

## Verification Test Results

```python
# test_commit_view.py results:
✓ Created CommitView successfully
✓ Found 33 commits
✓ Generated 18 display lines
✓ Space toggles selection
✓ Down arrow moves cursor
✓ 'c' clears selections
✓ 'a' selects all

# test_commit_notes.py results:
✓ Found commits with notes
✓ Display shows * indicator for commits with notes
```

## Status: ✅ COMPLETE

All Definition of Done criteria have been met for Issue #16.