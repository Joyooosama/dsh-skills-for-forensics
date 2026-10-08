---
name: analyzing-memory-dumps-with-volatility
description: Use when analyzing Windows memory dumps or RAM captures with Volatility 3 (`vol`) for process, injection, rootkit, network, YARA, timeline, or LSASS credential exposure work with pypykatz.
domain: cybersecurity
subdomain: digital-forensics
tags:
- malware
- memory-forensics
- Volatility
- RAM-analysis
- incident-response
- credential-extraction
- pypykatz
- password-hashes
mitre_attack:
- T1055
- T1003
- T1059
- T1620
- T1005
- T1074
- T1070
- T1119
version: 1.0.0
author: mahipal
license: Apache-2.0
nist_csf:
- DE.AE-02
- RS.AN-03
- ID.RA-01
- DE.CM-01
- RS.AN-01
- RS.MA-01
---

# Analyzing Memory Dumps with Volatility

Memory forensics for Windows RAM captures. **Part 1** triages a compromised image — processes, injected code, network
activity, rootkit artifacts, YARA hits, timeline. **Part 2** escalates to full credential recovery for post-breach impact
assessment — SAM/LSA/cached hashes plus NTLM / Kerberos / WDigest / DPAPI secrets from LSASS.

**Do not use** for disk-image analysis — use Autopsy, FTK, or Sleuth Kit for disk forensics.

## Runtime Environment (Important)

This application runs on **Windows**; the `exec` tool uses **PowerShell** syntax.

