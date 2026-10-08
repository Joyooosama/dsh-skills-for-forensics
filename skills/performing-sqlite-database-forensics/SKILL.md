---
name: performing-sqlite-database-forensics
description: Perform forensic analysis of SQLite databases to recover deleted records
  from freelists and WAL files, decode encoded timestamps, and extract evidence from
  browser history, messaging apps, and mobile device databases.
domain: cybersecurity
subdomain: digital-forensics
tags:
- sqlite
- database-forensics
- freelist
- wal
- write-ahead-log
- browser-history
- mobile-forensics
- deleted-records
- b-tree
- unallocated-space
version: '1.0'
author: mahipal
license: Apache-2.0
nist_csf:
- RS.AN-01
- RS.AN-03
- DE.AE-02
- RS.MA-01
mitre_attack:
- T1005
- T1074
- T1119
- T1070
- T1059
---

# Performing SQLite Database Forensics

## Overview

SQLite is the most widely deployed database engine in the world, used by virtually every mobile application, web browser, and many desktop applications to store user data. In digital forensics, SQLite databases are critical evidence sources containing browser history, messaging records, call logs, GPS locations, application preferences, and cached content. Forensic analysis goes beyond simple SQL queries to examine the internal B-tree page structures, freelist pages containing deleted records, Write-Ahead Log (WAL) files preserving transaction history, and unallocated space within database pages where recoverable data may persist after deletion.

## Runtime Environment (Important)

This application runs on **Windows**; the `exec` tool uses **PowerShell** syntax.

- Analysis is driven by **`python`** (3.8+) using only the standard library (`sqlite3`, `struct`) — **no pip
  packages required**. The bundled `scripts/process.py` is a self-contained, read-only analyzer. Optional GUI
  / CLI helpers: the `sqlite3` CLI, **DB Browser for SQLite**, and a hex editor (**HxD** / 010 Editor) for
  manual page inspection.
- **Self-check before you start.** Confirm Python resolves; if it is missing the environment is **not ready** —
  tell the user and stop. Do not invent paths or fall back to Linux commands:
  ```powershell
  Get-Command python -ErrorAction SilentlyContinue
  python --version
  ```
  If `python` is not found, report: *"SQLite-forensics environment is not ready (python not on PATH)."* and stop.
- **Use a large timeout for big databases.** Browser `History` and `msgstore.db` can be hundreds of MB to
  multi-GB; freelist/WAL scans take minutes — pass a large `exec` timeout (e.g. `600000` ms). The default 30 s
  will kill the scan mid-run.

> ⚠️ **Forensic integrity (SQLite-specific)**: SQLite is the **sanctioned exception** to the general "analyze evidence
> in place, don't copy it into the workspace" rule — here you MUST copy, because the database needs a consistent
> multi-file snapshot. Copy it **together with its sidecar files** — `<db>-wal`, `<db>-shm`, and `<db>-journal` — into
> your workspace. Analyzing the `.db` alone loses uncommitted (WAL) and rolled-back (journal) evidence, and **simply
> opening the original can trigger a checkpoint that destroys the WAL**. Hash the original first (`Get-FileHash`),
> analyze the copy, and open it **read-only** (`?mode=ro` URI / `PRAGMA query_only = ON`). Never modify the evidence
> original.

## When to Use

- Recovering **deleted records** (browser history, chat messages, call logs) from freelist pages, WAL frames, and unallocated space inside B-tree pages
- Examining **browser artifacts** — Chrome/Firefox/Safari history, downloads, and search terms
- Extracting evidence from **messaging / mobile app** databases — WhatsApp, Signal, iMessage, Skype, Android SMS
- Reconstructing **transaction history** from `-wal` / `-journal` sidecars that were never checkpointed
- Decoding application **timestamps** (Chrome/WebKit, Unix, Mac Absolute Time, Mozilla PRTime)
- Detecting **anti-forensics** — residual freelist/WAL data left after a user cleared history

**Do not use** on a live or locked database without first copying it and its sidecar files, or on an encrypted
database (SQLCipher / WhatsApp crypt) without the decryption key.

