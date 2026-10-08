---
name: analyzing-network-traffic-with-wireshark
description: 'Read and analyze network packet captures (.pcap / .pcapng) with Wireshark and tshark — and optionally capture live traffic — to answer questions about the traffic: follow streams, extract files / credentials / IOCs, identify hosts, DNS, TLS and protocols, and spot malicious patterns (C2, exfiltration, scanning, MITM). Use for ANY traffic / packet-capture question or CTF / forensics task that hands you a .pcap or .pcapng file, as well as authorized incident-response capture on a network segment.'
domain: cybersecurity
subdomain: network-security
tags:
- network-security
- wireshark
- packet-analysis
- traffic-analysis
- pcap
version: '1.0'
author: mahipal
license: Apache-2.0
nist_csf:
- PR.IR-01
- DE.CM-01
- ID.AM-03
- PR.DS-02
mitre_attack:
- T1040
- T1071
- T1557
- T1046
---
# Analyzing Network Traffic with Wireshark

Packet-level analysis for network security investigations. Capture or read PCAP/PCAPNG files, apply
display filters, follow streams, extract artifacts and IOCs, and produce evidence with chain-of-custody hashes.

**Do not use** to capture traffic on networks without authorization, to intercept private communications
without legal authority, or as a substitute for a full SIEM in production monitoring.

## Runtime Environment (Important)

This application runs on **Windows**; the `exec` tool uses **PowerShell** syntax.

- The CLI tools are **`tshark`** (headless capture/analysis), **`dumpcap`**, **`editcap`** and **`mergecap`**, all
  shipped with a **Wireshark** install. Live capture additionally needs the **Npcap** driver and an
  **elevated (Administrator)** session. A tool invocation itself is platform-neutral
  (`tshark -r <file> -Y <filter>`); only loops / pipes / redirection follow PowerShell.
- **Self-check before you start.** Confirm `tshark` resolves — it is the preferred engine (3,000+ dissectors,
  stream / object export, `-z` statistics). `tshark` ships with Wireshark, and on this product `exec` adds
  Wireshark's install directory to PATH, so it resolves here whenever Wireshark is installed (even if a bare
  shell would not find it):
  ```powershell
  Get-Command tshark -ErrorAction SilentlyContinue
  tshark -v
  ```
- **If `tshark` is genuinely missing, do NOT just stop** — fall back to a pure-Python parser so a `.pcap` /
  `.pcapng` question can still be answered. Write a short Python script to the workspace and run it with
  `uv run` using **scapy** (pure-Python, reads both pcap and pcapng; `uv` auto-provisions it — no manual pip):
  ```powershell
  # after writing e.g. parse.py  (from scapy.all import PcapReader; for p in PcapReader(path): ...)
  uv run --with scapy .\parse.py "<capture.pcapng>"
  ```
  scapy covers the common needs (iterate frames, filter, reassemble TCP streams, pull DNS / HTTP / payloads)
  but is weaker than tshark at deep dissection — note that and recommend installing Wireshark for full
  capability. (`pyshark` is NOT a tshark-free fallback: it shells out to tshark, so it still needs Wireshark —
  use scapy or dpkt.) Do not invent tshark paths or fall back to Linux commands (`sha256sum`, `sort -u`,
  `uniq`, `/tmp/...`).
- **Use a large timeout for capture and big-PCAP work.** A live capture runs for its full duration and
  protocol stats over multi-GB captures take minutes — pass a large `exec` timeout (e.g. `600000` ms). The
  default 30 s will kill the capture/analysis mid-run.
- **Windows interfaces have no `eth0`.** Enumerate with `tshark -D` and capture by the **number** it prints
  (`tshark -i 1 ...`), not a Linux interface name.

> ⚠️ **Forensic integrity**: hash the original capture first (`Get-FileHash`), analyze it **in place** (read-only —
> tshark/scapy never write to it, so a multi-GB capture need not be copied into the workspace), and write every export
> into your workspace directory. Never modify the evidence original.

## When to Use

- Investigating suspected network intrusions by examining packet-level evidence of command-and-control traffic, data exfiltration, or lateral movement
- Diagnosing network performance issues such as retransmissions, fragmentation, or DNS resolution failures
- Analyzing malware communication patterns by capturing traffic from sandboxed or isolated hosts
- Validating firewall and IDS rules by confirming what traffic is actually traversing network segments
- Extracting files, credentials, or indicators of compromise from captured network sessions

