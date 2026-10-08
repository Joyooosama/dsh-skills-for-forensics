# /// script
# requires-python = ">=3.11"
# dependencies = ["pillow", "numpy"]
# ///
"""技法5 · 通道 / 位平面导出（Stegsolve 平替）。

把每个 通道 × 位平面 导成黑白 PNG，并给每个平面打一个「非随机度」分（越高越可能藏图案/数据）。
agent 据分数挑可疑平面优先看；人工也可逐张浏览。只读输入。

用法: uv run bit_planes.py <image> [--out DIR]
输出: <out>/plane_<通道><位>.png（位0=LSB），以及各通道全图 channel_<C>.png
"""
import argparse
import sys
from pathlib import Path

import numpy as np
from PIL import Image

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass


def out_dir(args, image: Path) -> Path:
    d = Path(args.out) if args.out else Path(f"{image.stem}_steg")
    (d / "planes").mkdir(parents=True, exist_ok=True)
    return d


def non_random_score(plane: np.ndarray) -> float:
    """0/1 平面的非随机度：相邻像素相等比例偏离 0.5 的程度。纯随机≈0，有结构→高。
    常量平面（全0/全1，如不透明 alpha）无隐藏信息，返回 0。"""
    if plane.size < 4 or plane.min() == plane.max():
        return 0.0
    h = np.mean(plane[:, 1:] == plane[:, :-1])
    v = np.mean(plane[1:, :] == plane[:-1, :])
    return float(abs(h - 0.5) + abs(v - 0.5))  # 0~1


def main() -> int:
    ap = argparse.ArgumentParser(description="通道/位平面导出")
    ap.add_argument("image")
    ap.add_argument("--out")
    ap.add_argument("--bits", type=int, default=8, help="导出每通道前几位(默认8全导)")
    args = ap.parse_args()

    p = Path(args.image)
    if not p.is_file():
        print(f"[ERROR] 文件不存在: {p}")
        return 1
    try:
        im = Image.open(p)
        if im.format == "JPEG":
            print("[WARN] JPEG 像素低位已被压缩破坏，位平面意义有限")
        arr = np.array(im.convert("RGBA"))
    except Exception as e:
        print(f"[ERROR] 打不开图片: {e}")
        return 1

    outd = out_dir(args, p)
    chans = "RGBA"
    cand = []
    for ci, cn in enumerate(chans):
        # 跳过常量通道（如全不透明的 alpha）：无信息且会污染可疑度排名
        if arr[:, :, ci].min() == arr[:, :, ci].max():
            continue
        Image.fromarray(arr[:, :, ci]).save(outd / f"channel_{cn}.png")
        for bit in range(min(args.bits, 8)):
            plane = ((arr[:, :, ci] >> bit) & 1).astype(np.uint8)
            Image.fromarray(plane * 255).save(outd / "planes" / f"plane_{cn}{bit}.png")
            cand.append((non_random_score(plane), f"{cn} bit{bit}"))

    cand.sort(reverse=True)
    if not cand:
        # 所有通道都是常量（纯色/全透明/1×1）：无平面可分析，避免下方 cand[0] 越界
        print("[INFO] 所有通道都是常量（纯色/全透明/1×1），无位平面可分析；试 carve.py / lsb_scan.py")
        print(f"[INFO] 产物目录: {outd}")
        return 0
    print(f"[INFO] 已导出 {len(cand)} 个位平面到 {outd/'planes'}")
    print("[INFO] 非随机度最高的平面（优先看，可能藏图案/二维码/文字）：")
    for sc, tag in cand[:6]:
        flag = " ←可疑" if sc > 0.15 else ""
        print(f"[CAND] {tag:10s} 非随机度={sc:.3f}{flag}")
    if cand[0][0] > 0.15:
        print("[NEXT] 可疑平面若像二维码 → qr_decode.py；像文字 → 直接看 / OCR")
    else:
        print("[INFO] 各平面都接近随机；可能无位平面隐写，或藏在数据流（试 lsb_scan / carve）")
    print(f"[INFO] 产物目录: {outd}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
