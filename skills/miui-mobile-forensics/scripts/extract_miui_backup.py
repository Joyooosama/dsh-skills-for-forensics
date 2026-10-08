#!/usr/bin/env python3
"""
Extract lightweight Android app artifacts from MIUI backup zip files.

The script avoids full extraction: it opens selected .bak entries from a MIUI
zip, strips the MIUI/Android backup headers, streams the inner tar, and extracts
small DB/XML/JSON/MMKV/local-storage files.
"""

from __future__ import annotations

import argparse
import io
import os
import re
import sys
import tarfile
import zipfile
from pathlib import Path
from typing import Iterable


DEFAULT_EXTS = {
    ".db",
    ".sqlite",
    ".sqlite3",
    ".xml",
    ".json",
    ".mmkv",
    ".ldb",
    ".sst",
    ".log",
}

DEFAULT_NAME_HINTS = {
    "rkstorage",
    "mbrowser",
    "localstorage",
    "asyncstorage",
    "manifest",
    "current",
}

DEFAULT_PATH_HINTS = (
    "/db/",
    "/databases/",
    "/shared_prefs/",
    "/sp/",
    "/no_backup/",
    "/wallets",
    "/local storage/",
    "/indexeddb/",
    "/leveldb/",
)


class PrefixStream:
    def __init__(self, prefix: bytes, source):
        self.prefix = io.BytesIO(prefix)
        self.source = source

    def read(self, size: int = -1) -> bytes:
        first = self.prefix.read(size)
        if size >= 0:
            remaining = size - len(first)
            if remaining <= 0:
                return first
            return first + self.source.read(remaining)
        return first + self.source.read()


def sanitize(name: str) -> str:
    cleaned = re.sub(r'[<>:"/\\\\|?*]+', "_", name)
    cleaned = cleaned.strip(" .")
    return cleaned or "artifact"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Extract selected lightweight artifacts from MIUI backup zip files."
    )
    parser.add_argument("zip_path", help="Path to MIUI backup zip")
    parser.add_argument("--password", "-p", help="Zip password")
    parser.add_argument("--out", "-o", default="_work/app_extracts", help="Output directory")
    parser.add_argument(
        "--include",
        "-i",
        action="append",
        default=[],
        help="Package/display-name substring to include. Repeat for multiple apps.",
    )
    parser.add_argument(
        "--max-size",
        type=int,
        default=32 * 1024 * 1024,
        help="Maximum single file size to extract, default 32 MiB",
    )
    parser.add_argument(
        "--all-small",
        action="store_true",
        help="Extract all files below max-size from selected .bak entries",
    )
    return parser.parse_args()


def list_bak_entries(zf: zipfile.ZipFile, includes: Iterable[str]) -> list[zipfile.ZipInfo]:
    entries = [zi for zi in zf.infolist() if zi.filename.lower().endswith(".bak")]
    filters = [x.lower() for x in includes if x]
    if filters:
        entries = [zi for zi in entries if any(f in zi.filename.lower() for f in filters)]
    return entries


def strip_android_backup_header(source) -> PrefixStream:
    head = source.read(1024 * 1024)
    marker = b"ANDROID BACKUP\n"
    idx = head.find(marker)
    if idx < 0:
        raise RuntimeError("ANDROID BACKUP header not found inside .bak")

    pos = idx + len(marker)
    lines: list[bytes] = []
    for _ in range(3):
        end = head.find(b"\n", pos)
        if end < 0:
            raise RuntimeError("Incomplete Android backup header")
        lines.append(head[pos:end])
        pos = end + 1

    compressed = lines[1].strip()
    encryption = lines[2].strip().lower()
    if encryption != b"none":
        raise RuntimeError(f"Encrypted Android backup payload is not supported: {encryption!r}")
    if compressed != b"0":
        raise RuntimeError(f"Compressed Android backup payload is not supported: {compressed!r}")

    return PrefixStream(head[pos:], source)


def should_extract(member: tarfile.TarInfo, max_size: int, all_small: bool) -> bool:
    if not member.isfile() or member.size > max_size:
        return False
    if all_small:
        return True
    name = member.name.replace("\\", "/")
    lower = "/" + name.lower()
    suffix = Path(name).suffix.lower()
    base = Path(name).name.lower()
    if suffix in DEFAULT_EXTS:
        return True
    if any(hint in lower for hint in DEFAULT_PATH_HINTS):
        return True
    return base in DEFAULT_NAME_HINTS


def safe_target(base: Path, member_name: str) -> Path:
    normalized = member_name.replace("\\", "/").lstrip("/")
    parts = [sanitize(part) for part in normalized.split("/") if part not in ("", ".", "..")]
    target = base.joinpath(*parts)
    resolved_base = base.resolve()
    resolved_target = target.resolve()
    if not str(resolved_target).startswith(str(resolved_base)):
        raise RuntimeError(f"Unsafe tar path: {member_name}")
    return target


def extract_entry(zf: zipfile.ZipFile, zi: zipfile.ZipInfo, password: bytes | None, out_root: Path, args) -> int:
    app_name = sanitize(Path(zi.filename).stem)
    app_out = out_root / app_name
    count = 0
    with zf.open(zi, pwd=password) as raw:
        payload = strip_android_backup_header(raw)
        with tarfile.open(fileobj=payload, mode="r|*") as tf:
            for member in tf:
                if not should_extract(member, args.max_size, args.all_small):
                    continue
                src = tf.extractfile(member)
                if src is None:
                    continue
                target = safe_target(app_out, member.name)
                target.parent.mkdir(parents=True, exist_ok=True)
                with target.open("wb") as dst:
                    remaining = member.size
                    while remaining > 0:
                        chunk = src.read(min(1024 * 1024, remaining))
                        if not chunk:
                            break
                        dst.write(chunk)
                        remaining -= len(chunk)
                count += 1
    return count


def main() -> int:
    args = parse_args()
    zip_path = Path(args.zip_path)
    out_root = Path(args.out)
    password = args.password.encode("utf-8") if args.password else None
    if not zip_path.exists():
        print(f"Failure: zip not found: {zip_path}", file=sys.stderr)
        return 1

    out_root.mkdir(parents=True, exist_ok=True)
    try:
        with zipfile.ZipFile(zip_path) as zf:
            entries = list_bak_entries(zf, args.include)
            if not entries:
                print("Failure: no matching .bak entries found", file=sys.stderr)
                return 1
            print(f"Found {len(entries)} matching .bak entries")
            total = 0
            for zi in entries:
                try:
                    count = extract_entry(zf, zi, password, out_root, args)
                    total += count
                    print(f"Extracted {count:4d} files from {zi.filename}")
                except Exception as exc:
                    print(f"Warning: skipped {zi.filename}: {exc}", file=sys.stderr)
            print(f"Done: extracted {total} files into {out_root}")
            return 0
    except zipfile.BadZipFile as exc:
        print(f"Failure: bad zip file: {exc}", file=sys.stderr)
        return 1
    except RuntimeError as exc:
        print(f"Failure: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
