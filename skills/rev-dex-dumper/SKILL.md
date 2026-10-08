---
name: rev-dex-dumper
description: Dump DEX files from a running Android app for unpacking/deobfuscation. Activate when the user wants to unpack an Android APK, dump DEX from memory, extract decrypted DEX files, or defeat class-loading packing.
---

# rev-dex-dumper - Android DEX Dumper

Use this skill when the task matches the description above.
Keep the initial response concise and only open bundled references or scripts when clearly needed.

## Quick cues

- **Always verify ADB connection first** — run `adb devices` and confirm a device is listed before proceeding.
- **Multiple DEX files are normal** — packed apps often produce several DEX files. All files in `/data/local/tmp/panda/` should be pulled.

## Available sections

- rev-dex-dumper - Android DEX Dumper
- Tool Location
- Workflow
- 1. Push the tool to device
- 2. Determine target package name
- 3. Run the dumper
- 4. Pull DEX files to host
- 5. Clean up device cache
- Guidelines

## Bundled resources

- panda-dex-dumper
