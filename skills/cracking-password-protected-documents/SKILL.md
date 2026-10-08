---
name: cracking-password-protected-documents
description: "Recover the password of encrypted / password-protected Office documents — Word, Excel, PowerPoint (.docx / .doc / .xlsx / .xls / .pptx / .ppt) — and other encrypted files (.zip / .rar / .7z / .pdf). Extracts a crackable hash with office2john and cracks it with John the Ripper (default, CPU) or hashcat (when a GPU is present) using a bundled wordlist plus mask fallback. Use for ANY task where a document/archive is locked, encrypted, asks for a password, cannot be opened, or where you must recover / crack / brute-force / find the password of an Office file, ZIP, RAR, 7z or PDF — including CTF and forensic password-recovery questions."
version: '1.0'
author: honglian
domain: cybersecurity
subdomain: digital-forensics
tags:
- password-cracking
- office
- john-the-ripper
- hashcat
- office2john
- encrypted-documents
- zip
- rar
- pdf
license: Apache-2.0
---

# Cracking Password-Protected Documents

Recover the password of an **encrypted Office document** (Word / Excel / PowerPoint) so its contents can be
examined, and — with the same pipeline — of encrypted **ZIP / RAR / 7z / PDF** files. Applies to forensic
password recovery and to CTF challenges that hand you a locked file.

**Methodology: extract, then exhaust.** A modern Office file stores a *verifier hash* derived from the
password; you cannot reverse it, but you can hash-and-compare candidate passwords until one matches. The whole
job is two moves — (1) pull the crackable hash out of the file with `office2john`, (2) run a wordlist / mask
attack over it with John the Ripper or hashcat. The tools just package that loop; do not hand-roll a Python
brute-forcer or give up because a tool "looks unavailable" before you have run the self-check below.

## Runtime Environment (Important)

This application runs on **Windows**; the `exec` tool uses **PowerShell** syntax.

- The engines are **`john`** (John the Ripper *jumbo*, the default), **`hashcat`** (used only when a GPU is
  present), and **`office2john`** (a Python script that ships inside the John *jumbo* `run/` directory — there
  is **no `.exe` wrapper** for it). A tool invocation itself is platform-neutral (`john --format=office <hash>`
  is the same everywhere); only loops / pipes / redirection follow PowerShell.
- **Self-check before you start.** On this product `exec` prepends the app's `tools\` directory (and each of its
  first-level subdirectories) to PATH, so `john` and `hashcat` resolve by bare name whenever they are bundled —
  even if a bare shell would not find them:
  ```powershell
  Get-Command john -ErrorAction SilentlyContinue     # John the Ripper jumbo binary (required)
  Get-Command uv   -ErrorAction SilentlyContinue     # Python runner for office2john.py (required)
  Get-Command hashcat -ErrorAction SilentlyContinue  # optional GPU cracker
  ```
  If **`john` or `uv` is genuinely missing** (`Get-Command` returns nothing), the cracking environment is **not
  ready** — report *"password-cracking environment is not ready (john/uv not on PATH)"* and stop. **Do not** fall
  back to Linux commands (`sha256sum`, `hashcat.bin`, `/tmp/...`) or silently pretend the file is unbreakable.
- **`office2john` is a `.py`, not an exe — locate it via `john`.** PATH only resolves the exe. Find the John
  directory from `john.exe`, then run the script with `uv` (bundled, on PATH). `office2john` is essentially
  stdlib, so `uv run` needs no network — but offline it still needs a Python interpreter (the app ships one that
  `uv` finds); if `uv` is somehow unavailable yet a system `python` exists, `python "$johnDir\office2john.py"`
  works too:
  ```powershell
  $johnDir = Split-Path (Get-Command john).Source     # ...\tools\john
  uv run "$johnDir\office2john.py" .\secret.docx
  ```
- **Use a large timeout for cracking.** A wordlist or mask run can take many minutes — pass a large `exec`
  timeout (e.g. `600000` ms). The default 30 s will kill the crack mid-run and lose progress.

> ⚠️ **Forensic integrity**: hash the original document first (`Get-FileHash`), then read it **in place** (office2john
> never writes to the document — no copy needed), and write every artifact (`.hash` files, potfiles, cracked output)
> into your firmament **workspace** directory — never into the source evidence directory. Never modify the evidence
> original.