## Prerequisites

- **Python 3.8+** on `PATH` (standard library `sqlite3` + `struct` only — no extra packages)
- The database **plus** its `-wal`, `-shm`, and `-journal` sidecar files, copied together
- Optional: the `sqlite3` CLI, **DB Browser for SQLite** (sqlitebrowser), **HxD** / 010 Editor for manual page inspection
- Optional commercial tooling: Belkasoft Evidence Center, Magnet AXIOM
- Understanding of B-tree data structures

## Quick Triage with the Bundled Analyzer

`scripts/process.py` opens the database **read-only** and emits a structured JSON report — header fields, full
schema, per-table row counts + column metadata, freelist inventory, and WAL status — without touching the
evidence:

```powershell
# python scripts\process.py <db_path> <output_dir>
python scripts\process.py C:\cases\<case-id>\History C:\cases\<case-id>\out
Get-Content C:\cases\<case-id>\out\sqlite_forensic_report.json
```

Use the report to spot non-zero freelist pages and a present/uncheckpointed WAL, then drill into deleted-record
recovery (Methods 1–3 below).

## SQLite Internal Structure

### Database Header (First 100 Bytes)

| Offset | Size | Description |
|--------|------|-------------|
| 0 | 16 | Magic string: "SQLite format 3\000" |
| 16 | 2 | Page size (512-65536 bytes) |
| 18 | 1 | File format write version |
| 19 | 1 | File format read version |
| 24 | 4 | File change counter |
| 28 | 4 | Database size in pages |
| 32 | 4 | First freelist trunk page number |
| 36 | 4 | Total freelist pages |
| 52 | 4 | Text encoding (1=UTF-8, 2=UTF-16le, 3=UTF-16be) |
| 96 | 4 | Version-valid-for number |

### Page Types

| Type | ID | Description |
|------|----|-------------|
| B-tree Interior | 0x05 | Internal table node |
| B-tree Leaf | 0x0D | Table leaf page containing actual records |
| Index Interior | 0x02 | Internal index node |
| Index Leaf | 0x0A | Index leaf page |
| Freelist Trunk | - | Tracks freed pages |
| Freelist Leaf | - | Freed page with recoverable data |
| Overflow | - | Continuation of large records |

## Deleted Record Recovery

> The snippets below are standard-library Python (`struct`, `sqlite3`, `os`) and run as-is on Windows. Save to a
> `.py` file and run with `python`, or paste into a `python` session. Always point them at a **copy**.

### Method 1: Freelist Page Analysis

When records are deleted, SQLite may place their pages on the freelist rather than overwriting them immediately.

```python
import struct
import sqlite3
import os


def analyze_freelist(db_path: str) -> dict:
    """Analyze SQLite freelist to identify pages containing deleted data."""
    with open(db_path, "rb") as f:
        # Read header
        header = f.read(100)
        page_size = struct.unpack(">H", header[16:18])[0]
        if page_size == 1:
            page_size = 65536
        first_freelist_page = struct.unpack(">I", header[32:36])[0]
        total_freelist_pages = struct.unpack(">I", header[36:40])[0]

        freelist_info = {
            "page_size": page_size,
            "first_freelist_page": first_freelist_page,
            "total_freelist_pages": total_freelist_pages,
            "trunk_pages": [],
            "leaf_pages": []
        }

        if first_freelist_page == 0:
            return freelist_info

        # Walk the freelist trunk chain
        trunk_page = first_freelist_page
        while trunk_page != 0:
            offset = (trunk_page - 1) * page_size
            f.seek(offset)
            page_data = f.read(page_size)

            next_trunk = struct.unpack(">I", page_data[0:4])[0]
            leaf_count = struct.unpack(">I", page_data[4:8])[0]

            leaves = []
            for i in range(leaf_count):
                leaf_page = struct.unpack(">I", page_data[8 + i * 4:12 + i * 4])[0]
                leaves.append(leaf_page)

            freelist_info["trunk_pages"].append({
                "page_number": trunk_page,
                "next_trunk": next_trunk,
                "leaf_count": leaf_count,
                "leaf_pages": leaves
            })
            freelist_info["leaf_pages"].extend(leaves)
            trunk_page = next_trunk

    return freelist_info


def extract_freelist_content(db_path: str, output_dir: str):
    """Extract raw content from freelist pages for analysis."""
    info = analyze_freelist(db_path)
    os.makedirs(output_dir, exist_ok=True)

    with open(db_path, "rb") as f:
        page_size = info["page_size"]
        for page_num in info["leaf_pages"]:
            offset = (page_num - 1) * page_size
            f.seek(offset)
            page_data = f.read(page_size)
            output_file = os.path.join(output_dir, f"freelist_page_{page_num}.bin")
            with open(output_file, "wb") as out:
                out.write(page_data)

    return len(info["leaf_pages"])
```