## Prerequisites

- Wireshark 4.0+ installed (provides `tshark`, `dumpcap`, `editcap`, `mergecap`)
- **Npcap** driver installed and an **Administrator** PowerShell session for live packet capture
- Network interface access (physical NIC, span port, or network tap) to the monitored segment
- Sufficient disk space for capture files (estimate 1 GB per minute on busy gigabit links)
- Familiarity with TCP/IP protocols, HTTP, DNS, TLS, and SMB at the packet level

## Workflow

> The examples below use the symbolic case directory `C:\cases\<case-id>`. **On this product, write your
> outputs into your firmament workspace directory instead** (see the environment instructions for its path) and
> substitute that path for `C:\cases\<case-id>` throughout. Never write into the directory of the source
> capture — treat it as read-only evidence.

### Step 1: Configure Capture Environment

Set up the capture interface and filters to target relevant traffic:

```powershell
# List available interfaces (capture by the NUMBER shown, e.g. -i 1)
tshark -D

# Start capture on interface 1 with a capture filter to limit scope
tshark -i 1 -f "host <source-ip> and (port 80 or port 443 or port 445)" -w C:\cases\<case-id>\capture.pcapng

# Capture with ring buffer to manage disk usage (10 files, ~100 MB each)
tshark -i 1 -b filesize:102400 -b files:10 -w C:\cases\<case-id>\rolling_capture.pcapng

# Capture on multiple interfaces simultaneously
tshark -i 1 -i 2 -w C:\cases\<case-id>\multi_interface.pcapng
```

For the Wireshark GUI, set the capture filter in the Capture Options dialog before starting.

### Step 2: Apply Display Filters for Targeted Analysis

```powershell
# Filter HTTP traffic containing suspicious user agents
tshark -r C:\cases\<case-id>\capture.pcapng -Y 'http.user_agent contains "curl" or http.user_agent contains "Wget"'

# Find DNS queries to suspicious TLDs
tshark -r C:\cases\<case-id>\capture.pcapng -Y 'dns.qry.name contains ".xyz" or dns.qry.name contains ".top" or dns.qry.name contains ".tk"'

# Identify TCP retransmissions indicating network issues
tshark -r C:\cases\<case-id>\capture.pcapng -Y 'tcp.analysis.retransmission'

# Filter SMB traffic for lateral movement detection
tshark -r C:\cases\<case-id>\capture.pcapng -Y 'smb2.cmd == 5 or smb2.cmd == 3' -T fields -e ip.src -e ip.dst -e smb2.filename

# Find cleartext credential transmission
tshark -r C:\cases\<case-id>\capture.pcapng -Y 'ftp.request.command == "PASS" or http.authbasic'

# Detect beaconing patterns (regular interval connections)
tshark -r C:\cases\<case-id>\capture.pcapng -Y 'ip.dst == 192.0.2.50' -T fields -e frame.time_relative -e ip.src -e tcp.dstport
```

### Step 3: Protocol-Specific Deep Analysis

```powershell
# Follow a TCP stream to reconstruct a conversation
tshark -r C:\cases\<case-id>\capture.pcapng -q -z follow,tcp,ascii,0

# Analyze HTTP request/response pairs
tshark -r C:\cases\<case-id>\capture.pcapng -Y 'http' -T fields -e frame.time -e ip.src -e ip.dst -e http.request.method -e http.request.uri -e http.response.code

# Extract DNS query/response statistics
tshark -r C:\cases\<case-id>\capture.pcapng -q -z dns,tree

# Analyze TLS handshakes (Server Hello) for negotiated cipher suites
tshark -r C:\cases\<case-id>\capture.pcapng -Y 'tls.handshake.type == 2' -T fields -e ip.src -e ip.dst -e tls.handshake.ciphersuite

# SMB file access enumeration
tshark -r C:\cases\<case-id>\capture.pcapng -Y 'smb2' -T fields -e frame.time -e ip.src -e ip.dst -e smb2.filename -e smb2.cmd
```

### Step 4: Extract Artifacts and IOCs

