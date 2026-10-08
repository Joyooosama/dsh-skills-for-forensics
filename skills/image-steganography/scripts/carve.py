# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""技法3 · 文件尾追加 / 内嵌文件雕复 + 解码链 + PNG 文本块。

① 找图片正常结束（PNG IEND / JPEG FFD9 / GIF trailer）之后的追加数据；
② 全文件扫描内嵌文件签名（zip/rar/7z/pdf/png/jpg/gif…）并按签名雕出；
③ 提取 PNG tEXt/zTXt/iTXt 文本块；
④ 对追加/雕出的 blob 试 zlib/gzip/base64/hex 解码链，是 zip 就解。
产物写到输出目录。只读输入，纯标准库（无需第三方依赖）。

用法: uv run carve.py <image> [--out DIR]
"""
import argparse
import base64
import gzip
import io
import re
import struct
import sys
import zipfile
import zlib
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

SIGS = [
    (b"PK\x03\x04", "zip"), (b"Rar!\x1a\x07", "rar"), (b"7z\xbc\xaf\x27\x1c", "7z"),
    (b"%PDF", "pdf"), (b"\x89PNG\r\n\x1a\n", "png"), (b"\xff\xd8\xff", "jpg"),
    (b"GIF87a", "gif"), (b"GIF89a", "gif"), (b"BZh", "bz2"), (b"\x1f\x8b\x08", "gz"),
    (b"ID3", "mp3"), (b"OggS", "ogg"),
]


def out_dir(args, image: Path) -> Path:
    d = Path(args.out) if args.out else Path(f"{image.stem}_steg")
    d.mkdir(parents=True, exist_ok=True)
    return d


def find_all(data: bytes, sig: bytes) -> list[int]:
    out, i = [], data.find(sig)
    while i != -1:
        out.append(i)
        i = data.find(sig, i + 1)
    return out


def trailing_offset(data: bytes) -> int | None:
    """返回图片正常结束后的偏移（之后即追加数据）。"""
    if data.startswith(b"\x89PNG"):
        m = data.find(b"IEND")
        return m + 8 if m != -1 else None
    if data.startswith(b"\xff\xd8"):
        m = data.rfind(b"\xff\xd9")
        return m + 2 if m != -1 else None
    if data.startswith((b"GIF87a", b"GIF89a")):
        m = data.rfind(b"\x3b")
        return m + 1 if m != -1 else None
    return None


def try_decode_chain(blob: bytes) -> None:
    for name, fn in [
        ("zlib", lambda x: zlib.decompress(x)),
        ("gzip", lambda x: gzip.decompress(x)),
        ("base64", lambda x: base64.b64decode(re.sub(rb"\s", b"", x), validate=True)),
        ("hex", lambda x: bytes.fromhex(x.decode("latin1").strip())),
    ]:
        try:
            out = fn(blob)
            if out and len(out) > 3:
                print(f"[FINDING] 解码链 [{name}] -> {out[:120]!r}")
        except Exception:
            pass


def extract_png_text(data: bytes) -> None:
    off = 8
    while off + 8 <= len(data):
        try:
            (length,) = struct.unpack(">I", data[off:off + 4])
        except struct.error:
            break
        ctype = data[off + 4:off + 8]
        body = data[off + 8:off + 8 + length]
        if ctype == b"tEXt":
            print(f"[FINDING] tEXt: {body.replace(chr(0).encode(), b': ')[:300]!r}")
        elif ctype == b"zTXt":
            try:
                key, rest = body.split(b"\x00", 1)
                print(f"[FINDING] zTXt {key.decode('latin1')}: {zlib.decompress(rest[1:])[:300]!r}")
            except Exception:
                pass
        elif ctype == b"iTXt":
            print(f"[FINDING] iTXt: {body[:300]!r}")
        elif ctype == b"IEND":
            break
        off += 12 + length


def main() -> int:
    ap = argparse.ArgumentParser(description="文件尾追加 / 内嵌雕复 + 解码链")
    ap.add_argument("image")
    ap.add_argument("--out")
    args = ap.parse_args()
    p = Path(args.image)
    if not p.is_file():
        print(f"[ERROR] 文件不存在: {p}")
        return 1
    data = p.read_bytes()
    outd = out_dir(args, p)

    if data.startswith(b"\x89PNG"):
        extract_png_text(data)

    # 追加数据
    toff = trailing_offset(data)
    if toff is not None and toff < len(data):
        blob = data[toff:]
        ap_path = outd / "appended.bin"
        ap_path.write_bytes(blob)
        print(f"[FINDING] 追加数据 {len(blob)} 字节，头部 {blob[:8]!r} → {ap_path}")
        if blob[:2] == b"PK":
            try:
                zipfile.ZipFile(io.BytesIO(blob)).extractall(outd / "appended_zip")
                print(f"[FINDING] 追加数据是 zip，已解到 {outd/'appended_zip'}")
            except Exception as e:
                print(f"[WARN] zip 解压失败: {e}")
        try_decode_chain(blob[:8192])

    # 全文件签名雕复（跳过偏移0的本体）
    carved = 0
    for sig, ext in SIGS:
        for pos in find_all(data, sig):
            if pos == 0:
                continue
            seg = data[pos:]
            name = outd / f"carved_{pos}.{ext}"
            name.write_bytes(seg)
            print(f"[FINDING] 偏移 {pos} 内嵌 {ext}（签名 {sig!r}）→ {name}")
            carved += 1
            if ext == "zip":
                try:
                    zipfile.ZipFile(io.BytesIO(seg)).extractall(outd / f"zip_{pos}")
                    print(f"[FINDING]   └ 已解压到 {outd}/zip_{pos}")
                except Exception:
                    pass
    if carved == 0 and (toff is None or toff >= len(data)):
        print("[INFO] 未发现追加/内嵌数据；试 LSB(lsb_scan) / 位平面(bit_planes) / 高度(png_height_fix)")
    print(f"[INFO] 产物目录: {outd}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
