# DSH Forensics Migration

This repository is a forensic-only migration bundle for a Windows DSH workstation. Keep it private unless every included skill has been checked for redistribution rights.

It contains digital-forensics skills, environment notes, and a bootstrap script. It intentionally does not contain DSH credentials, sessions, caches, evidence images, unrelated personal skills, or vendor-restricted FireEye/Honglian executables.

## Layout

- `skills/`: forensic skills copied from the source workstation.
- `env/`: tool and runtime checklist.
- `vendor/`: instructions for adding authorized vendor components locally.
- `bootstrap.ps1`: installs the bundle into the current Windows user profile.

The bundle contains only the skills listed in `manifests\forensic-allowlist.txt`. Runtime/system skills from `.codex\skills` and unrelated user skills are intentionally not copied.

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