```powershell
# Export HTTP objects (files transferred over HTTP)
tshark -r C:\cases\<case-id>\capture.pcapng --export-objects "http,C:\cases\<case-id>\http_objects"

# Export SMB objects (files transferred over SMB)
tshark -r C:\cases\<case-id>\capture.pcapng --export-objects "smb,C:\cases\<case-id>\smb_objects"

# Extract all unique destination IPs for threat intelligence lookup
tshark -r C:\cases\<case-id>\capture.pcapng -T fields -e ip.dst | Sort-Object -Unique | Set-Content C:\cases\<case-id>\unique_dest_ips.txt

# Extract TLS certificate subject / SAN information
tshark -r C:\cases\<case-id>\capture.pcapng -Y 'tls.handshake.type == 11' -T fields -e x509sat.uTF8String -e x509ce.dNSName

# Extract all URLs accessed (host + URI), de-duplicated
tshark -r C:\cases\<case-id>\capture.pcapng -Y 'http.request' -T fields -e http.host -e http.request.uri | Sort-Object -Unique | Set-Content C:\cases\<case-id>\urls.txt

# Hash extracted files for IOC matching
Get-ChildItem -File -Recurse C:\cases\<case-id>\http_objects | Get-FileHash -Algorithm SHA256 |
  Export-Csv C:\cases\<case-id>\extracted_file_hashes.csv -NoTypeInformation
```

### Step 5: Statistical Analysis and Anomaly Detection

```powershell
# Protocol hierarchy statistics
tshark -r C:\cases\<case-id>\capture.pcapng -q -z io,phs

# Conversation statistics (TCP and UDP)
tshark -r C:\cases\<case-id>\capture.pcapng -q -z conv,tcp -z conv,udp

# Identify top talkers
tshark -r C:\cases\<case-id>\capture.pcapng -q -z endpoints,ip

# IO statistics (packets per second)
tshark -r C:\cases\<case-id>\capture.pcapng -q -z io,stat,1,"COUNT(frame) frame"

# Detect port scanning patterns (count SYN-only packets per src/port)
tshark -r C:\cases\<case-id>\capture.pcapng -Y 'tcp.flags.syn == 1 and tcp.flags.ack == 0' -T fields -e ip.src -e tcp.dstport |
  Group-Object | Sort-Object Count -Descending | Select-Object -First 20 Count, Name

# Top contacted HTTP hosts (C2 / beaconing candidates by request frequency)
tshark -r C:\cases\<case-id>\capture.pcapng -Y 'http.request' -T fields -e http.host |
  Group-Object | Sort-Object Count -Descending | Select-Object -First 20 Count, Name

# ARP cache poisoning / MITM (T1557): list every IP-to-MAC mapping claimed in ARP
# replies, de-duplicated. The same IP appearing with two different MACs is the tell.
tshark -r C:\cases\<case-id>\capture.pcapng -Y 'arp.opcode == 2' -T fields -e arp.src.proto_ipv4 -e arp.src.hw_mac |
  Sort-Object -Unique

# Wireshark's built-in duplicate-IP heuristic (gratuitous-ARP floods, cache poisoning)
tshark -r C:\cases\<case-id>\capture.pcapng -Y 'arp.duplicate-address-frame' -T fields -e arp.src.proto_ipv4 -e arp.src.hw_mac

# LLMNR / NBT-NS name poisoning (Responder-style MITM): a host answering broadcast
# name lookups it should not. Review which IP is responding.
tshark -r C:\cases\<case-id>\capture.pcapng -Y 'llmnr && dns.flags.response == 1' -T fields -e ip.src -e dns.qry.name
tshark -r C:\cases\<case-id>\capture.pcapng -Y 'nbns.flags.response == 1' -T fields -e ip.src -e nbns.name
```

### Step 6: Generate Reports and Export Evidence

