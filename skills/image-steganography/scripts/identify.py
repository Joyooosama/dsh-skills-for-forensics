# /// script
# requires-python = ">=3.11"
# dependencies = ["pillow"]
# ///
"""步骤1 · 图片真实类型识别与结构异常探测。

判断扩展名是否造假、解析结构、报告追加数据/多图拼接/文本块/调色板/APNG/PNG 高度疑似被改，
并据此建议优先试哪些隐写技法。只读，不修改输入。

用法: uv run identify.py <image>
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

MAGICS = [
    (b"\x89PNG\r\n\x1a\n", "PNG"),
    (b"\xff\xd8\xff", "JPEG"),
    (b"GIF87a", "GIF87a"),
    (b"GIF89a", "GIF89a"),
    (b"BM", "BMP"),
    (b"II*\x00", "TIFF(LE)"),
    (b"MM\x00*", "TIFF(BE)"),
    (b"PK\x03\x04", "ZIP"),
    (b"Rar!\x1a\x07", "RAR"),
    (b"7z\xbc\xaf\x27\x1c", "7Z"),
    (b"%PDF", "PDF"),
    (b"\x1f\x8b\x08", "GZIP"),
]

EXT_FMT = {".png": "PNG", ".jpg": "JPEG", ".jpeg": "JPEG", ".gif": "GIF",
           ".bmp": "BMP", ".tif": "TIFF", ".tiff": "TIFF", ".webp": "WEBP"}


def detect_format(data: bytes) -> str:
    if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return "WEBP"
    for magic, name in MAGICS:
        if data.startswith(magic):
            return name
    return "Unknown"


def find_all(data: bytes, sig: bytes) -> list[int]:
    out, i = [], data.find(sig)
    while i != -1:
        out.append(i)
        i = data.find(sig, i + 1)
    return out


def analyze_png(data: bytes) -> list[str]:
    out = []
    off = 8
    chunks = []
    width = height = bitdepth = colortype = None
    interlace = 0
    iend_end = None
    idat = bytearray()
    while off + 8 <= len(data):
        try:
            (length,) = struct.unpack(">I", data[off:off + 4])
        except struct.error:
            break
        ctype = data[off + 4:off + 8]
        chunks.append(ctype.decode("latin1", "replace"))
        body = data[off + 8:off + 8 + length]
        if ctype == b"IHDR" and length >= 13:
            width, height, bitdepth, colortype = struct.unpack(">IIBB", body[:10])
            interlace = body[12]  # 0=无隔行；1=Adam7（行布局不连续，下方按扫描行反推不适用）
        elif ctype == b"IDAT":
            idat += body
        elif ctype == b"IEND":
            iend_end = off + 12 + length
            break
        off += 12 + length

    ct = {0: "灰度", 2: "RGB", 3: "调色板(palette)", 4: "灰度+α", 6: "RGBA"}
    out.append(f"[INFO] PNG {width}x{height} bitdepth={bitdepth} colortype={colortype}({ct.get(colortype, '?')})")

    txt = [c for c in chunks if c in ("tEXt", "zTXt", "iTXt")]
    if txt:
        out.append(f"[FINDING] 含文本块 {txt} → 跑 carve.py 提取（常藏 flag/提示）")
    if "PLTE" in chunks:
        out.append("[INFO] 含调色板 PLTE → 可疑时查 palette 隐写（recipes）")
    if "acTL" in chunks:
        out.append("[FINDING] 含 acTL → APNG 多帧 → 跑 frames.py 逐帧看")

    if iend_end is not None and iend_end < len(data):
        out.append(f"[FINDING] IEND 之后还有 {len(data) - iend_end} 字节追加数据 → 跑 carve.py（图后藏包最常见）")

    sigs = find_all(data, b"\x89PNG\r\n\x1a\n")
    if len(sigs) > 1:
        out.append(f"[FINDING] 发现 {len(sigs)} 个 PNG 签名（偏移 {sigs}）→ 多图拼接，跑 carve.py")

    # 高度篡改探测：用 IDAT 解压后的真实行数 vs 声明高度
    if width and colortype is not None and bitdepth and idat:
        try:
            raw = zlib.decompressobj().decompress(bytes(idat))
            ch = {0: 1, 2: 3, 3: 1, 4: 2, 6: 4}.get(colortype)
            if ch and interlace == 0:
                stride = 1 + (width * ch * bitdepth + 7) // 8
                if stride > 1 and len(raw) % stride == 0:
                    real_h = len(raw) // stride
                    if real_h != height:
                        out.append(f"[FINDING] IDAT 实际行数={real_h} ≠ 声明高度={height} → 高度被改！跑 png_height_fix.py")
            elif interlace:
                out.append("[INFO] 隔行(Adam7)PNG，扫描行数反推高度不适用；若疑显示不全用 png_height_fix.py --brute")
        except Exception:
            out.append("[WARN] IDAT 解压失败（可能被截断/篡改）→ 试 png_height_fix.py")
    return out


def analyze_jpeg(data: bytes) -> list[str]:
    out = []
    sois = find_all(data, b"\xff\xd8\xff")
    if len(sois) > 1:
        out.append(f"[FINDING] 发现 {len(sois)} 个 JPEG 头 FFD8（偏移 {sois}）→ 多图拼接，跑 carve.py")
    eois = find_all(data, b"\xff\xd9")
    if eois:
        last = eois[-1] + 2
        if last < len(data):
            out.append(f"[FINDING] 最后一个 FFD9 之后还有 {len(data) - last} 字节追加数据 → 跑 carve.py")
    out.append("[INFO] JPEG 是有损压缩：不要做像素 LSB；走 EXIF(exif_dump) / steghide / 尾部追加")
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description="图片真实类型识别与结构异常探测")
    ap.add_argument("image")
    args = ap.parse_args()

    p = Path(args.image)
    if not p.is_file():
        print(f"[ERROR] 文件不存在: {p}")
        return 1
    data = p.read_bytes()

    real = detect_format(data)
    ext = p.suffix.lower()
    print(f"[INFO] 文件: {p.name}  大小: {len(data)} 字节")
    print(f"[INFO] 真实格式(magic): {real}   扩展名: {ext or '(无)'}")

    exp = EXT_FMT.get(ext)
    if exp and real != "Unknown" and not real.startswith(exp):
        print(f"[FINDING] 扩展名造假！实际是 {real}，按 {real} 处理（必要时改扩展名再开）")

    if real == "PNG":
        for line in analyze_png(data):
            print(line)
    elif real == "JPEG":
        for line in analyze_jpeg(data):
            print(line)
    elif real in ("ZIP", "RAR", "7Z", "PDF", "GZIP"):
        print(f"[FINDING] 这其实是 {real} 文件（伪装成图片）→ 直接按该类型解开")

    # PIL 交叉验证尺寸/帧数
    try:
        from PIL import Image
        with Image.open(p) as im:
            print(f"[INFO] PIL: mode={im.mode} size={im.size} format={im.format}")
            n = getattr(im, "n_frames", 1)
            if n > 1:
                print(f"[FINDING] 多帧图（{n} 帧）→ 跑 frames.py 逐帧导出")
    except Exception as e:
        print(f"[WARN] PIL 打不开（结构可能被篡改，如高度被改）: {e}")

    print("[NEXT] 按 SKILL.md 步骤2：LSB→lsb_scan / EXIF→exif_dump / 尾部→carve / 高度→png_height_fix / 通道→bit_planes")
    return 0


if __name__ == "__main__":
    sys.exit(main())
