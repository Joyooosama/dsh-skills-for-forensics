# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""技法4 · PNG 高度/宽度篡改检测与修复。

经典套路：把 IHDR 里的高度改小，让图底部（藏 flag 的区域）显示不全。
本脚本用 IDAT 解压后的真实扫描行数反推正确高度，重算 IHDR CRC 导正，输出修复后的 PNG。
IDAT 损坏时回退到爆破。纯标准库。

用法:
  uv run png_height_fix.py <image.png> [--out DIR]
  uv run png_height_fix.py <image.png> --width   # 也尝试宽度
  uv run png_height_fix.py <image.png> --brute --max 4096
"""
import argparse
import struct
import sys
import zlib
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

CH = {0: 1, 2: 3, 3: 1, 4: 2, 6: 4}  # colortype -> 通道数


def out_dir(args, image: Path) -> Path:
    d = Path(args.out) if args.out else Path(f"{image.stem}_steg")
    d.mkdir(parents=True, exist_ok=True)
    return d


def parse(data: bytes):
    """返回 (ihdr_off, ihdr_data(13B), 当前CRC, idat_bytes)。"""
    if not data.startswith(b"\x89PNG\r\n\x1a\n"):
        raise ValueError("不是 PNG")
    off = 8
    ihdr_off = ihdr = None
    cur_crc = None
    idat = bytearray()
    while off + 8 <= len(data):
        (length,) = struct.unpack(">I", data[off:off + 4])
        ctype = data[off + 4:off + 8]
        body = data[off + 8:off + 8 + length]
        crc = data[off + 8 + length:off + 12 + length]
        if ctype == b"IHDR":
            ihdr_off, ihdr, cur_crc = off, body, crc
        elif ctype == b"IDAT":
            idat += body
        elif ctype == b"IEND":
            break
        off += 12 + length
    if ihdr is None:
        raise ValueError("无 IHDR")
    return ihdr_off, bytes(ihdr), cur_crc, bytes(idat)


def write_fixed(data: bytes, ihdr_off: int, new_ihdr: bytes, outp: Path) -> None:
    chunk = b"IHDR" + new_ihdr
    crc = struct.pack(">I", zlib.crc32(chunk) & 0xFFFFFFFF)
    fixed = (data[:ihdr_off]
             + struct.pack(">I", 13) + chunk + crc
             + data[ihdr_off + 12 + 13:])
    outp.write_bytes(fixed)


def main() -> int:
    ap = argparse.ArgumentParser(description="PNG 高度/宽度篡改修复")
    ap.add_argument("image")
    ap.add_argument("--out")
    ap.add_argument("--width", action="store_true", help="也尝试爆破宽度")
    ap.add_argument("--brute", action="store_true", help="IDAT 反推失败时强制爆破")
    ap.add_argument("--max", type=int, default=4096, help="爆破上限")
    args = ap.parse_args()

    p = Path(args.image)
    if not p.is_file():
        print(f"[ERROR] 文件不存在: {p}")
        return 1
    data = p.read_bytes()
    outd = out_dir(args, p)
    try:
        ihdr_off, ihdr, cur_crc, idat = parse(data)
    except Exception as e:
        print(f"[ERROR] 解析 PNG 失败: {e}")
        return 1

    width, height, bitdepth, colortype = struct.unpack(">IIBB", ihdr[:10])
    interlace = ihdr[12] if len(ihdr) >= 13 else 0
    print(f"[INFO] 声明 {width}x{height} bitdepth={bitdepth} colortype={colortype} interlace={interlace}")

    # CRC 校验：不符说明 IHDR 被改过却没修 CRC（强信号）
    calc = struct.pack(">I", zlib.crc32(b"IHDR" + ihdr) & 0xFFFFFFFF)
    if cur_crc != calc:
        print(f"[FINDING] IHDR CRC 不符（存={cur_crc.hex()} 应={calc.hex()}）→ IHDR 被篡改过！")

    ch = CH.get(colortype)
    if not ch:
        print(f"[WARN] 未知 colortype={colortype}，只能 --brute")

    # 主路径：IDAT 解压反推真实行数
    raw = None
    if idat:
        try:
            raw = zlib.decompressobj().decompress(idat)
        except Exception as e:
            print(f"[WARN] IDAT 解压失败（可能被截断）: {e}")

    fixed = False
    if interlace and not args.brute:
        # Adam7 隔行：IDAT 解压后是 7 个缩减图分块，非「高度×stride」连续扫描行，简单反推不成立
        print(f"[WARN] 隔行(interlace={interlace})PNG 无法用扫描行数反推高度；用 --brute 产候选图人工看")
    elif raw is not None and ch and not args.brute:
        stride = 1 + (width * ch * bitdepth + 7) // 8
        if stride > 1 and len(raw) % stride == 0:
            real_h = len(raw) // stride
            if real_h != height:
                print(f"[FINDING] 真实行数={real_h} ≠ 声明高度={height} → 高度被改！")
                new = struct.pack(">II", width, real_h) + ihdr[8:]
                outp = outd / f"{p.stem}_fixed.png"
                write_fixed(data, ihdr_off, new, outp)
                print(f"[OK] 已写修复图（高度→{real_h}）: {outp}")
                fixed = True
            else:
                print(f"[INFO] 高度与 IDAT 一致（{height}），未见高度篡改")
        elif args.width and stride <= 1:
            pass

    # 宽度爆破：找一个宽度使 (1+stride)*某高度 == len(raw)
    if args.width and raw is not None and ch and interlace == 0:
        print("[INFO] 尝试宽度爆破…")
        for w in range(1, args.max + 1):
            stride = 1 + (w * ch * bitdepth + 7) // 8
            if stride > 1 and len(raw) % stride == 0:
                h = len(raw) // stride
                if 1 <= h <= args.max and not (w == width and h == height):
                    print(f"[CAND] 宽={w} 高={h}（stride={stride}）能整除 IDAT")

    # 回退爆破：直接产出几张候选高度图供查看
    if not fixed and (args.brute or raw is None):
        print("[INFO] 回退爆破高度，产出候选修复图（人工/再 identify 看哪张全）")
        for h in (height * 2, max(height + 1, width), args.max):
            new = struct.pack(">II", width, h) + ihdr[8:]
            outp = outd / f"{p.stem}_h{h}.png"
            write_fixed(data, ihdr_off, new, outp)
            print(f"[CAND] 高度={h} → {outp}")

    if not fixed and raw is not None and ch and interlace == 0 and not args.brute and not args.width:
        print("[INFO] 未见高度篡改。若仍怀疑显示不全，加 --brute 或 --width。")
    print(f"[INFO] 产物目录: {outd}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
