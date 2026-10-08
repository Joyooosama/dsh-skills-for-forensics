# /// script
# requires-python = ">=3.11"
# dependencies = ["pillow"]
# ///
"""扩展 · GIF / APNG / 动画 WEBP 逐帧导出。

多帧图常把信息分散到各帧（逐帧藏字 / 帧延迟编码 / 某一帧才是真图）。
本脚本导出每一帧为 PNG，并打印帧延迟（延迟异常有时本身就是编码）。只读输入。

用法: uv run frames.py <image> [--out DIR]
"""
import argparse
import sys
from pathlib import Path

from PIL import Image

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass


def out_dir(args, image: Path) -> Path:
    d = (Path(args.out) if args.out else Path(f"{image.stem}_steg")) / "frames"
    d.mkdir(parents=True, exist_ok=True)
    return d


def main() -> int:
    ap = argparse.ArgumentParser(description="多帧图逐帧导出")
    ap.add_argument("image")
    ap.add_argument("--out")
    args = ap.parse_args()
    p = Path(args.image)
    if not p.is_file():
        print(f"[ERROR] 文件不存在: {p}")
        return 1
    try:
        im = Image.open(p)
    except Exception as e:
        print(f"[ERROR] 打不开图片: {e}")
        return 1

    n = getattr(im, "n_frames", 1)
    if n <= 1:
        print("[INFO] 单帧图，无需逐帧；走其它技法")
        return 0

    outd = out_dir(args, p)
    delays = []
    for i in range(n):
        im.seek(i)
        im.convert("RGBA").save(outd / f"frame_{i:03d}.png")
        delays.append(im.info.get("duration", 0))
    print(f"[FINDING] 多帧图共 {n} 帧 → 已导出到 {outd}")
    uniq = sorted(set(delays))
    if len(uniq) > 1:
        print(f"[FINDING] 帧延迟不一致 {uniq[:10]} → 延迟可能本身是编码（如长短=点划/0-1）")
    print("[NEXT] 逐帧排查：对可疑帧再跑 lsb_scan / bit_planes / qr_decode；或拼接各帧（recipes）")
    print(f"[INFO] 产物目录: {outd.parent}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