### Method 2: WAL (Write-Ahead Log) Analysis

The WAL file contains pending transactions that have not yet been checkpointed back to the main database.

```python
def parse_wal_header(wal_path: str) -> dict:
    """Parse SQLite WAL file header and frame inventory."""
    with open(wal_path, "rb") as f:
        header = f.read(32)
        magic = struct.unpack(">I", header[0:4])[0]
        file_format = struct.unpack(">I", header[4:8])[0]
        page_size = struct.unpack(">I", header[8:12])[0]
        checkpoint_seq = struct.unpack(">I", header[12:16])[0]
        salt1 = struct.unpack(">I", header[16:20])[0]
        salt2 = struct.unpack(">I", header[20:24])[0]

        wal_info = {
            "magic": hex(magic),
            "format": file_format,
            "page_size": page_size,
            "checkpoint_sequence": checkpoint_seq,
            "frames": []
        }

        # Parse frames (24-byte header + page_size data each)
        frame_offset = 32
        frame_num = 0
        file_size = os.path.getsize(wal_path)

        while frame_offset + 24 + page_size <= file_size:
            f.seek(frame_offset)
            frame_header = f.read(24)
            page_number = struct.unpack(">I", frame_header[0:4])[0]
            db_size_after = struct.unpack(">I", frame_header[4:8])[0]

            wal_info["frames"].append({
                "frame_number": frame_num,
                "page_number": page_number,
                "db_size_pages": db_size_after,
                "offset": frame_offset
            })
            frame_offset += 24 + page_size
            frame_num += 1

    return wal_info
```

### Method 3: Unallocated Space Within Pages

Deleted cells within active B-tree pages leave data in the unallocated region between the cell pointer array and the cell content area.

```python
def analyze_unallocated_space(db_path: str, page_number: int) -> dict:
    """Analyze unallocated space within a specific B-tree page."""
    with open(db_path, "rb") as f:
        header = f.read(100)
        page_size = struct.unpack(">H", header[16:18])[0]
        if page_size == 1:
            page_size = 65536

        offset = (page_number - 1) * page_size
        f.seek(offset)
        page_data = f.read(page_size)

        # Parse page header (8 or 12 bytes depending on type)
        page_type = page_data[0]
        first_freeblock = struct.unpack(">H", page_data[1:3])[0]
        cell_count = struct.unpack(">H", page_data[3:5])[0]
        cell_content_offset = struct.unpack(">H", page_data[5:7])[0]
        if cell_content_offset == 0:
            cell_content_offset = 65536

        header_size = 12 if page_type in (0x02, 0x05) else 8
        cell_pointer_end = header_size + cell_count * 2

        unallocated_start = cell_pointer_end
        unallocated_end = cell_content_offset
        unallocated_size = unallocated_end - unallocated_start

        return {
            "page_number": page_number,
            "page_type": hex(page_type),
            "cell_count": cell_count,
            "unallocated_start": unallocated_start,
            "unallocated_end": unallocated_end,
            "unallocated_size": unallocated_size,
            "unallocated_data": page_data[unallocated_start:unallocated_end].hex()
        }
```

## Common Forensic Databases

