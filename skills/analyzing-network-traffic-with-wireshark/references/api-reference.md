# API Reference: Wireshark and tshark

> Windows / PowerShell. Enumerate interfaces with `tshark -D` and capture by the **number** shown
> (`tshark -i 1`) — there is no `eth0`. Live capture needs Npcap + an elevated session. Quote display
> filters that contain `"` in **single** quotes so PowerShell passes them literally.

## Live Capture
```powershell
tshark -D                                    # List interfaces (capture by number)
tshark -i 1                                  # Capture on interface 1
tshark -i 1 -w output.pcapng                 # Write to file
tshark -i 1 -a duration:60                   # Capture for 60 seconds
tshark -i 1 -f "port 80"                     # BPF capture filter
```

## Display Filters (Read Mode)
```powershell
tshark -r capture.pcapng -Y '<filter>'
```

### Common Filters
| Filter | Purpose |
|--------|---------|
| `ip.addr == 10.0.0.5` | Traffic to/from IP |
| `tcp.port == 443` | Traffic on port 443 |
| `http.request` | HTTP requests only |
| `dns.qr == 0` | DNS queries only |
| `tls.handshake.type == 1` | TLS Client Hello |
| `tcp.flags.syn == 1 && tcp.flags.ack == 0` | SYN-only |
| `frame.len > 1500` | Large frames |
| `tcp.analysis.retransmission` | Retransmissions |
| `icmp` | ICMP traffic |
| `arp.opcode == 2` | ARP replies — add `-e arp.src.proto_ipv4 -e arp.src.hw_mac` to spot one IP / many MACs |
| `arp.duplicate-address-frame` | ARP cache poisoning / MITM heuristic (T1557) |
| `llmnr && dns.flags.response == 1` | LLMNR responses (Responder-style name poisoning) |
| `nbns.flags.response == 1` | NBT-NS name responses (poisoning) |
| `dns.flags.rcode != 0` | Failed DNS lookups (NXDOMAIN storms → DGA / tunneling) |

## Field Extraction
```powershell
tshark -r capture.pcapng -T fields `
  -e frame.time -e ip.src -e ip.dst -e tcp.dstport `
  -E 'separator=,' -E header=y
```

### Common Fields
| Field | Description |
|-------|-------------|
| `frame.time` | Packet timestamp |
| `ip.src` / `ip.dst` | Source/destination IP |
| `tcp.srcport` / `tcp.dstport` | TCP ports |
| `http.request.method` | HTTP method |
| `http.host` | HTTP Host header |
| `http.request.uri` | Request URI |
| `http.user_agent` | User-Agent |
| `dns.qry.name` | DNS query name |
| `arp.src.proto_ipv4` / `arp.src.hw_mac` | ARP sender IP / MAC (duplicate-MAC detection) |
| `tls.handshake.extensions_server_name` | TLS SNI |
| `tls.handshake.ja3` | JA3 fingerprint |

## Statistics
```powershell
tshark -r capture.pcapng -q -z conv,ip         # IP conversations
tshark -r capture.pcapng -q -z endpoints,ip    # IP endpoints
tshark -r capture.pcapng -q -z io,stat,60      # I/O per minute
tshark -r capture.pcapng -q -z io,phs          # Protocol hierarchy
tshark -r capture.pcapng -q -z http,tree       # HTTP stats
tshark -r capture.pcapng -q -z dns,tree        # DNS stats
tshark -r capture.pcapng -q -z expert          # Expert info
```

## Object Export
```powershell
tshark -r capture.pcapng --export-objects "http,C:\cases\<case-id>\http_objects"
tshark -r capture.pcapng --export-objects "smb,C:\cases\<case-id>\smb_objects"
tshark -r capture.pcapng --export-objects "tftp,C:\cases\<case-id>\tftp_objects"
tshark -r capture.pcapng --export-objects "imf,C:\cases\<case-id>\imf_objects"
```

## Stream Following
```powershell
tshark -r capture.pcapng -q -z follow,tcp,ascii,0
tshark -r capture.pcapng -q -z follow,http,ascii,0
tshark -r capture.pcapng -q -z follow,tls,ascii,0
```

## Credential & Auth Fields (cleartext / crackable)
| Field | Yields |
|-------|--------|
| `http.authbasic` | Decoded HTTP Basic `user:password` |
| `http.authorization` | Raw `Authorization` header (decode base64 yourself) |
| `ftp.request.command == "USER"` / `"PASS"` + `ftp.request.arg` | FTP credentials |
| `ntlmssp.auth.username` / `.domain` / `.ntlmv2response` | NTLMv2 hash (hashcat `-m 5600`) |
| `kerberos.CNameString` / `kerberos.realm` | Kerberos principal / realm |
| `pop.request.command` + `pop.request.parameter` | POP3 USER/PASS |
| `imap.request` (contains `"LOGIN"`) | IMAP login |
| `smtp.req.command == "AUTH"` | SMTP auth exchange |

## TLS Decryption
```powershell
# SSLKEYLOGFILE of pre-master secrets (preferred; works with PFS cipher suites)
tshark -r capture.pcapng -o tls.keylog_file:C:\cases\<case-id>\sslkeys.log -Y 'http2 or http'

# Server RSA private key (only non-forward-secret RSA key-exchange suites)
tshark -r capture.pcapng -o 'tls.keys_list:<source-ip>,443,http,C:\cases\<case-id>\server.key' -Y 'http'
```

## Export Formats
```powershell
tshark -r capture.pcapng -T fields -E header=y -E 'separator=,' -e frame.time -e ip.src -e ip.dst   # CSV
tshark -r capture.pcapng -Y 'http' -T json    # JSON (structured)
tshark -r capture.pcapng -T ek                # Elastic/ELK bulk (one obj per packet)
tshark -r capture.pcapng -T pdml              # PDML (XML)
```

## Wireshark GUI Shortcuts

| Shortcut | Action |
|----------|--------|
| `Ctrl+F` | Find packet |
| `Ctrl+G` | Go to packet |
| `Ctrl+Shift+E` | Export objects |
| `Ctrl+H` | Follow stream |

## editcap - PCAP Manipulation

```powershell
editcap -A "<start-time>" -B "<end-time>" in.pcapng out.pcapng  # Time window
editcap -c 1000 large.pcapng split.pcapng    # Split into 1000-packet files
editcap -F pcap in.pcapng out.pcap           # Convert format
```

## mergecap - Merge PCAPs

```powershell
mergecap -w merged.pcapng file1.pcapng file2.pcapng
```
