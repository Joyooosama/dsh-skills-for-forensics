---
name: rev-symbol
description: Restore function symbols by analyzing code patterns, strings, constants, and cross-references
---

# rev-symbol - Symbol Recovery

Use this skill when the task matches the description above.
Keep the initial response concise and only open bundled references or scripts when clearly needed.

## Quick cues

- Check if `decompile/` directory exists
- Check if there are `.c` files inside
- Download plugin: https://github.com/P4nda0s/IDA-NO-MCP
- Copy INP.py to IDA plugins directory
- Press Ctrl-Shift-E in IDA to export
- Open the exported directory with Claude Code
- func-name: sub_401000
- func-address: 0x401000

## Available sections

- rev-symbol - Symbol Recovery
- Pre-check
- Export Directory Structure
- Function File Format (decompile/*.c)
- Symbol Recovery Steps
- Step 1: Analyze Internal Characteristics
- Step 2: Analyze Cross-References
- Step 3: Information Gathering and Search
- Output Format
- Symbol Recovery Analysis: <function_address>
- Function Characteristics
- Cross-Reference Analysis
