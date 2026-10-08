---
name: using-git-worktrees
description: Use when starting feature work that needs isolation from current workspace or before executing implementation plans - creates isolated git worktrees with smart directory selection and safety verification
---

# Using Git Worktrees

Use this skill when the task matches the description above.
Keep the initial response concise and only open bundled references or scripts when clearly needed.

## Quick cues

- .worktrees/ (project-local, hidden)
- ~/.config/superpowers/worktrees/<project-name>/ (global location)
- Add appropriate line to .gitignore
- Commit the change
- Proceed with worktree creation
- **Problem:** Worktree contents get tracked, pollute git status
- **Fix:** Always use `git check-ignore` before creating project-local worktree
- **Problem:** Creates inconsistency, violates project conventions

## Available sections

- Using Git Worktrees
- Overview
- Directory Selection Process
- 1. Check Existing Directories
- Check in priority order
- 2. Check CLAUDE.md
- 3. Ask User
- Safety Verification
- For Project-Local Directories (.worktrees or worktrees)
- Check if directory is ignored (respects local, global, and system gitignore)
- For Global Directory (~/.config/superpowers/worktrees)
- Creation Steps
