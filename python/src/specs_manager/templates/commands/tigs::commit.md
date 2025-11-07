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

**Step 4.1: Get commit context**
```bash
git show --stat <commit_sha>
git show <commit_sha>
```
- Understand what files were changed
- Extract commit message
- Identify key terms, features, file names to search for

**Step 4.2: Get log metadata (lightweight)**
```bash
tigs list-logs --recent 10
```
This returns metadata for the 10 most recent logs (log IDs, timestamps, message counts) - minimal token cost.

**Step 4.3: Progressive message analysis**

Search logs one at a time, starting with the most recent:

```bash
# Fetch messages from most recent log
tigs list-messages <log-id-1>
```

For each log:
1. **Analyze messages** - Look for conversation related to this commit
2. **Assess completeness** - Do you have the full story (start → middle → end)?
3. **Decision:**
   - If **complete** → Stop searching, build suggestions
   - If **incomplete** → Fetch next log's messages and continue
   - If **no relevant messages found yet** → Fetch next log
4. **Stop after 10 logs** maximum

This progressive approach minimizes token usage - only fetch what you need!

**Step 4.4: Identify relevant messages**

Within each log you fetch, look for:

   **Conversation start** - Messages where:
   - User explicitly requests the feature/change (e.g., "add dark mode", "implement authentication")
   - User describes the problem this commit solves
   - User initiates the task that led to these changes
   - Assistant proposes or begins planning the feature

   **Look for conversation middle** - Messages showing:
   - Implementation steps and progress updates
   - Code changes to files included in the commit
   - Design decisions and technical discussions
   - Debugging, testing, or refinement activities
   - File reads, edits, or writes related to commit files

   **Look for conversation end** - Messages where:
   - The work is completed and tested
   - The commit is created or prepared
   - Assistant summarizes what was accomplished
   - User approves or moves to a different topic

   **Important**: Conversations may be **interrupted and scattered**:
   - User might ask unrelated questions mid-conversation (skip those)
   - Work might pause and resume in the same log (include both parts)
   - Conversation might span multiple logs (continue searching)

**Step 4.5: Build complete conversation history**

As you progressively fetch and analyze logs:
   - Identify ALL relevant message segments across logs (up to 10 logs)
   - Within each log, find all segments (can be multiple non-contiguous ranges)
   - Group segments by log_id
   - Stop searching when you believe you have the complete story from start to finish
   - If uncertain, err on the side of including more context

**Step 4.6: Build suggestion string**

Once you have the complete conversation history:
   - Format with comma-separated indices: `<idx>,<idx>,<idx>,...`
   - Full format: `"<log_id>:<indices>;<log_id>:<indices>"`
   - Order logs chronologically (oldest first) to tell the story in order
   - Use the log IDs from `tigs list-logs` output

**Example 1: Complete conversation in single log (scattered messages)**

```
Commit: "feat: add dark mode theme support"
Files changed: ThemeContext.tsx, index.css, Settings.tsx

Step 1: Get log metadata
→ tigs list-logs --recent 10
→ Found: claude-code:e8f7d11f.jsonl (modified today, 50 messages)

Step 2: Fetch most recent log
→ tigs list-messages claude-code:e8f7d11f.jsonl

Analysis:
- Messages 5-12: User requests dark mode, planning discussion [START]
- Messages 13-18: UNRELATED - User asks about deployment (skip)
- Messages 19-35: Implementation of ThemeContext and CSS [MIDDLE]
- Messages 36-40: UNRELATED - Quick question about API (skip)
- Messages 41-47: Testing, fixing bugs, finalizing [END]
- Message 48: Commit created

Assessment: COMPLETE! All phases found in one log.

Suggestion string: "claude-code:e8f7d11f.jsonl:5,6,7,8,9,10,11,12,19,20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,35,41,42,43,44,45,46,47,48"
```

**Example 2: Conversation spanning multiple logs (progressive search)**

```
Commit: "fix: resolve authentication timeout issue"
Files changed: auth.py, session.py

Step 1: Get log metadata
→ tigs list-logs --recent 10
→ Found 10 logs, starting with most recent

Step 2: Fetch log 1 (most recent)
→ tigs list-messages claude-code:xyz789.jsonl

Analysis of xyz789.jsonl:
- Messages 0-5: Final testing and verification [END phase]
- Messages 6-10: Creating the commit
- No START or MIDDLE phases found
Assessment: INCOMPLETE - need earlier context

Step 3: Fetch log 2
→ tigs list-messages claude-code:def456.jsonl

Analysis of def456.jsonl:
- Messages 0-8: UNRELATED - Different feature work (skip)
- Messages 9-22: Root cause analysis, implementing fix [MIDDLE phase]
- Messages 23-30: UNRELATED - Documentation update (skip)
- Still no START phase
Assessment: INCOMPLETE - need to find initiation

Step 4: Fetch log 3
→ tigs list-messages claude-code:abc123.jsonl

Analysis of abc123.jsonl:
- Messages 25-40: User reports timeout bug, initial investigation [START phase]
Assessment: COMPLETE! Found all phases across 3 logs

Stopped after 3 logs (saved 7 log fetches).

Suggestion string (ordered oldest→newest):
"claude-code:abc123.jsonl:25,26,27,28,29,30,31,32,33,34,35,36,37,38,39,40;claude-code:def456.jsonl:9,10,11,12,13,14,15,16,17,18,19,20,21,22;claude-code:xyz789.jsonl:0,1,2,3,4,5,6,7,8,9,10"
```

