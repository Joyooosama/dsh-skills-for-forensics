---
name: jadx
description: Android APK decompiler that converts DEX bytecode to readable Java source code. Use when you need to decompile APK files, analyze app logic, search for vulnerabilities, find hardcoded credentials, or understand app behavior through readable source code.
---

# Jadx - Android APK Decompiler

Use this skill when the task matches the description above.
Keep the initial response concise and only open bundled references or scripts when clearly needed.

## Quick cues

- Converting DEX bytecode to readable Java source
- Understanding app logic and control flow
- Finding security vulnerabilities in code
- Discovering hardcoded credentials, API keys, URLs
- Analyzing encryption/authentication implementations
- Searching through code with familiar Java syntax
- **jadx** (and optionally **jadx-gui**) must be installed
- Java Runtime Environment (JRE) required

## Windows tool discovery

Before running JADX on Windows, run the bundled preflight script. It checks `PATH`, `JADX_HOME`, common `C:\Tools`, Program Files, Scoop, and Chocolatey locations, then returns the resolved CLI, GUI, and Java paths.

```powershell
$tool = & "$env:USERPROFILE\.agents\skills\jadx\scripts\find-jadx.ps1" -Json | ConvertFrom-Json
if (-not $tool.found) {
    throw 'JADX CLI was not found. Install JADX or set JADX_HOME.'
}
if (-not $tool.java) {
    throw 'Java was not found. Install a JRE/JDK and retry.'
}
$jadx = $tool.cli
$jadxGui = $tool.gui
```

Use `$jadx` and `$jadxGui` instead of assuming that `jadx` is already in `PATH`. If the script returns `found: false`, do not guess a path.

## Available sections

- Jadx - Android APK Decompiler
- Tool Overview
- Prerequisites
- GUI vs CLI
- Instructions
- 1. Basic APK Decompilation (Most Common)
- 2. Understanding Output Structure
- 3. Decompilation Options
- A. Performance Options
- -j specifies number of threads (default: CPU cores)
- B. Deobfuscation Options
- C. Output Control
