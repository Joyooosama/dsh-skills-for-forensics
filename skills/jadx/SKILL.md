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

Before running JADX on Windows, run this preflight block. It checks `PATH`, `JADX_HOME`, common `C:\Tools`, Program Files, Scoop, and Chocolatey locations, then resolves the CLI, GUI, and Java paths.

```powershell
$jadxCandidates = @()
$jadxGuiCandidates = @()

foreach ($name in @('jadx.bat', 'jadx.cmd', 'jadx.exe', 'jadx')) {
    $command = Get-Command $name -CommandType Application -ErrorAction SilentlyContinue | Select-Object -First 1
    if ($command) { $jadxCandidates += $command.Source }
}
foreach ($name in @('jadx-gui.bat', 'jadx-gui.cmd', 'jadx-gui.exe', 'jadx-gui')) {
    $command = Get-Command $name -CommandType Application -ErrorAction SilentlyContinue | Select-Object -First 1
    if ($command) { $jadxGuiCandidates += $command.Source }
}

$roots = @(
    $env:JADX_HOME,
    'C:\Tools\jadx',
    'C:\Tools\JADX',
    "$env:ProgramFiles\jadx",
    "$env:ProgramFiles\JADX",
    "${env:ProgramFiles(x86)}\jadx",
    "$env:LOCALAPPDATA\Programs\jadx",
    "$env:USERPROFILE\scoop\apps\jadx\current",
    "$env:ChocolateyInstall\lib\jadx\tools",
    "$env:ChocolateyInstall\bin"
) | Where-Object { $_ }

foreach ($root in $roots) {
    foreach ($base in @($root, (Join-Path $root 'bin'))) {
        $jadxCandidates += Join-Path $base 'jadx.bat'
        $jadxCandidates += Join-Path $base 'jadx.cmd'
        $jadxCandidates += Join-Path $base 'jadx.exe'
        $jadxGuiCandidates += Join-Path $base 'jadx-gui.bat'
        $jadxGuiCandidates += Join-Path $base 'jadx-gui.cmd'
        $jadxGuiCandidates += Join-Path $base 'jadx-gui.exe'
    }
}

$jadx = $jadxCandidates | Select-Object -Unique | Where-Object { Test-Path -LiteralPath $_ -PathType Leaf } | Select-Object -First 1
$jadxGui = $jadxGuiCandidates | Select-Object -Unique | Where-Object { Test-Path -LiteralPath $_ -PathType Leaf } | Select-Object -First 1
$java = (Get-Command java -CommandType Application -ErrorAction SilentlyContinue | Select-Object -First 1).Source

if (-not $jadx) {
    throw 'JADX CLI was not found. Install JADX or set JADX_HOME.'
}
if (-not $java) {
    throw 'Java was not found. Install a JRE/JDK and retry.'
}
```

Use `$jadx` and `$jadxGui` instead of assuming that `jadx` is already in `PATH`. If `$jadx` is empty, do not guess a path.

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
