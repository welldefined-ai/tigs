# /tigs::commit - Create Commit and Link Chats

Create a git commit and optionally link relevant chat messages to it using the interactive TUI.

## Your Task

Guide the user through creating a commit and linking chat history in a streamlined workflow.

## Workflow

### Step 1: Review Changes

Run git commands in parallel to understand the current state:
- `git status` - Show staged and unstaged files
- `git diff --cached` - Show staged changes
- `git diff` - Show unstaged changes

Display the changes to the user.

### Step 2: Stage Files (if needed)

If there are unstaged changes that should be committed:
- Use AskUserQuestion to ask ONCE: "Which files should we stage?"
  - Options: "All files", "Modified files only", "Let me specify"
- Run `git add <files>` to stage the selected files
- **Do NOT ask for confirmation again** - proceed directly to Step 3

If nothing is staged and nothing is unstaged:
- Use AskUserQuestion to ask if they want to link chats to HEAD instead
- If yes, skip to Step 4 (launch TUI for HEAD)

### Step 3: Create Commit

Create a descriptive commit message following the repository's style:
- Review recent commits with `git log --oneline -10` to understand the style
- Draft a clear, concise commit message that explains the "why" not just the "what"
- Run `git commit -m "message"` to create the commit immediately
- Capture and save the commit SHA from the output

**Important**:
- Use regular `git commit`, NOT the special Claude Code commit format (no co-author, no emoji)
- **Do NOT ask "Ready to commit?"** - just create the commit directly after staging

### Step 4: Launch Interactive TUI

**Always** launch the TUI automatically after creating the commit. No need to ask - if the user doesn't want to link chats, they can simply press 'q' to quit the TUI.

The TUI requires a fully interactive terminal. Auto-open a new terminal window/tab with `tigs store`:

**For macOS**, run:
```bash
osascript -e '
tell application "System Events"
    set terminalRunning to (name of processes) contains "Terminal"
end tell

tell application "Terminal"
    do script "cd \"'$(pwd)'\" && tigs store"
    if terminalRunning then
        activate
    end if
end tell
' 2>/dev/null
```

This checks if Terminal is already running before activating it, avoiding the duplicate window issue when Terminal launches fresh.

**For Linux**, try terminals in order (gnome-terminal, konsole, xterm):
```bash
# Try gnome-terminal first
if command -v gnome-terminal >/dev/null 2>&1; then
    gnome-terminal --working-directory="$(pwd)" -- bash -c "tigs store; exec bash" &
    sleep 0.2
    wmctrl -a "Terminal" 2>/dev/null || true
elif command -v konsole >/dev/null 2>&1; then
    konsole --workdir "$(pwd)" -e bash -c "tigs store; exec bash" &
    sleep 0.2
    wmctrl -a "Konsole" 2>/dev/null || true
elif command -v xterm >/dev/null 2>&1; then
    xterm -e "cd \"$(pwd)\" && tigs store; bash" &
    sleep 0.2
    wmctrl -a "XTerm" 2>/dev/null || true
else
    echo "No supported terminal found. Please run 'tigs store' manually in your terminal."
fi
```

**Note**: On Linux, `wmctrl` (if available) will try to bring the terminal to the foreground. If not available, the terminal will still open but may be in the background.

Inform the user:
```
✓ Created commit {SHORT_SHA}: {COMMIT_MESSAGE}

Opening tigs store TUI in a new terminal window...

TUI Controls:
  Tab/Shift+Tab - Switch between panes
  ↑/↓ - Navigate within pane
  Space - Select/deselect items
  Enter - Store selected messages to selected commit
  q - Quit

Your new commit ({SHORT_SHA}) is at the top of the commits list.

When you're done linking chats, return to this window.
```

**Note**: Do NOT try to wait for the terminal to close. The terminal opens automatically. Just inform the user and finish.

### Step 5: Completion Message

After opening the terminal, show:
```
✓ Commit created successfully
  Commit: {SHORT_SHA}

The tigs store TUI is now open in a separate terminal window.
- To link chat messages: Select the commit with Space, navigate with Tab, select messages, press Enter
- To skip linking: Press 'q' to quit
- View linked chats later with: tigs show {SHORT_SHA}
```

## Important Notes

### About TodoWrite
- **DO NOT** use the TodoWrite tool for this command
- The workflow is simple enough that tracking steps would be overhead
- Just execute the steps sequentially

### About Commit Messages
- Follow the repository's existing commit message style
- Be concise but descriptive
- Focus on the "why" rather than just the "what"
- Do NOT use the Claude Code co-author format

### Error Handling
- **No changes to commit**: Ask if they want to link chats to HEAD instead (using AskUserQuestion)
- **tigs store not available**: Inform user they can link chats later by running `tigs store` manually
- **Terminal fails to open**: Fall back to telling user to run `tigs store` manually in their terminal

### Alternative: Link Chats to Existing Commit

If the user doesn't want to create a new commit but just wants to link chats to an existing commit:
1. Use AskUserQuestion to ask which commit (with options like "HEAD", "Previous commit", "Specify SHA")
2. Skip directly to Step 4 (launching terminal with `tigs store`)

## Example Flow

**User runs**: `/tigs::commit`

**You respond**:

1. Show git status and diff:
```
Changes to commit:
  M src/auth.py
  A tests/test_auth.py

Creating commit...
```

2. Create commit immediately:
```
✓ Created commit a3f7d21: Add user authentication with JWT tokens
```

3. Automatically open terminal (no questions):
```
Opening tigs store TUI in a new terminal window...

TUI Controls:
  Tab/Shift+Tab - Switch panes
  Space - Select items
  Enter - Link selected messages
  q - Quit (if you don't want to link chats)

Your new commit (a3f7d21) is at the top of the commits list.
```

4. Run platform-specific terminal command (osascript for macOS, gnome-terminal for Linux)

5. Show completion:
```
✓ Commit created successfully
  Commit: a3f7d21

The tigs store TUI is now open in a separate terminal window.
- To link chat messages: Select the commit with Space, navigate with Tab, select messages, press Enter
- To skip linking: Press 'q' to quit
- View linked chats later with: tigs show a3f7d21
```

**Key**: Zero questions after commit is created - TUI opens automatically. User can simply press 'q' to skip linking if not needed.

## Tips

- Keep commit messages concise (50 chars for subject line)
- The TUI will preserve existing chat links when updating
- You can link messages from multiple chat providers to the same commit
- Chat history is stored in git notes and survives rebases
