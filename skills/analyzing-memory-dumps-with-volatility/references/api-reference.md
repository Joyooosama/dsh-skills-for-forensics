# API Reference: Volatility 3 + pypykatz (Windows Memory Forensics)

> _Adapted from the **Anthropic Cybersecurity Skills** project (Apache-2.0; see `../LICENSE`). Merged from two upstream
> skills' references and rewritten for Windows: `vol3`→`vol`, Linux paths removed._

The Volatility 3 CLI is `vol`. In this app, `vol.exe` is user-provided (pip or standalone) and the environment detector
injects its directory into the `exec` PATH. `pypykatz` must be present on `PATH` for LSASS credential parsing. Commands are
shown for **Windows / PowerShell**.

## Core Syntax

```powershell
vol -f <image> <plugin> [options]
vol -f .\memory.raw --help            # list all plugins
vol -f .\memory.raw <plugin> --help   # plugin-specific help
vol --version
```

## Windows Plugins

### Process Analysis
| Plugin | Purpose |
|--------|---------|
| `windows.pslist` | List active (linked) processes |
| `windows.pstree` | Process tree (parent-child) |
| `windows.psscan` | Pool-tag scan (finds hidden/unlinked processes) |
| `windows.cmdline` | Process command-line arguments |
| `windows.envars` | Process environment variables |
| `windows.handles` | Process handle table |

### Code Injection Detection
| Plugin | Purpose |
|--------|---------|
| `windows.malfind` | Detect injected code (RWX memory + PE headers in non-image VADs) |
| `windows.hollowfind` | Detect process hollowing |
| `windows.dlllist` | List loaded DLLs per process |
| `windows.ldrmodules` | Detect unlinked DLLs |

### Network
| Plugin | Purpose |
|--------|---------|
| `windows.netscan` | List network connections and listeners |
| `windows.netstat` | Network connections (older Windows) |

### Kernel / Rootkit
| Plugin | Purpose |
|--------|---------|
| `windows.ssdt` | System Service Descriptor Table hooks |
| `windows.callbacks` | Kernel callback registrations |
| `windows.driverscan` | Scan for driver objects |
| `windows.modules` | Loaded kernel modules |

### Credentials
| Plugin | Purpose |
|--------|---------|
| `windows.hashdump` | Dump SAM local-account NTLM hashes |
| `windows.cachedump` | Dump cached domain credentials (DCC2) |
| `windows.lsadump` | Dump LSA secrets (service-account passwords) |

### Registry
| Plugin | Purpose |
|--------|---------|
| `windows.registry.printkey` | Print registry key values |
| `windows.registry.hivelist` | List registry hives |

### File System
| Plugin | Purpose |
|--------|---------|
| `windows.filescan` | Scan for file objects |
| `windows.dumpfiles` | Extract files from memory |
| `windows.memmap` | Dump process memory (used to extract LSASS) |

### YARA Scanning
```powershell
vol -f .\memory.raw yarascan.YaraScan --yara-file .\rules.yar
vol -f .\memory.raw yarascan.YaraScan --yara-file .\rules.yar --pid 2184
vol -f .\memory.raw yarascan.YaraScan --yara-rules 'rule Test { strings: $s = "cmd.exe" condition: $s }'
```

### Timeline
```powershell
vol -f .\memory.raw timeliner.Timeliner --output-file .\analysis\timeline.csv
```

## Output Options
```powershell
vol -f .\memory.raw windows.pslist --output csv  | Out-File .\analysis\processes.csv
vol -f .\memory.raw windows.pslist --output json | Out-File .\analysis\processes.json
vol -f .\memory.raw windows.malfind --dump --pid 2184
```

## pypykatz (LSASS Credential Extraction)

`pypykatz` is a Python implementation of Mimikatz; it parses an LSASS minidump or a raw memory image.

```powershell
pypykatz lsa minidump .\analysis\lsass.dmp                 # human-readable, from an LSASS dump
pypykatz lsa minidump .\analysis\lsass.dmp -j              # JSON to stdout (parse with ConvertFrom-Json)
pypykatz lsa minidump .\analysis\lsass.dmp -k .\analysis\kerberos\   # export .kirbi tickets
pypykatz rekall .\memory.raw                               # parse a full raw memory image directly
```

Recovered credential types: NTLM hashes (`msv_creds`), Kerberos tickets/passwords (`kerberos_creds`), WDigest plaintext
passwords (`wdigest_creds`), DPAPI master keys (`dpapi_creds`).

### pypykatz JSON shape (per logon session)
```json
{
  "logon_sessions": {
    "<id>": {
      "username": "admin", "domainname": "CORP", "sid": "S-1-5-...",
      "msv_creds":     [{ "NThash": "...", "LMHash": "..." }],
      "kerberos_creds":[{ "password": "...", "tickets": [{ "server": "...", "enc_type": "..." }] }],
      "wdigest_creds": [{ "password": "..." }],
      "dpapi_creds":   [{ "masterkey": "..." }]
    }
  }
}
```

## Offline Cracking / Advanced (separate install)

| Tool | Purpose |
|------|---------|
| `hashcat` / John the Ripper | Crack recovered NTLM and DCC2 hashes |
| Mimikatz | Windows credential tool (offline against dumps) |
| Impacket `secretsdump.py` | Extract secrets from SAM/SYSTEM/SECURITY |
| Rubeus | Kerberos ticket manipulation |

## Memory Acquisition (Windows)

| Tool | Command |
|------|---------|
| WinPmem | `winpmem_mini_x64.exe memdump.raw` |
| DumpIt | `DumpIt.exe` (interactive) |

## Symbols

The Volatility 3 environment card only proves `vol.exe` was found and injected into the `exec` PATH; it does not prove
symbol readiness for a specific memory image. Verify symbols at runtime with:

```powershell
vol -f <image> windows.info
```

With network access, `vol` downloads missing ISF symbols automatically. Offline investigations must pre-stage matching
symbols under `%APPDATA%\volatility3\symbols`. A wrong or missing symbol table is the most common cause of plugin failure
or incorrect output.