- The Volatility 3 CLI is **`vol`** (not `vol3`/`vol2`) and the credential tool is **`pypykatz`**. Volatility 3 is
  user-provided: the environment detector locates `vol.exe` from `tools\`, Python `Scripts\`, or `PATH`, then injects that
  directory into the `exec` PATH. `pypykatz` has no automated detector yet; verify it separately before LSASS credential
  extraction. A tool invocation itself is platform-neutral (`vol -f <image> <plugin>`); only loops / pipes / redirection
  follow PowerShell.
- **Self-check before the relevant phase.** Part 1 only requires `vol`; full Part 2 credential extraction requires
  `pypykatz` in addition to `vol`. Do not block triage just because `pypykatz` is absent. Do not invent paths, do not fall
  back to `vol3` or Linux commands:
  ```powershell
  Get-Command vol -ErrorAction SilentlyContinue
  vol --version
  # Before Part 2 only:
  Get-Command pypykatz -ErrorAction SilentlyContinue
  ```
  If `vol` is not found, report: *"Memory-forensics environment is not ready (`vol` not on PATH). Check Volatility 3 status
  under **Settings → 解析工具检测** (Volatility 3 card) — it shows whether `vol` is installed and where it resolves from.
  Prepare the environment before memory analysis can run."* and stop.
  If Part 2 needs `pypykatz` and it is not found, report: *"Credential extraction is not ready (`pypykatz` not on PATH).
  Volatility 3 triage and native hashdump/lsadump/cachedump can still run, but install or expose `pypykatz` before LSASS
  credential parsing."* and skip the pypykatz steps.
- **Use a large timeout.** Plugins over multi-GB images take minutes — pass a large `exec` timeout (e.g. `600000` ms). The
  default 30 s will kill the analysis mid-run.
- The Settings -> 解析工具检测 Volatility 3 card only proves `vol.exe` was located and `vol` can be called by the agent; it
  does **not** prove symbol readiness for this memory image. Verify symbols at runtime with `vol -f <image> windows.info`.
  With network access, `vol` fetches missing ISF symbols automatically. Offline investigations must pre-stage matching
  symbols under `%APPDATA%\volatility3\symbols`. A wrong/missing symbol table is the #1 cause of plugin failures or garbage
  output.

Need plugin names, options, or pypykatz JSON shape? Read `references/api-reference.md` in this skill directory.

> ⚠️ **Forensic integrity**: hash the original first (`Get-FileHash`), analyze the dump **in place** (read-only — do NOT
> copy a multi-GB image into the workspace; `vol` never writes to it), and write every dump/export to a dedicated output
> directory in your workspace. Never modify the evidence original.

## When to Use

- A compromised system's RAM has been captured and needs forensic analysis for malware artifacts.
- Detecting fileless / memory-resident malware that leaves no persistent disk artifacts.
- Identifying process injection, DLL injection, or process hollowing.
- Analyzing rootkit activity that hides from disk-based tools.
- Determining what credentials an attacker could access after a breach (scope of compromise, accounts to reset).
- Investigating lateral movement and pass-the-hash / pass-the-ticket (NTLM hashes, Kerberos tickets).
- Recovering encryption keys, tokens, or cloud credentials from process memory.

## Prerequisites

- A memory dump acquired from the target (WinPmem / DumpIt), in raw, crash, or ELF form. Dumps can be 4–64 GB — analyze
  them in place (do NOT copy into the workspace); ensure disk space for the dumped artifacts only.
- The forensic environment prepared (`vol` for Part 1; `pypykatz` only for full Part 2 credential extraction; see Runtime
  Environment).
- The source OS version, for correct symbol selection.
- YARA rules, for signature scanning of memory (Part 1, Step 6).
- Understanding of Windows authentication (NTLM, Kerberos, DPAPI) for interpreting Part 2 output.
- Appropriate legal authorization for credential extraction.

## Step 0 · Forensic Integrity

```powershell
Get-FileHash .\memory.raw -Algorithm SHA256          # record the original hash
New-Item -ItemType Directory -Force .\analysis | Out-Null   # dedicated output dir (in your workspace)
```

Record the hash, then analyze the dump **in place** via its absolute path — do NOT copy a multi-GB image into the
workspace; `vol` opens it read-only. Write every artifact under `.\analysis\` (your workspace, not the evidence
directory). Examples below use `.\memory.raw` for brevity — substitute the dump's real absolute path.

---

# Part 1 — Triage & Analysis

### Step 1: Identify the Image

```powershell
vol -f .\memory.raw windows.info     # OS / build / kernel base — runtime symbol-readiness check
vol -f .\memory.raw --help           # list available plugins
```

### Step 2: Enumerate Processes

```powershell
vol -f .\memory.raw windows.pslist           # active (linked) process list
vol -f .\memory.raw windows.pstree           # parent-child tree
vol -f .\memory.raw windows.psscan           # pool-tag scan — finds hidden/unlinked processes
```

Compare `pslist` vs `psscan`: entries present in `psscan` but **not** `pslist` are potentially hidden by a rootkit (DKOM).

```
Suspicious Process Indicators
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
- svchost.exe not spawned by services.exe (wrong parent)
- csrss.exe / lsass.exe with an unusual parent
- Multiple lsass.exe instances (there should be exactly one)
- Misspelled names (scvhost.exe, lssas.exe)
- cmd.exe / powershell.exe spawned by WINWORD.EXE or a browser
- Processes running from %TEMP% / %APPDATA%
- Orphaned processes (parent already terminated)
```

### Step 3: Detect Malicious Code Injection

```powershell
vol -f .\memory.raw windows.malfind                    # RWX regions + PE headers in non-image VADs
vol -f .\memory.raw windows.malfind --dump --pid 2184  # dump injected regions for a PID
vol -f .\memory.raw windows.dlllist --pid 2184         # loaded DLLs per process
vol -f .\memory.raw windows.hollowfind                 # process hollowing (mapped image vs disk)
vol -f .\memory.raw windows.driverscan                 # driver objects (rootkit drivers)
vol -f .\memory.raw windows.modules                    # loaded kernel modules
```

### Step 4: Analyze Network Connections

```powershell
vol -f .\memory.raw windows.netscan                          # all connections + listeners
vol -f .\memory.raw windows.netscan | Select-String "ESTABLISHED"   # only established
```

Cross-reference PIDs with the process list. Suspicious: `svchost.exe` connected to an external IP on a non-standard port; a
GUI app like `notepad.exe` with network connections.

### Step 5: Extract Artifacts

```powershell
vol -f .\memory.raw windows.cmdline                          # process command lines
vol -f .\memory.raw windows.memmap --dump --pid 2184         # dump a process's memory
vol -f .\memory.raw windows.registry.printkey --key "Software\Microsoft\Windows\CurrentVersion\Run"   # persistence
vol -f .\memory.raw windows.filescan | Select-String -Pattern "payload|malware|suspicious"
vol -f .\memory.raw windows.dumpfiles --virtaddr 0xFA8001234560   # extract a file from memory
```

### Step 6: Scan Memory with YARA

```powershell
vol -f .\memory.raw yarascan.YaraScan --yara-file .\malware_rules.yar
vol -f .\memory.raw yarascan.YaraScan --yara-file .\malware_rules.yar --pid 2184
vol -f .\memory.raw yarascan.YaraScan --yara-rules 'rule FindC2 { strings: $s1 = "gate.php" condition: $s1 }'
```

### Step 7: Timeline

```powershell
vol -f .\memory.raw timeliner.Timeliner --output-file .\analysis\timeline.csv
vol -f .\memory.raw windows.pslist --output csv | Out-File .\analysis\processes.csv
vol -f .\memory.raw windows.netscan --output csv | Out-File .\analysis\network.csv
```

---

# Part 2 — Credential Extraction

Run after triage when you need to assess credential compromise. Volatility recovers stored hashes; **pypykatz** recovers the
live LSASS secrets (NTLM, Kerberos, WDigest plaintext, DPAPI).

### Step 1: Locate LSASS

```powershell
vol -f .\memory.raw windows.pslist | Select-String "lsass"
# note the LSASS PID (e.g. 684) for the dumps below
```

### Step 2: Volatility-Native Credential Dumps

```powershell
vol -f .\memory.raw windows.hashdump  | Tee-Object .\analysis\hashdump.txt    # SAM local-account NTLM hashes
vol -f .\memory.raw windows.lsadump   | Tee-Object .\analysis\lsadump.txt     # LSA secrets (service passwords)
vol -f .\memory.raw windows.cachedump | Tee-Object .\analysis\cachedump.txt   # DCC2 cached domain creds
```

```
hashdump format:
User           RID    LM Hash                           NTLM Hash
<account>       <rid>  <lm-hash>                         <ntlm-hash>
```

### Step 3: Dump LSASS Process Memory

```powershell
vol -f .\memory.raw windows.memmap --pid 684 --dump -o .\analysis\lsass\
Move-Item .\analysis\lsass\pid.684.dmp .\analysis\lsass.dmp     # rename for pypykatz
```

### Step 4: Extract Credentials with pypykatz

```powershell
pypykatz lsa minidump .\analysis\lsass.dmp | Tee-Object .\analysis\pypykatz.txt   # human-readable
pypykatz rekall .\memory.raw | Tee-Object .\analysis\pypykatz_full.txt            # against the raw image directly
```

For structured parsing, take pypykatz JSON (`-j`) and parse it in PowerShell — **no inline Python heredocs**:

```powershell
$data = pypykatz lsa minidump .\analysis\lsass.dmp -j | ConvertFrom-Json
$data.logon_sessions.PSObject.Properties.Value | ForEach-Object {
  $s = $_
  if ($s.username -and $s.username -ne '(null)') {
    "Session: $($s.domainname)\$($s.username)  (SID $($s.sid))"
    $s.msv_creds     | Where-Object { $_.NThash }  | ForEach-Object { "  NTLM:   $($_.NThash)" }
    $s.wdigest_creds | Where-Object { $_.password } | ForEach-Object { "  WDigest(plaintext): $($_.password)" }
    $s.kerberos_creds| ForEach-Object { $_.tickets } | ForEach-Object { "  Kerberos ticket: $($_.server)" }
    $s.dpapi_creds   | Where-Object { $_.masterkey } | ForEach-Object { "  DPAPI masterkey: $($_.masterkey)" }
  }
}
```

### Step 5: Kerberos Tickets and Token / Cloud-Credential Hunting

```powershell
pypykatz lsa minidump .\analysis\lsass.dmp -k .\analysis\kerberos\    # export .kirbi tickets
Get-ChildItem .\analysis\kerberos\*.kirbi                             # list recovered tickets
```

Hunt auth tokens and cloud keys in memory with YARA (reliable, needs no pre-generated strings file):

```powershell
vol -f .\memory.raw yarascan.YaraScan --yara-rules 'rule CloudCreds {
  strings:
    $aws  = /AKIA[A-Z0-9]{16}/
    $awss = "aws_secret_access_key" nocase
    $auth = "authorization: bearer" nocase
  condition: any of them }'
