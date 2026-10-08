---
name: rev-frida
description: Generate Frida hook scripts using modern Frida API. Activate when the user wants to write Frida scripts, hook functions at runtime, trace calls/arguments/return values, intercept native or ObjC/Java methods, or dump memory and exports.
---

# rev-frida - Frida Script Generator

Use this skill when the task matches the description above.
Keep the initial response concise and only open bundled references or scripts when clearly needed.

## Quick cues

- **Always use modern API** — `Process.getModuleByName()`, `mod.getExportByName()`, not deprecated `Module.findBaseAddress()`
- **No `--no-pause`** — the new Frida CLI does not support this flag
- **Handle module load timing** — if hooking early, check if the module is loaded first:
- **Print hex for pointers** — use `ptr.toString(16)` or `hexdump(ptr, { length: 64 })`
- **Wrap in try/catch** for robustness in production hooks
- **Use `hexdump()`** for binary data inspection:

## Available sections

- rev-frida - Frida Script Generator
- Important: Modern Frida CLI
- Spawn and hook (process starts after script loads)
- Attach to running process
- Attach by PID
- Modern API Reference
- Module & Symbol Lookup
- Interceptor
- NativeFunction & NativeCallback
- Memory Operations
- ObjC (iOS/macOS)
- Java (Android)
