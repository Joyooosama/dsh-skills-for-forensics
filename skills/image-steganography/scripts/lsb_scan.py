# /// script
# requires-python = ">=3.11"
# dependencies = ["pillow", "numpy"]
# ///
"""技法1 · LSB / 位平面穷举提取。

遍历 通道 × 位平面 × 像素顺序(xy/yx) × 比特序(msb/lsb)，抽出比特流打包成字节，
打分（可打印率 + flag/magic 命中）并按最优排序展示。只对无损格式(PNG/BMP/GIF)有意义。

用法:
  uv run lsb_scan.py <image> --show-best          # 跑全组合，列最可疑的几条
  uv run lsb_scan.py <image> --bits 3 --regex "secret|key"
  uv run lsb_scan.py <image> --mode pixel         # 像素值低字节直接当 ASCII（套路9）
"""
import argparse
import re
import sys
from pathlib import Path

import numpy as np
from PIL import Image

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

FLAG_RE = re.compile(rb"(flag|FLAG|ctf|CTF)\{[^}]{0,80}\}")
MAGIC = [b"PK\x03\x04", b"Rar!", b"\x89PNG", b"\xff\xd8\xff", b"GIF8", b"%PDF", b"BZh", b"\x1f\x8b"]


def printable_ratio(b: bytes) -> float:
    if not b:
        return 0.0
    ok = sum(1 for x in b if 32 <= x < 127 or x in (9, 10, 13))
    return ok / len(b)


def score(data: bytes) -> tuple[float, str]:
    """返回 (分数, 命中说明)。分数越高越可疑。"""
    notes = []
    s = 0.0
    m = FLAG_RE.search(data)
    if m:
        s += 100
        notes.append(f"FLAG命中 {m.group()[:60]!r}")
    for sig in MAGIC:
        if sig in data[:4096]:
            s += 30
            notes.append(f"magic {sig!r}")
            break
    pr = printable_ratio(data[:2048])
    s += pr * 20
    if pr > 0.9:
        notes.append(f"高可打印率 {pr:.2f}")
    return s, "; ".join(notes) or f"可打印率 {pr:.2f}"


def extract(arr: np.ndarray, ch: int, bit: int, order: str, bitorder: str) -> bytes:
    plane = (arr[:, :, ch] >> bit) & 1
    seq = plane.reshape(-1) if order == "xy" else plane.T.reshape(-1)
    n = (seq.size // 8) * 8
    bits = seq[:n].reshape(-1, 8)
    if bitorder == "lsb":
        bits = bits[:, ::-1]
    return np.packbits(bits).tobytes()


def main() -> int:
    ap = argparse.ArgumentParser(description="LSB / 位平面穷举提取")
    ap.add_argument("image")
    ap.add_argument("--bits", type=int, default=1, help="扫描最低几个位平面(默认1，越大越慢)")
    ap.add_argument("--regex", help="自定义命中正则(字节模式)")
    ap.add_argument("--show-best", action="store_true", help="只列最可疑的若干条")
    ap.add_argument("--top", type=int, default=8, help="--show-best 时展示条数")
    ap.add_argument("--mode", choices=["lsb", "pixel"], default="lsb")
    ap.add_argument("--out", help="把每个组合的原始字节落盘到该目录")
    args = ap.parse_args()

    p = Path(args.image)
    if not p.is_file():
        print(f"[ERROR] 文件不存在: {p}")
        return 1
    try:
        im = Image.open(p)
        if im.format == "JPEG":
            print("[WARN] JPEG 有损压缩，像素 LSB 基本无效；改走 steghide / 尾部追加")
        arr = np.array(im.convert("RGBA"))
    except Exception as e:
        print(f"[ERROR] 打不开图片: {e}")
        return 1

    user_re = re.compile(args.regex.encode()) if args.regex else None
    chans = "RGBA"

    if args.mode == "pixel":
        # 像素值（每通道整字节）按顺序直接当 ASCII
        for ci, cn in enumerate(chans):
            raw = arr[:, :, ci].reshape(-1).astype("uint8").tobytes()
            txt = bytes(x for x in raw if 32 <= x < 127)
            if FLAG_RE.search(raw) or printable_ratio(raw[:512]) > 0.85:
                print(f"[FINDING] 通道{cn} 像素值≈ASCII: {txt[:120]!r}")
        return 0

    results = []
    outdir = None
    if args.out:
        outdir = Path(args.out)
        outdir.mkdir(parents=True, exist_ok=True)

    for ci, cn in enumerate(chans):
        for bit in range(args.bits):
            for order in ("xy", "yx"):
                for bo in ("msb", "lsb"):
                    data = extract(arr, ci, bit, order, bo)
                    tag = f"{cn} bit{bit} {order} {bo}"
                    if user_re and user_re.search(data):
                        print(f"[FINDING] {tag} 命中自定义正则: {user_re.search(data).group()[:80]!r}")
                    sc, note = score(data)
                    results.append((sc, tag, note, data))
                    if outdir:
                        (outdir / f"lsb_{cn}_b{bit}_{order}_{bo}.bin").write_bytes(data)

    results.sort(key=lambda r: r[0], reverse=True)
    shown = results[: args.top] if args.show_best else [r for r in results if r[0] >= 30]
    if not shown:
        print("[INFO] 未见明显可读数据；试 --bits 3、--mode pixel，或 bit_planes.py 目视，或换 carve.py")
    for sc, tag, note, data in shown:
        preview = bytes(x for x in data[:64] if 9 <= x < 127)
        print(f"[CAND] score={sc:5.1f}  {tag:18s}  {note}  | {preview[:60]!r}")
    print(f"[INFO] 共试 {len(results)} 个组合。要提取某组合原始字节加 --out <目录>。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
