# /// script
# requires-python = ">=3.11"
# dependencies = ["pillow", "pyzbar"]
# ///
"""扩展 · 二维码 / 条码识别。

用 pyzbar 解码 QR / DataMatrix / 各类一维条码。原图解不出时，自动尝试 灰度/二值/反相/放大
等预处理（隐写题常把码藏在某个位平面或对比度很低）。只读输入。

用法: uv run qr_decode.py <image>
提示: 若位平面导出图(bit_planes)里某张像二维码，对那张跑本脚本。
"""
import argparse
import sys
from pathlib import Path

from PIL import Image, ImageOps

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass


def variants(im: Image.Image):
    g = im.convert("L")
    yield "原图(灰度)", g
    yield "反相", ImageOps.invert(g)
    yield "二值128", g.point(lambda x: 255 if x > 128 else 0)
    yield "二值反相", g.point(lambda x: 0 if x > 128 else 255)
    yield "自动对比度", ImageOps.autocontrast(g)
    w, h = g.size
    yield "放大2x", g.resize((w * 2, h * 2))


def main() -> int:
    ap = argparse.ArgumentParser(description="二维码/条码识别")
    ap.add_argument("image")
    args = ap.parse_args()
    p = Path(args.image)
    if not p.is_file():
        print(f"[ERROR] 文件不存在: {p}")
        return 1
    try:
        from pyzbar.pyzbar import decode
    except Exception as e:
        print(f"[ERROR] pyzbar 不可用（Windows wheel 自带 zbar dll，联网首次 uv run 会装）: {e}")
        return 1

    try:
        im = Image.open(p)
    except Exception as e:
        print(f"[ERROR] 打不开图片: {e}")
        return 1

    seen = set()
    hit = False
    for name, v in variants(im):
        try:
            codes = decode(v)
        except Exception:
            codes = []
        for c in codes:
            payload = c.data.decode("utf-8", "replace")
            key = (c.type, payload)
            if key in seen:
                continue
            seen.add(key)
            hit = True
            print(f"[FINDING] [{name}] {c.type}: {payload!r}")
    if not hit:
        print("[INFO] 未解出码。pyzbar 不支持 Micro QR（罕见）。若疑码藏在位平面：先 bit_planes.py，再对可疑平面图跑本脚本。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
