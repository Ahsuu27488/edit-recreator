"""Side-by-side frame study: reference frame on top, ours below, for every frame in a range.

Usage: python pair_sheet.py <ref_dir> <ours_dir> <first> <last> <out.jpg> [cols] [tile_w] [step]
ref_dir has NNNN.jpg (named by YOUR frame numbers, see extract_ref.py), ours_dir has element-NNN.jpeg
(Remotion --sequence output). Top row = reference, bottom = your render.
"""
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
from _paths import font as _font

import os, sys
from PIL import Image, ImageDraw, ImageFont

ref_dir, ours_dir, first, last, out = sys.argv[1], sys.argv[2], int(sys.argv[3]), int(sys.argv[4]), sys.argv[5]
cols = int(sys.argv[6]) if len(sys.argv) > 6 else 6
tw = int(sys.argv[7]) if len(sys.argv) > 7 else 320
step = int(sys.argv[8]) if len(sys.argv) > 8 else 1
th = tw * 9 // 16
frames = list(range(first, last + 1, step))
rows = (len(frames) + cols - 1) // cols
font = _font(max(12, tw // 18))
sheet = Image.new("RGB", (cols * tw, rows * (2 * th + 6)), (20, 20, 20))
d = ImageDraw.Draw(sheet)


def tile(path):
    if not os.path.exists(path):
        return Image.new("RGB", (tw, th), (60, 0, 0))
    im = Image.open(path).convert("RGB")
    return im.resize((tw, th), Image.LANCZOS)


for i, f in enumerate(frames):
    x, y = (i % cols) * tw, (i // cols) * (2 * th + 6)
    ref = tile(os.path.join(ref_dir, f"{f:04d}.jpg"))
    p = os.path.join(ours_dir, f"element-{f:03d}.jpeg")
    ours = tile(p if os.path.exists(p) else os.path.join(ours_dir, f"element-{f}.jpeg"))
    sheet.paste(ref, (x, y))
    sheet.paste(ours, (x, y + th))
    t = f / 30
    d.text((x + 4, y + 2), f"REF {f} ({t:.2f}s)", fill=(255, 230, 0), font=font)
    d.text((x + 4, y + th + 2), f"OURS {f}", fill=(0, 230, 255), font=font)
sheet.save(out, quality=90)
print(out, sheet.size)
