---
name: rev-struct
description: Reconstruct data structures by analyzing memory access patterns across functions
---

# rev-struct - Structure Recovery

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

- rev-struct - Structure Recovery
- Pre-check
- Export Directory Structure
- Function File Format (decompile/*.c)
- Structure Recovery Steps
- Step 1: Read Target Function
- Step 2: Collect Memory Access Patterns
- Step 3: Traverse Callers for Analysis
- Step 4: Traverse Callees for Analysis
- Step 5: Aggregate and Infer
- Output Format