```powershell
# Export filtered packets to a new PCAP for evidence preservation
tshark -r C:\cases\<case-id>\capture.pcapng -Y 'ip.addr == <source-ip> and tcp.port == 4444' -w C:\cases\<case-id>\evidence_c2_traffic.pcapng

# Generate packet summary in CSV format
tshark -r C:\cases\<case-id>\capture.pcapng -T fields -E header=y -E 'separator=,' -e frame.number -e frame.time -e ip.src -e ip.dst -e ip.proto -e tcp.srcport -e tcp.dstport -e frame.len |
  Set-Content C:\cases\<case-id>\traffic_summary.csv

# Export to JSON / Elastic (EK) for SIEM ingestion (Splunk / ELK)
tshark -r C:\cases\<case-id>\capture.pcapng -Y 'http or dns' -T json | Set-Content C:\cases\<case-id>\packets.json
tshark -r C:\cases\<case-id>\capture.pcapng -T ek | Set-Content C:\cases\<case-id>\packets.ek.json

# Create PDML (XML) output for programmatic analysis
tshark -r C:\cases\<case-id>\capture.pcapng -T pdml | Set-Content C:\cases\<case-id>\capture_analysis.xml

# Calculate capture file hash for chain of custody
Get-FileHash C:\cases\<case-id>\capture.pcapng -Algorithm SHA256 | Tee-Object C:\cases\<case-id>\capture_hash.txt
```

### Step 7: Extract Credentials and Authentication Artifacts

Recover credentials sent in the clear or as crackable hashes (authorized forensics only — treat everything
recovered here as highly sensitive):

```powershell
# HTTP Basic Auth — Wireshark dissects the decoded "user:password" for you
tshark -r C:\cases\<case-id>\capture.pcapng -Y 'http.authbasic' -T fields -e ip.src -e http.authbasic

# ...or decode the raw Authorization header yourself (PowerShell equivalent of `base64 -d`)
$h = tshark -r C:\cases\<case-id>\capture.pcapng -Y 'http.authorization' -T fields -e http.authorization | Select-Object -First 1
[Text.Encoding]::ASCII.GetString([Convert]::FromBase64String(($h -replace '^Basic ', '')))

# FTP credentials (cleartext)
tshark -r C:\cases\<case-id>\capture.pcapng -Y 'ftp.request.command == "USER" or ftp.request.command == "PASS"' -T fields -e ip.src -e ftp.request.command -e ftp.request.arg

# NTLMv2 challenge/response (SMB or HTTP NTLMSSP) — crack offline with hashcat -m 5600
tshark -r C:\cases\<case-id>\capture.pcapng -Y 'ntlmssp.auth.ntlmv2response' -T fields -e ntlmssp.auth.username -e ntlmssp.auth.domain -e ntlmssp.auth.ntlmv2response |
  Set-Content C:\cases\<case-id>\ntlm_hashes.txt

# Kerberos principals / realms (AS-REQ pre-auth)
tshark -r C:\cases\<case-id>\capture.pcapng -Y 'kerberos.CNameString' -T fields -e kerberos.CNameString -e kerberos.realm

# SMTP / POP3 / IMAP auth on un-encrypted mail sessions
tshark -r C:\cases\<case-id>\capture.pcapng -Y 'pop.request.command == "USER" or pop.request.command == "PASS"' -T fields -e ip.src -e pop.request.parameter
tshark -r C:\cases\<case-id>\capture.pcapng -Y 'imap.request contains "LOGIN"' -T fields -e ip.src -e imap.request
```

> Credentials only appear in cleartext on **un-encrypted** sessions. NTLMv2 responses are not reversible but
> are crackable offline — store them under the case directory and follow the evidence-handling policy.

### Step 8: Decrypt TLS (when session keys are available)

With the session keys, tshark decrypts TLS so the inner HTTP / HTTP2 / gRPC becomes readable:

```powershell
# Preferred: an SSLKEYLOGFILE of pre-master secrets exported by the browser/app at capture time
tshark -r C:\cases\<case-id>\capture.pcapng -o tls.keylog_file:C:\cases\<case-id>\sslkeys.log -Y 'http2 or http'

# Server RSA private key — only decrypts non-forward-secret (RSA key-exchange) cipher suites
tshark -r C:\cases\<case-id>\capture.pcapng -o 'tls.keys_list:<source-ip>,443,http,C:\cases\<case-id>\server.key' -Y 'http'
```

## Key Concepts

