# Python 隐写配方（通用兜底）

**核心理念：有思路就能用 Python 穷举。** 现成脚本（`lsb_scan` / `bit_planes` / `carve` …）覆盖了主线；
这里是**情境化、需按题目改造**的片段——遇到非标准套路时，复制改一改用 `uv run` 跑。

跑法：把片段存成 `x.py`，顶部加依赖头后 `uv run x.py`（依赖自动装）：
```python
# /// script
# dependencies = ["pillow", "numpy"]
# ///
```
无损格式（PNG/BMP/GIF）才适合像素级 LSB；JPEG 是有损压缩，走 steghide / 尾部追加。

---

## 1. 最小 LSB 提取（按需改维度）
```python
import numpy as np
from PIL import Image
arr = np.array(Image.open("c.png").convert("RGB"))   # H x W x 3
bits = (arr & 1).reshape(-1)                          # 全通道 LSB，xy 顺序
print(np.packbits(bits).tobytes()[:200])              # MSB-first
```
换维度（就是「换种方式再试」）：通道 `arr[:,:,0]`；位平面 `(arr>>k)&1`；列优先 `arr.T`；
LSB-first 先 `bits.reshape(-1,8)[:, ::-1]` 再 packbits。**主线已封装在 `lsb_scan.py`，先跑它。**

## 2. 通道分离
```python
from PIL import Image
for ch, im in zip("RGBA", Image.open("c.png").convert("RGBA").split()):
    im.save(f"channel_{ch}.png")
```

## 3. 双图异或（找差异/还原）
```python
import numpy as np
from PIL import Image
a = np.array(Image.open("a.png").convert("RGB"))
b = np.array(Image.open("b.png").convert("RGB"))
n = (min(a.shape[0], b.shape[0]), min(a.shape[1], b.shape[1]))
out = a[:n[0], :n[1]] ^ b[:n[0], :n[1]]
Image.fromarray(out).save("xor.png")                  # 隐藏图案常在异或后现形
```

## 4. 拼图 / 多图拼接
```python
from PIL import Image
imgs = [Image.open(f"part{i}.png") for i in range(1, 5)]
W, H = sum(i.width for i in imgs), max(i.height for i in imgs)
canvas = Image.new("RGB", (W, H)); x = 0
for im in imgs:
    canvas.paste(im, (x, 0)); x += im.width
canvas.save("combined.png")                           # 纵向拼接把 (W,H) 与 paste 坐标对调
```

## 5. 像素值直接当编码（套路9）
```python
from PIL import Image
px = list(Image.open("c.png").convert("RGB").getdata())
print("".join(chr(r) for r, g, b in px if 32 <= r < 127)[:300])   # R 通道；也试 g/b 或 r^g^b
```
（`lsb_scan.py --mode pixel` 已含此法。）

## 6. 调色板（palette）隐写
索引图（colortype=3）的「像素索引」与「调色板颜色」可分别藏信息：
```python
from PIL import Image
im = Image.open("c.png")
if im.mode == "P":
    idx = list(im.getdata())                          # 索引序列本身可能是数据
    pal = im.getpalette()                             # [r,g,b, r,g,b, ...]
    print("索引前64:", idx[:64])
    print("调色板前16色:", [tuple(pal[i:i+3]) for i in range(0, 48, 3)])
    im.convert("RGB").save("depalette.png")           # 换成真彩看是否露馅
```

## 7. 单字节异或爆破（数据像被异或加密时）
```python
data = open("appended.bin", "rb").read()
for key in range(256):
    out = bytes(b ^ key for b in data)
    if b"flag{" in out.lower() or out[:2] == b"PK":
        print(key, out[:120])
```

## 8. PNG 文本块 / chunk 手抠（carve 已自动，特殊结构时手改）
```python
import struct, zlib
raw = open("c.png", "rb").read(); off = 8
while off < len(raw):
    (ln,) = struct.unpack(">I", raw[off:off+4]); t = raw[off+4:off+8]
    body = raw[off+8:off+8+ln]
    if t in (b"tEXt", b"iTXt"): print(t, body[:200])
    if t == b"zTXt":
        k, rest = body.split(b"\x00", 1); print("zTXt", k, zlib.decompress(rest[1:])[:200])
    if t == b"IEND": break
    off += 12 + ln
```

---

## 维度速记（穷举时挨个换）
**通道、位平面、像素遍历顺序、比特序、起始偏移、按行/按列、是否异或/再解码、单帧/多帧、像素值 vs 像素位。**
一个维度没结果就换下一个，必要时几个维度一起爆破——这正是 `lsb_scan.py` 在做的事，它不够再用上面的片段定制。
