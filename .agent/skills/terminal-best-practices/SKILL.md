---
name: terminal-best-practices
description: Standards for executing and verifying terminal commands
---

# Terminal Best Practices

## 1. Verify Critical Commands
**Rule:** When executing critical commands (git commit, build, deploy, heavy file operations), successful dispatch does NOT mean successful execution.
**Action:** YOU MUST always use `command_status` to verify the output of these commands immediately after running them.

**Example:**
```javascript
// BAD
run_command("git commit -m 'fix'");
notify_user("Committed!");

// GOOD
run_command("git commit -m 'fix'");
command_status(command_id);
// Check output for "1 file changed" or errors
notify_user("Committed successfully!");
```

## 2. Check Command Compatibility
**Rule:** Assume standard Windows PowerShell limitations.
**Action:** Do NOT use `&&` or `||` for chaining unless you are certain of the shell environment. Split commands into separate tool calls.

## 4. Background Processes in PowerShell
**Rule:** The `start` command in PowerShell is an alias for `Start-Process`. It **does NOT** accept the legacy cmd.exe syntax like `start "Title" /B command arguments`.
**Action:** Never use `start "Title" /B` in PowerShell. Instead, use:
```powershell
Start-Process -FilePath "python.exe" -ArgumentList "-m http.server 8080" -WindowStyle Hidden
```

## 5. Tool Usage Integrity (Anti-Workaround)
**Rule:** When communicating with the user, you must exclusively use the `notify_user` tool or standard conversational responses (when not in a task boundary).
**Action:** NEVER use `run_command` with `echo`, `print`, or similar commands solely to output messages to the terminal as a workaround for communication restrictions. If you are blocked from using `notify_user`, you should simply provide a standard conversational response. Terminal commands are for system operations, not for chatting with the user.

## 6. Persistent Memory
**Rule:** This skill should be reviewed at the start of complex coding sessions to ensure operational reliability.