| Term | Definition |
|------|------------|
| **Capture Filter (BPF)** | Berkeley Packet Filter syntax applied at capture time to limit which packets are recorded, reducing file size and improving performance |
| **Display Filter** | Wireshark-specific filter syntax applied to already-captured packets for focused analysis without altering the capture file |
| **PCAPNG** | Next-generation packet capture format supporting multiple interfaces, name resolution, annotations, and metadata in a single file |
| **TCP Stream** | Reassembled sequence of TCP segments representing a complete bidirectional conversation between two endpoints |
| **Protocol Dissector** | Wireshark module that decodes a specific protocol's fields and structure, enabling deep inspection of packet contents |
| **IO Graph** | Time-series view of packet or byte rates over the capture duration, useful for identifying traffic spikes or beaconing |

## Tools & Systems

- **Wireshark 4.0+**: GUI packet analyzer with dissectors for 3,000+ protocols, stream reassembly, and export capabilities
- **tshark**: Command-line Wireshark for headless capture, batch processing, and scripted analysis pipelines
- **dumpcap**: Lightweight capture engine (bundled with Wireshark) for high-rate captures with minimal overhead — the Windows alternative to tcpdump
- **mergecap**: Combines multiple capture files into a single PCAP for unified analysis
- **editcap**: Splits, time-slices, filters, and converts between capture file formats

See `references/api-reference.md` for the full tshark cheat-sheet — display-filter and field tables, statistics
(`-z`) options, object-export / stream-follow forms, credential & auth fields, TLS-decryption and export
formats, and `editcap` / `mergecap` usage.

## Common Scenarios

### Scenario: Investigating Suspected Data Exfiltration via DNS Tunneling

**Context**: The SOC team detected unusually high DNS query volumes from a workstation (<source-ip>) to an external domain. The SIEM alert flagged DNS queries averaging <observed-rate> compared to <baseline>. A packet capture was initiated from the network tap on the workstation's VLAN.

**Approach**:
1. Capture traffic from the workstation (interface <interface-number> = the <segment-description>): `tshark -i <interface-number> -f "host <source-ip> and port 53" -w C:\cases\<case-id>\dns_exfil.pcapng`
2. Analyze DNS query patterns: `tshark -r C:\cases\<case-id>\dns_exfil.pcapng -Y 'dns.qry.name contains "<domain>.invalid"' -T fields -e frame.time -e dns.qry.name`
3. Examine subdomain labels for encoded data (long base64-like subdomains indicate tunneling): `tshark -r C:\cases\<case-id>\dns_exfil.pcapng -Y 'dns.qry.type == 16' -T fields -e dns.qry.name -e dns.txt`
4. Estimate exfiltration bandwidth by summing query-name lengths over time
5. Extract unique query names and decode base64 subdomains to recover exfiltrated content
6. Export evidence packets to a separate PCAP and `Get-FileHash` it for chain of custody

**Pitfalls**:
- Capturing unfiltered traffic on a busy network and running out of disk space before collecting relevant data
- Using display filters instead of capture filters, resulting in massive files that are slow to process
- Overlooking encrypted DNS (DoH/DoT) traffic that bypasses traditional DNS capture on port 53
- Failing to establish a capture-file hash and chain-of-custody documentation for forensic evidence

## Output Format

```
## Traffic Analysis Report

> **TEMPLATE ONLY:** The following is a fictional shape-only example. Replace every placeholder with values produced by the current capture; placeholders and labels must never appear in a real report.

**Case ID**: `<case-id>`
**Capture File**: `<capture-file>.pcapng`
**SHA-256**: `<sha256-of-source-capture>`
**Duration**: `<start-time>` to `<end-time>` `<timezone>`
**Source Interface**: `<interface-number>` (`<segment-description>`)

### Findings

**1. `<finding title: e.g. suspected DNS tunneling>`**
- Source: `<source-ip>`
- Destination DNS: `<resolver-ip>` (forwarded to `<nameserver>.invalid`)
- Query volume: <query-count> queries in `<duration>` (`<rate>` vs `<baseline>`)
- Average subdomain label length: `<N>` characters (`<encoding hypothesis>`)
- Estimated data exfiltrated: `<quantity and unit>` via `<record type>` responses

**2. Indicators of Compromise**
- Domain: `<domain>.invalid` (registration age: `<observed value or not available>`)
- Nameserver: `<nameserver>.invalid` (`<documentation-address>`)
- Query pattern: `<observed filter and pattern>`
- Response pattern: `<observed response pattern>`
```
