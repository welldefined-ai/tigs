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

### Step 4: Analyze and Suggest Relevant Messages

**Fetch recent chat messages:**
```bash
tigs list-messages --recent 5
```

This fetches the most recent 5 logs (regardless of time) and returns YAML with their messages. Parse the output and analyze:

1. **Get commit context:**
   - Run `git show --stat <commit_sha>` to see files changed
   - Run `git show <commit_sha>` to see the diff
   - Extract commit message

2. **Analyze each message for relevance:**
   - Match keywords from commit message/diff with message content
   - Check timestamps (messages close to commit time are more relevant)
   - Look for code snippets, file names, function names mentioned
   - Score each message (0-10) based on relevance

3. **Select ALL relevant messages per log (score > 6):**
   - Group messages by log_uri
   - For each log, include ALL messages with score > 6
   - Skip logs that have no messages scoring > 6
   - Build suggestion format: `"<log_uri>:<idx>,<idx>,...;<log_uri>:<idx>,..."`

**Example analysis:**
```
Commit: "Add JWT authentication to API"
Diff includes: auth.py, token.py, added jwt library

Relevant messages found:
- Log: claude-code:/path/to/log
  - Message 5 (score 9): "Let's add JWT authentication"
  - Message 6 (score 8): "I'll implement the token generation"
  - Message 7 (score 7): "Need to add jwt library"
  - Message 10 (score 7): "Testing the auth endpoints"
- Log: codex-cli:/path/to/other
  - Message 3 (score 8): "Reviewing auth implementation"

Suggestion string: "claude-code:/path/to/log:5,6,7,10;codex-cli:/path/to/other:3"
```

**If no messages score > 6:** Don't pass `--suggest` flag at all.

### Step 5: Launch Interactive TUI with Suggestions

**Always** launch the TUI automatically with AI suggestions. No need to ask - if the user doesn't want to link chats, they can press 'q' to quit.

The TUI requires a fully interactive terminal. Auto-open a new terminal window/tab:

**If suggestions found:**
```bash
tigs store --commit <COMMIT_SHA> --suggest "<SUGGESTIONS>"
```

**If no suggestions found:**
```bash
tigs store --commit <COMMIT_SHA>
```

**For macOS**, run:
```bash
# Build the tigs command (with or without suggestions)
if [ -n "<SUGGESTIONS>" ]; then
    TIGS_CMD="tigs store --commit <COMMIT_SHA> --suggest \"<SUGGESTIONS>\""
else
    TIGS_CMD="tigs store --commit <COMMIT_SHA>"
fi

osascript -e "
tell application \"System Events\"
    set terminalRunning to (name of processes) contains \"Terminal\"
end tell

tell application \"Terminal\"
    do script \"cd '$PWD' && $TIGS_CMD\"
    if terminalRunning then
        activate
    end if
end tell
" 2>/dev/null
```

**For Linux**, try terminals in order (gnome-terminal, konsole, xterm):
```bash
# Build the tigs command (with or without suggestions)
if [ -n "<SUGGESTIONS>" ]; then
    TIGS_CMD="tigs store --commit <COMMIT_SHA> --suggest \"<SUGGESTIONS>\""
else
    TIGS_CMD="tigs store --commit <COMMIT_SHA>"
fi

# Try gnome-terminal first
if command -v gnome-terminal >/dev/null 2>&1; then
    gnome-terminal --working-directory="$(pwd)" -- bash -c "$TIGS_CMD; exec bash" &
    sleep 0.2
    wmctrl -a "Terminal" 2>/dev/null || true
elif command -v konsole >/dev/null 2>&1; then
    konsole --workdir "$(pwd)" -e bash -c "$TIGS_CMD; exec bash" &
    sleep 0.2
    wmctrl -a "Konsole" 2>/dev/null || true
elif command -v xterm >/dev/null 2>&1; then
    xterm -e "cd \"$(pwd)\" && $TIGS_CMD; bash" &
    sleep 0.2
    wmctrl -a "XTerm" 2>/dev/null || true
else
    echo "No supported terminal found. Please run '$TIGS_CMD' manually in your terminal."
fi
```

**Important**:
- Replace `<COMMIT_SHA>` with the actual commit SHA
- Replace `<SUGGESTIONS>` with the built suggestion string (or empty if no suggestions)
- The TUI will show a 2-pane layout (Messages | Logs) since --commit is specified
- Suggested messages will be pre-selected with `[x]`
- Logs with suggestions will show `*` marker

Inform the user:
```
✓ Created commit {SHORT_SHA}: {COMMIT_MESSAGE}

Analyzing recent chat messages for relevance...
Found {N} relevant messages across {M} logs

Opening tigs store TUI with AI suggestions in a new terminal window...

TUI Layout (2-pane):
  Messages | Logs

TUI Controls:
  Tab/Shift+Tab - Switch between panes
  ↑/↓ - Navigate within pane
  Space - Select/deselect messages
  Enter - Link selected messages to commit
  q - Quit

AI-suggested messages are pre-selected with [x]
Logs with suggestions are marked with *

You can adjust the selection before pressing Enter.
```

**Note**: Do NOT try to wait for the terminal to close. The terminal opens automatically. Just inform the user and finish.

### Step 6: Completion Message

After opening the terminal, show:
```
✓ Commit created successfully
  Commit: {SHORT_SHA}

The tigs store TUI is now open in a separate terminal window.
- AI has pre-selected relevant messages (marked with [x])
- Adjust selection as needed, then press Enter to link
- Press 'q' to skip linking
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

3. Analyze messages (run `tigs list-messages --recent 5`):
```
Analyzing most recent 5 logs for relevance...
```

4. Parse YAML, score messages, build suggestions:
```
Found 6 relevant messages across 2 logs:
- claude-code:/path/to/log: messages 12,13,14,15
- codex-cli:/path/to/log2: messages 3,7

Building suggestion string: "claude-code:/path/to/log:12,13,14,15;codex-cli:/path/to/log2:3,7"
```

5. Open terminal with suggestions:
```
Opening tigs store TUI with AI suggestions in a new terminal window...

TUI Layout (2-pane):
  Messages | Logs

AI-suggested messages are pre-selected with [x]
Logs with suggestions are marked with *
```

6. Run platform-specific terminal command with suggestions

7. Show completion:
```
✓ Commit created successfully
  Commit: a3f7d21

The tigs store TUI is now open in a separate terminal window.
- AI has pre-selected relevant messages (marked with [x])
- Adjust selection as needed, then press Enter to link
- Press 'q' to skip linking
- View linked chats later with: tigs show a3f7d21
```

**Key**: AI analyzes and suggests relevant messages automatically. User can adjust before linking.

## Tips

- Keep commit messages concise (50 chars for subject line)
- The TUI will preserve existing chat links when updating
- You can link messages from multiple chat providers to the same commit
- Chat history is stored in git notes and survives rebases
