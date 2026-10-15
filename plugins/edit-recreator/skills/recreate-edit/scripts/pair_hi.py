"""Large reference-vs-ours pairs for a few frames, with a 10% ruler so positions can be read off.

Usage: python pair_hi.py <reference.mp4> <ours_dir> <out.jpg> <frame> [frame ...] [--offset N] [--fps 30]

Reference frame for your frame f = frame index f+N of the reference (seeks to just before (f+N)/fps s,
which lands exactly on that frame; seeking to +0.001 s lands one frame late). Ours come from
<ours_dir>/element-NNN.jpeg (Remotion --sequence output). Each row: reference left, ours right, 960x540.
"""
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
from _paths import font as _font

import argparse, os, subprocess, tempfile
from PIL import Image, ImageDraw, ImageFont

ap = argparse.ArgumentParser()
ap.add_argument("ref"); ap.add_argument("ours"); ap.add_argument("out"); ap.add_argument("frames", nargs="+", type=int)
ap.add_argument("--offset", type=int, default=0)
ap.add_argument("--fps", type=float, default=30)
a = ap.parse_args()
W, H = 960, 540
font = _font(22)
tmp = tempfile.mkdtemp()


def ruled(im, label, color):
    d = ImageDraw.Draw(im)
    for i in range(1, 10):
        d.line([(i * W // 10, 0), (i * W // 10, 8)], fill="white", width=2)
        d.line([(i * W // 10, H - 8), (i * W // 10, H)], fill="white", width=2)
        d.line([(0, i * H // 10), (8, i * H // 10)], fill="white", width=2)
    d.rectangle([0, 0, 170, 28], fill="black")
    d.text((5, 2), label, fill=color, font=font)
    return im


def ours_path(f):
    for name in (f"element-{f:03d}.jpeg", f"element-{f:04d}.jpeg", f"element-{f}.jpeg"):
        p = os.path.join(a.ours, name)
        if os.path.exists(p):
            return p
    return None


sheet = Image.new("RGB", (2 * W + 6, len(a.frames) * (H + 6)), (20, 20, 20))
for r, f in enumerate(a.frames):
    p = os.path.join(tmp, f"{f}.png")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{(f + a.offset) / a.fps - 0.001:.4f}", "-i", a.ref,
                    "-frames:v", "1", "-vf", f"scale={W}:{H}", p], check=True)
    ref = ruled(Image.open(p).convert("RGB"), f"REF {f}", "yellow")
    op = ours_path(f)
    ours = Image.open(op).convert("RGB").resize((W, H), Image.LANCZOS) if op else Image.new("RGB", (W, H), (60, 0, 0))
    sheet.paste(ref, (0, r * (H + 6)))
    sheet.paste(ruled(ours, f"OURS {f}", "cyan"), (W + 6, r * (H + 6)))
sheet.save(a.out, quality=88)
print(a.out, sheet.size)
