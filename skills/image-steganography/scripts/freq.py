# /// script
# requires-python = ">=3.11"
# dependencies = ["pillow", "numpy"]
# ///
"""扩展 · 频域 / 盲水印分析。

对图做 2D FFT 取幅度谱（log 归一化）。盲水印 / 周期性隐藏图案在像素域看不到，
却会在频域留下亮点或文字。逐通道 + 灰度各导一张幅度谱 PNG 供查看。只读输入，仅用 numpy。

用法: uv run freq.py <image> [--out DIR]
看输出: <out>/fft_*.png 里有无规则亮点 / 隐约文字 → 盲水印迹象。
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
    d.mkdir(parents=True, exist_ok=True)
    return d


def magnitude(plane: np.ndarray) -> np.ndarray:
    f = np.fft.fftshift(np.fft.fft2(plane.astype(np.float64)))
    mag = np.log1p(np.abs(f))
    mag -= mag.min()
    if mag.max() > 0:
        mag = mag / mag.max() * 255
    return mag.astype(np.uint8)


def main() -> int:
    ap = argparse.ArgumentParser(description="频域/盲水印分析")
    ap.add_argument("image")
    ap.add_argument("--out")
    args = ap.parse_args()
    p = Path(args.image)
    if not p.is_file():
        print(f"[ERROR] 文件不存在: {p}")
        return 1
    try:
        im = Image.open(p)
        rgb = np.array(im.convert("RGB"))
        gray = np.array(im.convert("L"))
    except Exception as e:
        print(f"[ERROR] 打不开图片: {e}")
        return 1

    outd = out_dir(args, p)
    Image.fromarray(magnitude(gray)).save(outd / "fft_gray.png")
    for ci, cn in enumerate("RGB"):
        Image.fromarray(magnitude(rgb[:, :, ci])).save(outd / f"fft_{cn}.png")
    print(f"[FINDING] 已导出频域幅度谱到 {outd}（fft_gray.png / fft_R|G|B.png）")
    print("[NEXT] 查看这些图：除中心十字外若有对称亮点/隐约文字 → 盲水印；否则频域无明显隐藏")
    print(f"[INFO] 产物目录: {outd}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