| Application | Database File | Key Tables |
|------------|--------------|------------|
| Chrome | History | urls, visits, downloads, keyword_search_terms |
| Firefox | places.sqlite | moz_places, moz_historyvisits |
| Safari | History.db | history_items, history_visits |
| WhatsApp | msgstore.db | messages, chat_list |
| Signal | signal.sqlite | sms, mms |
| iMessage | sms.db | message, handle, chat |
| Android SMS | mmssms.db | sms, mms, threads |
| Skype | main.db | Messages, Conversations |

## Timestamp Decoding

```python
from datetime import datetime, timedelta

def decode_chrome_timestamp(chrome_ts: int) -> datetime:
    """Convert Chrome/WebKit timestamp to datetime (microseconds since 1601-01-01)."""
    epoch_delta = 11644473600
    return datetime.utcfromtimestamp((chrome_ts / 1000000) - epoch_delta)

def decode_unix_timestamp(unix_ts: int) -> datetime:
    """Convert Unix timestamp to datetime."""
    return datetime.utcfromtimestamp(unix_ts)

def decode_mac_absolute_time(mac_ts: float) -> datetime:
    """Convert Mac Absolute Time (seconds since 2001-01-01)."""
    mac_epoch = datetime(2001, 1, 1)
    return mac_epoch + timedelta(seconds=mac_ts)

def decode_mozilla_timestamp(moz_ts: int) -> datetime:
    """Convert Mozilla PRTime (microseconds since Unix epoch)."""
    return datetime.utcfromtimestamp(moz_ts / 1000000)
```

## Reference Files

- `references/workflows.md` — step-by-step flowcharts for full analysis and deleted-record recovery
- `references/api-reference.md` — quick tables: header layout, page-type bytes, timestamp decoders, common DBs
- `references/standards.md` — standards (NIST SP 800-86, SWGDE), tooling, and on-device DB locations
- `assets/template.md` — forensic analysis report template

## References

- SQLite File Format: https://www.sqlite.org/fileformat2.html
- Belkasoft SQLite Analysis: https://belkasoft.com/sqlite-analysis
- Spyder Forensics SQLite Training: https://www.spyderforensics.com/sqlite-forensic-fundamentals-2025/
- Forensic Analysis of Damaged SQLite Databases: https://www.forensicfocus.com/articles/forensic-analysis-of-damaged-sqlite-databases/

## Output Template

> **TEMPLATE ONLY:** This is a fictional shape-only example. Replace every angle-bracketed field only with values returned
> by the current investigation. Placeholders and labels must never appear in a real report; do not copy example URLs,
> counts, timestamps, filenames, or conclusions into a real report.

```text
> python scripts\process.py C:\cases\<case-id>\<database-file> C:\cases\<case-id>\out

[*] Database: C:\cases\<case-id>\<database-file>
[*] Page size: <page-size>
[*] Tables: <table-count>
[*] Freelist pages: <freelist-page-count>
[*] WAL present: <true-or-false>
[*] Report: C:\cases\<case-id>\out\sqlite_forensic_report.json
```

Deeper carving (Methods 1–3) over the freelist and WAL then recovers the deleted rows, e.g.:

```text
--- Recovered Deleted URLs ---
Row ID | URL                                              | Visit Count | Last Visit (UTC)
-------|--------------------------------------------------|-------------|---------------------
<row-id> | https://example.invalid/<path>                    | <N>         | <timestamp>
<row-id> | <observed-url-or-redacted>                       | <N>         | <timestamp>
<row-id> | <observed-url-or-redacted>                       | <N>         | <timestamp>

--- Recovered Deleted Downloads ---
Row ID | Filename               | Size      | Start Time (UTC)
-------|------------------------|-----------|---------------------
<row-id> | <observed-filename>     | <size>    | <timestamp>
<row-id> | <observed-filename>     | <size>    | <timestamp>

Summary:
  Active records:          <N>
  Deleted / WAL records:   <recovered-row-count> (recovered)
  Anti-forensics evidence: <observed evidence or none; do not infer from a non-zero count alone>
```
