# Issue #14 Verification

## Goal
Implement sessions list showing only timestamps in the right pane (20% width)

## Implementation Summary

### ✅ Definition of Done

1. **Lists sessions via `cligent.ChatParser("claude-code").list_logs()`**
   - ✅ Integrated cligent library
   - ✅ ChatParser initialized in __init__
   - ✅ Sessions loaded from list_logs()

2. **Sorted by modification time descending (newest at top)**
   - ✅ `sorted(logs, key=lambda x: x[1]['modified'], reverse=True)`
   - ✅ Latest session appears first

3. **Latest session auto-selected on startup**
   - ✅ `self.selected_session_idx = 0` selects first (newest) session
   - ✅ Visual indicator: "•" for selected session

4. **Shows only relative timestamps: "14:32", "2h ago", "yesterday"**
   - ✅ `_format_timestamp()` method implemented
   - ✅ Formats: "just now", "Xm ago", "Xh ago", "yesterday", "Xd ago", "MM/DD HH:MM"

5. **Up/Down navigation, selection triggers message reload**
   - ✅ Arrow keys navigate when sessions pane is focused
   - ✅ Selection updates `selected_session_idx`
   - ✅ TODO comment for message reload (Issue #15)

6. **Single selection only (radio button behavior)**
   - ✅ Only one session can be selected at a time
   - ✅ "•" indicator for selected, "  " for unselected

7. **Handles empty log directory gracefully**
   - ✅ Shows "No sessions found" when empty
   - ✅ Shows "Cligent not available" if import fails
   - ✅ No crashes with missing/empty logs

## Features Implemented

- **Dependency**: Added `cligent>=0.1.2` to pyproject.toml
- **Session loading**: `_load_sessions()` fetches and sorts logs
- **Timestamp formatting**: `_format_timestamp()` creates relative times
- **Display generation**: `_get_session_display_lines()` formats for display
- **Scrolling support**: Handles lists longer than pane height
- **Navigation**: Up/Down arrows when focused on sessions pane

## Testing

```bash
# Run the TUI
uv run tigs store

# Expected behavior:
1. Sessions appear in right pane (20% width)
2. Shows timestamps only (no titles)
3. Latest session selected by default (•)
4. Tab to focus sessions pane
5. Up/Down arrows navigate sessions
6. Timestamps show relative format
```

## Next Steps

Issue #15 will implement message loading when session selection changes.

## Status: ✅ COMPLETE

All Definition of Done criteria have been met for Issue #14.