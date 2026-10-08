#!/usr/bin/env python3
"""
Quick triage for extracted Android app artifacts.

It prints SQLite schemas/row counts and searches small text/binary files for a
regex pattern. Output is intentionally compact for CTF notebook use.
"""

from __future__ import annotations

import argparse
import os
import re
import sqlite3
import sys
from pathlib import Path


TEXT_EXTS = {".xml", ".json", ".txt", ".log", ".html", ".js", ".properties"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Scan extracted Android artifacts.")
    parser.add_argument("root", help="Extracted artifact directory")
    parser.add_argument("--pattern", "-p", help="Regex to search in small files and SQLite text fields")
    parser.add_argument("--max-size", type=int, default=16 * 1024 * 1024, help="Max file size to inspect")
    parser.add_argument("--sqlite-limit", type=int, default=5, help="Rows per SQLite table when searching")
    return parser.parse_args()


def is_sqlite(path: Path) -> bool:
    try:
        with path.open("rb") as f:
            return f.read(16) == b"SQLite format 3\x00"
    except OSError:
        return False


def scan_text(path: Path, regex: re.Pattern[str] | None, max_size: int) -> None:
    try:
        size = path.stat().st_size
        if size > max_size:
            return
        data = path.read_bytes()
    except OSError:
        return
    if not regex and path.suffix.lower() not in TEXT_EXTS:
        return
    text = data.decode("utf-8", errors="ignore")
    if regex:
        for match in regex.finditer(text):
            start = max(0, match.start() - 80)
            end = min(len(text), match.end() + 120)
            snippet = " ".join(text[start:end].split())
            print(f"[hit] {path}: {snippet}")


def scan_sqlite(path: Path, regex: re.Pattern[str] | None, row_limit: int) -> None:
    try:
        con = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
    except sqlite3.Error as exc:
        print(f"[sqlite-error] {path}: {exc}", file=sys.stderr)
        return
    try:
        cur = con.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
        tables = [row[0] for row in cur.fetchall()]
        print(f"[sqlite] {path}")
        for table in tables:
            try:
                count = con.execute(f'SELECT COUNT(*) FROM "{table}"').fetchone()[0]
                cols = [row[1] for row in con.execute(f'PRAGMA table_info("{table}")').fetchall()]
                print(f"  {table}: rows={count}, cols={','.join(cols[:12])}")
            except sqlite3.Error as exc:
                print(f"  {table}: {exc}")
            if regex:
                search_table(con, table, regex, row_limit)
    finally:
        con.close()


def search_table(con: sqlite3.Connection, table: str, regex: re.Pattern[str], row_limit: int) -> None:
    try:
        cols_info = con.execute(f'PRAGMA table_info("{table}")').fetchall()
        cols = [row[1] for row in cols_info]
        if not cols:
            return
        cur = con.execute(f'SELECT * FROM "{table}" LIMIT 2000')
        printed = 0
        for row in cur:
            joined = " | ".join("" if value is None else str(value) for value in row)
            if regex.search(joined):
                print(f"    [hit] {table}: {joined[:500]}")
                printed += 1
                if printed >= row_limit:
                    return
    except sqlite3.Error:
        return


def main() -> int:
    args = parse_args()
    root = Path(args.root)
    if not root.exists():
        print(f"Failure: root not found: {root}", file=sys.stderr)
        return 1
    regex = re.compile(args.pattern, re.IGNORECASE) if args.pattern else None
    for dirpath, _, filenames in os.walk(root):
        for filename in filenames:
            path = Path(dirpath) / filename
            try:
                if path.stat().st_size > args.max_size:
                    continue
            except OSError:
                continue
            if is_sqlite(path):
                scan_sqlite(path, regex, args.sqlite_limit)
            else:
                scan_text(path, regex, args.max_size)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
