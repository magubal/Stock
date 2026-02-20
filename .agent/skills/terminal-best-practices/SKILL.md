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

## 3. Persistent Memory
**Rule:** This skill should be reviewed at the start of complex coding sessions to ensure operational reliability.