```

> `windows.strings` can also dump readable strings but requires a strings file generated up front from the image — prefer the
> YARA approach above for targeted IOC/secret hunting.

### Step 6: Credential Compromise Report

Summarize what was recovered and the required actions:

> **TEMPLATE ONLY:** Every angle-bracketed field below must be replaced with a value returned by tools in the current
> investigation. The placeholders and labels below are not findings and must never appear in a real report as evidence.

```
CREDENTIAL COMPROMISE ASSESSMENT
================================
Local NTLM hashes (SAM):    <local-account-count>
Domain NTLM hashes (LSASS): <domain-account-count>
Kerberos tickets:           <tgt-count> TGT, <tgs-count> TGS
Plaintext (WDigest):        <plaintext-count> (<accounts-or-none>)
Cached domain creds (DCC2): <cached-credential-count>
DPAPI master keys:          <dpapi-key-count>
Cloud credentials:          <cloud-credential-count> (<types-or-none>)

Highest privilege exposed: <highest-verified-privilege> (<account-or-none>)

Required actions:
- <action justified by the recovered evidence>
- <additional action or none>
```

---

## Key Concepts

| Term | Definition |
|------|------------|
| **Memory Forensics** | Analysis of volatile RAM to find processes, connections, and in-memory artifacts absent from disk |
| **Process Hollowing** | Creating a suspended legit process, replacing its image with malicious code, then resuming it |
| **Malfind** | Volatility plugin flagging injected code: executable (RWX) regions with PE headers in non-image VADs |
| **VAD** | Virtual Address Descriptor — kernel structure tracking a process's memory regions; anomalies indicate injection |
| **Pool-Tag Scanning** | Finds kernel objects (processes/files/connections) by their pool tags even when unlinked (rootkit-hidden) |
| **Fileless Malware** | Operates entirely in memory with no disk file; only detectable via memory forensics |
| **LSASS** | Windows process managing authentication; holds NTLM/Kerberos/WDigest/DPAPI secrets in memory |
| **NTLM hash** | Hash of a user password usable for authentication (and pass-the-hash) |
| **Kerberos TGT/TGS** | Ticket-Granting Ticket / service ticket; basis of pass-the-ticket and golden/silver tickets |
| **WDigest** | Legacy protocol that kept **plaintext** passwords in LSASS (pre-Win8.1 / when re-enabled) |
| **DPAPI** | Data Protection API; master keys derived from user credentials protect secrets at rest |
| **DCC2** | Domain Cached Credentials — cached domain password hashes for offline logon |

## Tools & Systems

| Tool | Purpose |
|------|---------|
| **Volatility 3 (`vol`)** | Memory forensics framework; triage plugins + `hashdump`/`lsadump`/`cachedump` |
| **pypykatz** | Python Mimikatz; recovers NTLM/Kerberos/WDigest/DPAPI from LSASS dumps or raw images |
| **WinPmem / DumpIt** | Windows memory acquisition (raw dump) |
| **hashcat / John the Ripper** | Offline cracking of recovered NTLM / DCC2 hashes |
| **Mimikatz / Rubeus / Impacket** | Advanced (separate install) — offline LSASS parsing, Kerberos ticket manipulation, secretsdump |

## Common Scenarios

**Fileless malware after an EDR alert** — disk artifacts were wiped, but a pre-reboot dump exists. `windows.pstree` to find
what spawned PowerShell → `windows.malfind` for injected code → dump the suspect process and extract C2 strings →
`windows.netscan` for connections → `windows.cmdline` for executed commands → YARA for known families → then Part 2 to
assess credential exposure.

**Post-breach credential assessment** — go straight to Part 2: `hashdump`/`lsadump`/`cachedump`, dump LSASS, run pypykatz for
all credential types, check for krbtgt / domain-admin material, prioritize resets by privilege.

**Lateral-movement investigation** — extract NTLM hashes and Kerberos tickets (pypykatz) to reconstruct pass-the-hash /
pass-the-ticket activity; correlate recovered accounts with logon events.

**Pitfalls**: wrong symbol table for the OS build (plugin failures / garbage); not comparing `pslist` vs `psscan` (missing
hidden processes); concluding before dumping full process memory (strings may hold extra IOCs); forgetting the large `exec`
timeout on big images.

## Output Format

> **TEMPLATE ONLY:** This block defines structure, not case content. Replace every angle-bracketed field only with values
> returned by tools in the current investigation. These placeholders must never appear in a real report as evidence.

```
MEMORY FORENSICS ANALYSIS REPORT
================================
Dump File:   <dump-file>       OS: <verified-os-and-build>
Dump Size:   <dump-size>       Capture: <capture-tool-and-time-or-unknown>
SHA-256:     <source-sha256>

SUSPICIOUS PROCESSES
PID    PPID    Name            Path              Observed anomaly
<pid>  <ppid>  <process-name>  <process-path>    <observation-or-none>

CODE INJECTION (malfind)
PID <pid> (<process-name>): <address>  <permissions>  <observed-signature>  SHA-256(dump)=<dump-sha256>

NETWORK
PID    Process         Local                      Foreign                    State
<pid>  <process-name>  <local-ip>:<local-port>    <remote-ip>:<remote-port>  <state>

CREDENTIALS (see Part 2 report block above)
YARA: PID <pid> -> <rule-name-or-no-hit> @ <address-or-none>

TIMELINE
<timestamp>  <event supported by a named plugin or artifact>
<timestamp>  <event supported by a named plugin or artifact>
```