**If no coherent conversation found:** Don't pass `--suggest` flag at all.

### Step 5: Launch Interactive TUI with Suggestions

**Always** launch the TUI automatically with AI suggestions. No need to ask - if the user doesn't want to link chats, they can press 'q' to quit.

The TUI requires a fully interactive terminal. Auto-open a new terminal window/tab:

**For macOS with suggestions**:
```bash
osascript <<EOF
tell application "System Events"
    set terminalRunning to (name of processes) contains "Terminal"
end tell

tell application "Terminal"
    do script "cd '$(pwd)' && tigs store --commit <COMMIT_SHA> --suggest \"<SUGGESTIONS>\""
    if terminalRunning then
        activate
    end if
end tell
EOF
```

**For macOS without suggestions**:
```bash
osascript <<EOF
tell application "System Events"
    set terminalRunning to (name of processes) contains "Terminal"
end tell

tell application "Terminal"
    do script "cd '$(pwd)' && tigs store --commit <COMMIT_SHA>"
    if terminalRunning then
        activate
    end if
end tell
EOF
```

**For Linux with suggestions**:
```bash
# Try gnome-terminal first
if command -v gnome-terminal >/dev/null 2>&1; then
    gnome-terminal --working-directory="$(pwd)" -- bash -c "tigs store --commit <COMMIT_SHA> --suggest \"<SUGGESTIONS>\"; exec bash" &
    wmctrl -a "Terminal" 2>/dev/null || true
elif command -v konsole >/dev/null 2>&1; then
    konsole --workdir "$(pwd)" -e bash -c "tigs store --commit <COMMIT_SHA> --suggest \"<SUGGESTIONS>\"; exec bash" &
    wmctrl -a "Konsole" 2>/dev/null || true
elif command -v xterm >/dev/null 2>&1; then
    xterm -e bash -c "cd \"$(pwd)\" && tigs store --commit <COMMIT_SHA> --suggest \"<SUGGESTIONS>\"; exec bash" &
else
    echo "No supported terminal found. Please run manually: tigs store --commit <COMMIT_SHA> --suggest \"<SUGGESTIONS>\""
fi
```

**For Linux without suggestions**:
```bash
# Try gnome-terminal first
if command -v gnome-terminal >/dev/null 2>&1; then
    gnome-terminal --working-directory="$(pwd)" -- bash -c "tigs store --commit <COMMIT_SHA>; exec bash" &
    wmctrl -a "Terminal" 2>/dev/null || true
elif command -v konsole >/dev/null 2>&1; then
    konsole --workdir "$(pwd)" -e bash -c "tigs store --commit <COMMIT_SHA>; exec bash" &
    wmctrl -a "Konsole" 2>/dev/null || true
elif command -v xterm >/dev/null 2>&1; then
    xterm -e bash -c "cd \"$(pwd)\" && tigs store --commit <COMMIT_SHA>; exec bash" &
else
    echo "No supported terminal found. Please run manually: tigs store --commit <COMMIT_SHA>"
fi
```

**Important**:
- Choose the appropriate command based on whether you found suggestions
- Replace `<COMMIT_SHA>` with the actual commit SHA
- Replace `<SUGGESTIONS>` with the built suggestion string
- The heredoc (<<EOF) and escaped quotes (\\") prevent quoting issues with long suggestion strings
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

When you're done linking chats, push your changes:
  git push              # Push your commits
  tigs push             # Push chat links
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

3. Get log metadata (run `tigs list-logs --recent 10`):
```
Retrieved 10 log files (metadata only):
- claude-code:log1.jsonl (modified: 2025-10-30 19:31, 25 messages)
- claude-code:log2.jsonl (modified: 2025-10-30 18:45, 42 messages)
- claude-code:log3.jsonl (modified: 2025-10-30 17:20, 38 messages)
...
```

4. Progressive search with early stopping:
```
Fetching messages from log1.jsonl (most recent)...
→ Found: final testing and commit creation (messages 0-5)
→ Assessment: Incomplete - no feature start found

Fetching messages from log2.jsonl...
→ Found: main implementation work (messages 12-28)
→ Assessment: Incomplete - still no feature initiation

Fetching messages from log3.jsonl...
→ Found: user request and initial planning (messages 40-45)
→ Assessment: COMPLETE! Have full story from start to finish

Stopping search (found complete conversation in 3 logs, saved 7 log fetches)

Suggestion string: "claude-code:log3.jsonl:40,41,42,43,44,45;claude-code:log2.jsonl:12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28;claude-code:log1.jsonl:0,1,2,3,4,5"
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

When you're done linking chats, push your changes:
  git push              # Push your commits
  tigs push             # Push chat links
```

**Key**: AI analyzes and suggests relevant messages automatically. User can adjust before linking.

## Tips

- Keep commit messages concise (50 chars for subject line)
- The TUI will preserve existing chat links when updating
- You can link messages from multiple chat providers to the same commit
- Chat history is stored in git notes and survives rebases