## When to Use

- A Word / Excel / PowerPoint file (`.docx .doc .xlsx .xls .pptx .ppt`) is password-protected / encrypted and
  you must recover the password to read it.
- Any file asks for a password, "cannot be opened", or is reported as encrypted — including `.zip .rar .7z .pdf`.
- A forensic case or CTF task asks you to **crack / recover / brute-force / find** a document or archive password.

## Workflow

The examples use a placeholder case directory `C:\cases\case-01` and write `.hash` files into it. **On this
product, substitute your firmament workspace directory** (a `scratch/` subfolder is ideal for the intermediate
`.hash` / potfiles). Treat the source document as read-only evidence.

### Step 0: Forensic integrity

```powershell
Get-FileHash .\secret.docx -Algorithm SHA256   # record the original hash
```

office2john only **reads** the document, and john/hashcat crack the extracted `.hash` file — never the doc itself — so
analyze the original **in place**; there is no need to copy it. Write the `.hash`, potfiles, and cracked output into your
workspace (a `scratch\` subfolder).

### Step 1: Extract the hash with office2john

`office2john` reads the encrypted document and prints a crackable hash line of the form
`secret.docx:$office$*2013$*...`. Locate the script via `john`, then run it with `uv`:

```powershell
$johnDir = Split-Path (Get-Command john).Source
$doc     = '.\secret.docx'                          # the original evidence, read in place

# Full line (filename:hash) — John the Ripper consumes this as-is:
uv run "$johnDir\office2john.py" $doc | Set-Content C:\cases\case-01\secret.hash
Get-Content C:\cases\case-01\secret.hash
```

If office2john prints nothing / errors that the file is not encrypted, the document is **not** password-protected
— open it directly. If it reports a missing dependency (rare — it is essentially stdlib; legacy OLE `.doc`/`.xls`
can want `olefile`), retry with `uv run --with <dep> "$johnDir\office2john.py" $doc` — which only succeeds if that
dep is already cached offline.

If office2john dies with **`AttributeError: 'ElementTree' object has no attribute 'getiterator'`** (or
`getchildren`), that is a **Python 3.9+ incompatibility** in this 2019 script — `uv` provisions modern Python
(3.13), which removed those ElementTree methods; the `getiterator` one is on the Office **2013+** (agile) parsing
path, so it hits the most common case. The shipped bundle should already carry the patch; if this copy does not,
self-recover: copy the script into `scratch\`, replace `getiterator(` → `iter(` (and any `getchildren(x)` →
`list(x)`), and run the patched copy:

```powershell
$fix = 'C:\cases\case-01\office2john.py'
Copy-Item "$johnDir\office2john.py" $fix
(Get-Content $fix) -replace '\.getiterator\(', '.iter(' | Set-Content $fix
uv run $fix $doc
```

### Step 2: Pick the cracker — probe for a *discrete* GPU

Default to **john** (CPU, rock-solid). Switch to **hashcat** only when the machine has a **discrete** GPU
(NVIDIA, AMD Radeon RX, Intel Arc) — that is where hashcat's big speed-up comes from. An **integrated** GPU
(Intel HD / UHD / Iris, or an AMD APU's built-in Radeon) is barely faster than the CPU for the slow Office KDFs
and can be flaky, so **treat an iGPU like no GPU and stay on john.**

> ⚠️ **hashcat must run from its own install directory.** It resolves `OpenCL\` / `kernels\` / `modules\`
> **relative to the current directory** (not to the .exe), with no override flag — run it from anywhere else and
> even `hashcat -I` dies with `./OpenCL/: No such file or directory`. So for **every** hashcat call (probe,
> crack, mask): `cd` into its folder (located via `hashcat` on PATH) and pass **absolute** hash / wordlist /
> potfile paths.

Probe, and classify discrete-vs-integrated automatically:

```powershell
$hcDir = Split-Path (Get-Command hashcat).Source        # ...\tools\hashcat
$info  = & { Push-Location $hcDir; try { hashcat -I 2>&1 } finally { Pop-Location } } | Out-String
$info   # also read the full device inventory yourself

# Discrete GPU if EITHER a CUDA/HIP backend block is present (those backends only target discrete NVIDIA/AMD),
# OR a GPU device reports dedicated VRAM (Memory.Unified: 0). Integrated GPUs report Memory.Unified: 1.
$discrete = ($info -match '(?m)^\s*(CUDA|HIP)\s+Info:') -or ($info -match 'Memory\.Unified.*?:\s*0')
if ($discrete) { 'discrete GPU -> hashcat (Step 3b)' } else { 'integrated / CPU only -> john (Step 3a)' }
```

- **`discrete GPU`** → **hashcat** (Step 3b, orders of magnitude faster). If the box has *both* a discrete GPU and
  an iGPU, hashcat uses all GPU devices by default; to pin the fast one, read its `Backend Device ID` from the
  `-I` output and add `-d <id>`.
- **otherwise** (only an iGPU, only a CPU device, or `No devices found`) → **john** (Step 3a). This is the normal
  offline-forensics path; no discrete GPU is required to proceed.

### Step 3a: Crack with John the Ripper (default, CPU)

`--format=office` auto-detects the 2007 / 2010 / 2013+ agile variants; for legacy 97–2003 files use
`--format=oldoffice`.

```powershell
# Re-derive $johnDir here — each exec runs in a fresh PowerShell, so variables do not carry across steps.
$johnDir  = Split-Path (Get-Command john).Source                       # ...\tools\john
# Bundled curated wordlist sits at tools\wordlists\forensic.txt — ONE level up from tools\john:
$wordlist = Join-Path (Split-Path $johnDir) 'wordlists\forensic.txt'
$johnList = Join-Path $johnDir 'password.lst'                          # John's own bundled list (next to john.exe)
if (-not (Test-Path $wordlist)) { $wordlist = $johnList }              # fall back to John's list if the curated one is absent
$pot = 'C:\cases\case-01\john.pot'                                     # keep the potfile in the workspace, not next to the binary

john --format=office --pot=$pot --wordlist=$wordlist C:\cases\case-01\secret.hash
john --format=office --pot=$pot --wordlist=$johnList C:\cases\case-01\secret.hash   # also try John's built-in list

# Retrieve the recovered password (John caches cracked results in the potfile above):
john --show --format=office --pot=$pot C:\cases\case-01\secret.hash
```

### Step 3b: Crack with hashcat (when a GPU is present)

hashcat wants **only the hash** (`$office$...`), not the `filename:` prefix — strip it. Choose `-m` by the hash
prefix that office2john emitted:

```powershell
# strip the "filename:" prefix that office2john adds — hashcat wants only the $office$... hash.
# Cut everything before the first "$" (robust even if the label contains a drive-letter colon):
(Get-Content C:\cases\case-01\secret.hash) -replace '^.*?(?=\$)', '' | Set-Content C:\cases\case-01\secret.hc

$johnDir  = Split-Path (Get-Command john).Source
$wordlist = Join-Path (Split-Path $johnDir) 'wordlists\forensic.txt'
if (-not (Test-Path $wordlist)) { $wordlist = Join-Path $johnDir 'password.lst' }

# hashcat runs from its own dir (see Step 2). Every file is ABSOLUTE, so cwd = $hcDir does not break them.
$hcDir = Split-Path (Get-Command hashcat).Source
$hash  = 'C:\cases\case-01\secret.hc'
$pot   = 'C:\cases\case-01\hashcat.potfile'   # absolute — potfile stays in the workspace
Push-Location $hcDir
try {
  hashcat -m 9600 -a 0 --potfile-path=$pot $hash $wordlist   # -a 0 = wordlist attack (add --force if it rejects a CPU-only device)
  hashcat -m 9600 --show --potfile-path=$pot $hash           # print the cracked password
} finally { Pop-Location }
```

| office2john hash prefix | Office version | hashcat `-m` |
|---|---|---|
| `$office$*2007$` | 2007 | 9400 |
| `$office$*2010$` | 2010 | 9500 |
| `$office$*2013$` (also 2016 / 2019 / 365, agile) | 2013+ | 9600 |
| `$oldoffice$*0$` / `*1$` | 97–2003 (MD5 + RC4) | **9700** (9710/9720 = collider variants, not plain recovery) |
| `$oldoffice$*3$` / `*4$` | 97–2003 (SHA1 + RC4) | **9800** (9810/9820 = collider variants, not plain recovery) |

(John's `--format=office` / `--format=oldoffice` does this selection for you; the table only matters on the
hashcat path.)

### Step 4: When the plain wordlist misses — climb the escalation ladder

**You do not need to know the password's format up front — do not try to.** Real passwords are not uniformly
distributed; they cluster in dictionary words, dates, names+digits and common patterns. So when the format is
unknown (the normal forensic case) the winning move is not "pick digits vs letters vs a mask" — it is to run this
ladder **top-down and stop on the first hit**. Rules (Rung 1) and incremental / Markov (Rung 3) order the whole
space by real-world frequency for you, spanning every length and character class automatically; only reach for a
hand-built mask when the case hands you a structural lead (Rung 0) — guessing a mask with no lead is just a
slower brute force.

Steps 3a/3b ran the **plain** `tools\wordlists\forensic.txt` (~80k common passwords, pinyin, dates) and John's
`password.lst`. When those miss, do **not** jump straight to a naked `?a` brute force — it is hopeless against
the slow Office KDF (2013+ runs SHA-512 ×100k iterations, so a CPU manages only hundreds–a few thousand
guesses/s; `?a?a?a?a?a?a?a?a` = 95⁸ ≈ 6.6×10¹⁵ would take millennia). Instead climb this ladder — **cheapest /
highest-hit first**. Everything below is **already bundled** (`john.conf` rule + incremental sections, the `.chr`
stat files, `hashcat\rules\`, `hashcat\masks\`); no extra downloads. Re-derive `$johnDir` / `$wordlist` / `$pot`
in each `exec` (fresh PowerShell — variables do not carry across calls).

**Rung 0 — Targeted candidates from the case (forensics' biggest edge; try FIRST).** A real suspect's password
is usually *their own* data: phone number, birthday (`YYYYMMDD` / `YYMMDD`), name pinyin, a company name, or a
password already recovered from another artifact in the case. Build a tiny list from those known facts (or a
narrow mask — e.g. the exact 11-digit phone) and run it before anything generic. A **known** phone number is one
candidate, not a 1.8-billion keyspace.

```powershell
$pot = 'C:\cases\case-01\john.pot'
Set-Content C:\cases\case-01\leads.txt @('13800138000','19900101','zhangsan','ZhangSan1990')  # case-specific facts
john --format=office --pot=$pot --wordlist=C:\cases\case-01\leads.txt C:\cases\case-01\secret.hash
```

**Rung 1 — Rule mutation (the single biggest lever, and it was missing).** Rules turn each dictionary word into
human-style variants (`password`→`Password1`, `p@ssw0rd`, `password2024`). This is exactly what catches "a word
that is *close to* the dictionary but not literally in it" — the common reason a crack stalls. Run cheap → broad:

```powershell
$johnDir  = Split-Path (Get-Command john).Source
$wordlist = Join-Path (Split-Path $johnDir) 'wordlists\forensic.txt'
$pot      = 'C:\cases\case-01\john.pot'
john --format=office --pot=$pot --wordlist=$wordlist --rules=best64 C:\cases\case-01\secret.hash  # fast: top mutations
john --format=office --pot=$pot --wordlist=$wordlist --rules=Jumbo  C:\cases\case-01\secret.hash  # much broader (slower)
```
hashcat path (discrete GPU), run from `$hcDir` with absolute paths (Step 2):
`hashcat -m 9600 -a 0 <abs .hc> <abs wordlist> -r rules\best66.rule` then `-r rules\dive.rule`.

**Rung 2 — Hybrid: word + digits / year** (`名字2024`, `公司123`, `pinyin888`). hashcat only; John approximates
it via `--rules=Jumbo` (which already appends digit strings):
```powershell
$hcDir = Split-Path (Get-Command hashcat).Source
Push-Location $hcDir; try {
  hashcat -m 9600 -a 6 C:\cases\case-01\secret.hc $wordlist ?d?d?d?d   # word + up to 4 digits
  hashcat -m 9600 -a 7 C:\cases\case-01\secret.hc ?d?d?d?d $wordlist   # up to 4 digits + word
} finally { Pop-Location }
```

**Rung 3 — Statistical brute force (the "format-unknown" engine; smarter than a naked mask).** John's incremental
mode walks the keyspace in **frequency order** from the bundled `.chr` stats — every length and character class,
most-probable first — so you never have to declare the format. It hits far earlier than a left-to-right `?a` sweep
and runs until cracked or stopped, so time-box it (large `exec` timeout, then read the potfile). Go cheap → broad:
numeric first (a huge cluster — most 6-/8-digit passwords are dates), then the full printable space:
```powershell
john --format=office --pot=$pot --incremental=Digits C:\cases\case-01\secret.hash  # numeric PIN / date, any length
john --format=office --pot=$pot --incremental=ASCII  C:\cases\case-01\secret.hash  # everything, frequency-ordered
```
> **Numeric cliff (why 6 digits crack instantly but 7 crawl):** the bundled list holds ~37k six-digit and ~32k
> eight-digit entries — they are **dates** — but almost no seven-digit (7 digits has no date/PIN shape). So a
> 6-/8-digit date is a wordlist hit in seconds, while a 7-digit number drops to a full 10⁷ brute force. Expected,
> not a bug: `--incremental=Digits` catches any non-random 7-digit fast; a uniform-random 7-digit needs the whole
> space (~30 min at ~5k c/s on CPU, seconds on a discrete GPU). Do **not** "fix" it by stuffing every 7-digit
> number into the wordlist — the KDF runs per candidate either way, so a mask is the right tool, not a bloated list.

**Rung 4 — Ordered mask sets / one targeted mask.** hashcat ships `masks\rockyou-1-60.hcmask` …
`rockyou-7-2592000.hcmask`: mask collections **pre-sorted by how often they crack real passwords** — use them
instead of hand-guessing masks. Or run a single mask the case implies (e.g. 8-digit date):
```powershell
Push-Location $hcDir; try { hashcat -m 9600 -a 3 C:\cases\case-01\secret.hc masks\rockyou-2-1800.hcmask } finally { Pop-Location }
john --format=office --pot=$pot --mask='?d?d?d?d?d?d?d?d' C:\cases\case-01\secret.hash   # john path, YYYYMMDD
```
> ⚠️ The seconds in those `.hcmask` names (60 … 2592000) are calibrated for **fast** hashes on a **GPU** — they
> do **not** predict wall-clock against the slow Office KDF. The *ordering* still helps (most-likely masks first),
> but on CPU only the low-numbered sets (`rockyou-1` / `-2`) finish in practical time; bigger keyspaces need a
> discrete GPU. Mask tokens: `?d`=digit, `?l`=lower, `?u`=upper, `?a`=all printable — each `?a` position ×95.

**Rung 5 — Bigger wordlist (the one real bundling gap).** `tools\wordlists\` ships **only** `forensic.txt`. If
rungs 0–4 all miss, the fix is a broader list (`rockyou.txt`, or a Chinese phone-segment / name-pinyin+birthday
list) dropped into `tools\wordlists\`, then re-run rungs 0–2 over it. That is a packaging/environment change —
surface it like a missing engine; do not try to brute-force around it.

### Step 5: Report honestly (and know where CPU stops)

- **Cracked** → report the recovered plaintext **verbatim**, and note which rung / engine found it (e.g. "hashcat,
  forensic.txt + best66 rules").
- **Not cracked** → say so plainly and **list the ladder you climbed** (which rungs, which lists / rules / masks),
  so the reader sees the actual coverage. Then give the **specific** next step, not "try harder":
  - **no discrete GPU** and you stopped at rung 3/4 → the remaining keyspace (long/complex passwords, the full
    phone-number space, `?a`⁸) is **GPU-scale**; recommend re-running on an NVIDIA/AMD box via hashcat.
  - **rungs 0–2 exhausted** forensic.txt + rules → recommend a **larger wordlist** (rung 5) or **more case leads**
    (rung 0) — the two levers that actually move the needle against a slow KDF.
- **Never fabricate a password** and never claim "uncrackable". An honest *"not recovered with the bundled
  wordlist + rules + masks; needs a GPU / a larger list / more case-specific leads"* is the correct terminal state.

## Generalizing to ZIP / RAR / 7z / PDF

The exact same `*2john → crack` pipeline works for other encrypted containers — the companion extractors live in
the **same flattened** `tools\john\` directory. Mind what each needs: `zip2john.exe` / `rar2john.exe` are **native
exes** and `office2john.py` runs via `uv` — these work out of the box. **But in this bundle `pdf2john.pl` and
`7z2john.pl` are Perl scripts and Perl is NOT bundled** (there is no `pdf2john.py` / `7z2john.py` here), so **PDF
and 7z hash-extraction are an environment gap** — install Perl to run them, or surface the gap the way you would a
missing engine; don't silently give up. Extract the hash, then crack with john (auto-detects the format) or
hashcat (`-m` by the hash prefix):

```powershell
$johnDir = Split-Path (Get-Command john).Source   # re-derive: variables do not carry across exec calls
& "$johnDir\zip2john.exe" .\archive.zip | Set-Content C:\cases\case-01\zip.hash   # ZIP  → works (native exe)
& "$johnDir\rar2john.exe" .\archive.rar | Set-Content C:\cases\case-01\rar.hash   # RAR  → works (native exe)
# PDF / 7z extraction needs Perl (NOT bundled):
#   perl "$johnDir\pdf2john.pl" .\locked.pdf | Set-Content C:\cases\case-01\pdf.hash   # requires a Perl install

john C:\cases\case-01\zip.hash        # John auto-detects zip/rar format — no --format needed
john --show C:\cases\case-01\zip.hash
```

Common hashcat modes if you take the GPU path (or confirm via `hashcat --help`):

| Container | hashcat `-m` |
|---|---|
| ZIP (WinZip AES) | 13600 |
| PKZIP (legacy ZIP) | 17200 / 17210 / 17220 / 17225 / 17230 |
| 7-Zip | 11600 |
| RAR3 (`-hp`) | 12500 |
| RAR5 | 13000 |
| PDF 1.1–1.3 (Acrobat 2–4, RC4 40-bit) | 10400 |
| PDF 1.4–1.6 (Acrobat 5–8) | 10500 |
| PDF 1.7 L3 (Acrobat 9) | 10600 |
| PDF 1.7 L8 (Acrobat 10–11) | 10700 |

## Pitfalls

1. **Locate `office2john` via `john` — never hard-code a path.** It is a `.py` with no exe wrapper; `where.exe
   john` / `Get-Command john` gives you its directory in both dev and packaged builds.
2. **hashcat needs the bare hash; John takes the whole `filename:hash` line.** Feeding hashcat the prefix, or
   feeding it a `$oldoffice$` hash under the wrong `-m`, produces "No hashes loaded" / "Token length exception".
3. **hashcat only runs from its own install directory.** It finds `OpenCL\`/`kernels\`/`modules\` relative to the
   current directory, so every hashcat call — including `-I` — must be wrapped `Push-Location (Split-Path
   (Get-Command hashcat).Source)` … `Pop-Location`, with **absolute** hash/wordlist/potfile paths. Run it from
   elsewhere and it dies with `./OpenCL/: No such file or directory`. john has no such constraint.
4. **Default to john; switch to hashcat only for a *discrete* GPU** (NVIDIA / AMD RX / Intel Arc — a `CUDA`/`HIP`
   block, or a GPU with `Memory.Unified: 0`). An integrated GPU (`Memory.Unified: 1`; Intel HD/UHD/Iris) barely
   beats the CPU for the slow Office KDFs — keep it on john. (CPU-only OpenCL devices also need `--force`.)
5. **If `john` is not on PATH, stop and report** — do not silently claim the file is uncrackable or improvise a
   Python cracker. Cracking is only as good as the wordlist; missing engines is an environment problem to surface.
6. **Use a `600000` ms timeout** for the crack step, and keep intermediate `.hash` / potfiles in your workspace,
   not in the evidence directory. Password-cracking binaries are commonly AV-flagged; that is expected here.
