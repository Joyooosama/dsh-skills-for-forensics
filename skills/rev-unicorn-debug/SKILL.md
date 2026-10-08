---
name: rev-unicorn-debug
description: Debug and emulate specific code fragments or functions using the Unicorn engine. Activate when the user wants to emulate a function with Unicorn, trace binary execution without running the full program, decrypt or decode data by emulating the algorithm, or bypass environment dependencies (JNI, syscalls, libc) during emulation.
---

# rev-unicorn-debug - Unicorn Emulation Debugger

Use this skill when the task matches the description above.
Keep the initial response concise and only open bundled references or scripts when clearly needed.

## Quick cues

- **Use callbacks extensively** — leverage Unicorn's hook system for debugging, tracing, error recovery, and environment simulation.
- **Run** — start emulation, let it crash
- **Read callback output** — which address faulted? What type (read/write/fetch)?
- **Diagnose**:
- Unmapped memory fetch → missing code page, map it
- Unmapped memory read/write → missing data section or uninitialized pointer, map or hook
- Hitting an import stub → identify the function, add a simulation hook
- Infinite loop → add a code hook with execution counter, stop after threshold

## Available sections

- rev-unicorn-debug - Unicorn Emulation Debugger
- Core Principles
- Environment Simulation Strategy
- Callback Types to Use
- Iterative Debugging Workflow
- Architecture Quick Reference
