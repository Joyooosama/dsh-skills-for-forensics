# /// script
# requires-python = ">=3.11"
# dependencies = ["pillow"]
# ///
"""技法2 · EXIF / 元数据提取。

有 exiftool（在 PATH 或 tools\）就用它（最全，含 XMP/IPTC/MakerNotes/缩略图）；
否则用 Pillow 兜底读 EXIF + PNG 文本块。自动提取 EXIF 缩略图（藏图经典手法）。
只读，不修改输入。

用法: uv run exif_dump.py <image> [--out DIR]
"""
import argparse
import shutil
import subprocess
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

HOT = ("comment", "usercomment", "description", "artist", "copyright", "software",
       "author", "title", "gps", "keywords", "make", "model", "xpcomment")


def out_dir(args, image: Path) -> Path:
    d = Path(args.out) if args.out else Path(f"{image.stem}_steg")
    d.mkdir(parents=True, exist_ok=True)
    return d


def via_exiftool(p: Path, outd: Path) -> bool:
    exe = shutil.which("exiftool")
    if not exe:
        return False
    print(f"[INFO] 使用 exiftool: {exe}")
    try:
        r = subprocess.run([exe, "-a", "-G1", "-u", str(p)], capture_output=True, timeout=60)
        text = r.stdout.decode("utf-8", "replace")
        print(text)
        for line in text.splitlines():
            low = line.lower()
            if any(h in low for h in HOT):
                print(f"[FINDING] 关注字段: {line.strip()}")
        # 提取缩略图（常与主图不同 → 藏图）
        thumb = outd / "thumbnail.jpg"
        subprocess.run([exe, "-b", "-ThumbnailImage", str(p)], stdout=open(thumb, "wb"),
                       stderr=subprocess.DEVNULL, timeout=30)
        if thumb.stat().st_size > 0:
            print(f"[FINDING] 已提取 EXIF 缩略图 → {thumb}（与主图比对，藏图经典手法）")
        else:
            thumb.unlink(missing_ok=True)
    except Exception as e:
        print(f"[WARN] exiftool 执行异常: {e}")
        return False
    return True


def via_pillow(p: Path, outd: Path) -> None:
    from PIL import Image
    from PIL.ExifTags import GPSTAGS, TAGS
    print("[INFO] 未找到 exiftool，用 Pillow 兜底（建议把 exiftool.exe 放进 tools\\ 获取更全元数据）")
    try:
        im = Image.open(p)
    except Exception as e:
        print(f"[ERROR] 打不开图片: {e}")
        return

    # PNG/GIF 文本信息
    if getattr(im, "text", None):
        for k, v in im.text.items():
            print(f"[FINDING] 文本块 {k} = {str(v)[:200]!r}")
    if im.info:
        for k, v in im.info.items():
            if k in ("exif", "icc_profile") or isinstance(v, (bytes, bytearray)):
                continue
            if any(h in str(k).lower() for h in HOT):
                print(f"[FINDING] info {k} = {str(v)[:200]!r}")

    exif = None
    try:
        exif = im.getexif()
    except Exception:
        pass
    if exif:
        for tag_id, value in exif.items():
            name = TAGS.get(tag_id, tag_id)
            line = f"{name}: {str(value)[:300]}"
            print(f"  {line}")
            if str(name).lower() in HOT or any(h in str(name).lower() for h in HOT):
                print(f"[FINDING] 关注字段 {line}")
        try:
            gps = exif.get_ifd(0x8825)
            if gps:
                print("[FINDING] 含 GPS:", {GPSTAGS.get(k, k): v for k, v in gps.items()})
        except Exception:
            pass
        # 缩略图（IFD1）
        try:
            thumb = im.getexif().get_ifd(0x0201)
            _ = thumb  # Pillow 提取缩略图较繁，提示用 exiftool
        except Exception:
            pass
    else:
        print("[INFO] 无 EXIF 数据（PNG 一般无 EXIF；JPEG 也常见无元数据）。看文本块/缩略图/其它技法")


def main() -> int:
    ap = argparse.ArgumentParser(description="EXIF / 元数据提取")
    ap.add_argument("image")
    ap.add_argument("--out")
    args = ap.parse_args()
    p = Path(args.image)
    if not p.is_file():
        print(f"[ERROR] 文件不存在: {p}")
        return 1
    outd = out_dir(args, p)
    if not via_exiftool(p, outd):
        via_pillow(p, outd)
    return 0


if __name__ == "__main__":
    sys.exit(main())
