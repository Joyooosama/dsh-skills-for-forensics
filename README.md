# DSH Forensics Migration

This repository is a private migration bundle for a Windows DSH forensic-analysis workstation. Keep it private unless every included skill has been checked for redistribution rights.

It contains user-managed skills, DSH plugin source, environment notes, and a bootstrap script. It intentionally does not contain DSH credentials, sessions, caches, evidence images, or vendor-restricted FireEye/Honglian executables.

## Layout

- `skills/`: user-managed skills copied from the source workstation.
- `plugins/`: DSH plugin source that is safe to migrate.
- `env/`: tool and runtime checklist.
- `vendor/`: instructions for adding authorized vendor components locally.
- `bootstrap.ps1`: installs the bundle into the current Windows user profile.

The bundle contains user-managed skills from `.agents\skills`. Runtime/system skills from `.codex\skills` are intentionally not copied; install those with the target application's normal package mechanism.

## Basic setup

1. Install DSH, Git, Node.js, Python, and the forensic tools listed in `env/tools.txt`.
2. Clone this repository into the target workstation.
3. Run PowerShell as the target user and execute:

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\bootstrap.ps1
```

4. Mount the evidence in FireEye/Honglian and point DSH at the resulting read-only drive or directory.

## Vendor components

Place authorized FireEye/Honglian skill folders and CLI binaries under `vendor-drop/` locally. That directory is ignored by Git and must not be pushed to a public repository.
