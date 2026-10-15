"""Labelled pose picker: one tile every <step> seconds from each clip, each with a short code (e.g. A12) the user
can name. Usage: pose_sheet.py <out.jpg> <step> <tile_w> <cols> <code>=<video> [<code>=<video> ...]
Writes the sheet plus <out>.json mapping each code to (video, seconds)."""
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
from _paths import font as _font

import json, os, subprocess, sys, tempfile, glob
from PIL import Image, ImageDraw, ImageFont

out, step, tw, cols = sys.argv[1], float(sys.argv[2]), int(sys.argv[3]), int(sys.argv[4])
font = _font(max(18, tw // 9))
tiles, index = [], {}
for spec in sys.argv[5:]:
    code, video = spec.split("=", 1)
    tmp = tempfile.mkdtemp()
    subprocess.run(["ffmpeg", "-v", "error", "-i", video, "-vf", f"fps=1/{step},scale={tw}:-2",
                    os.path.join(tmp, "%04d.png")], check=True)
    for i, f in enumerate(sorted(glob.glob(os.path.join(tmp, "*.png")))):
        t = i * step
        label = f"{code}{i + 1}"
        im = Image.open(f).convert("RGB")
        d = ImageDraw.Draw(im)
        txt = f"{label}  {t:.1f}s"
        w = d.textlength(txt, font=font)
        d.rectangle([0, 0, w + 12, font.size + 10], fill="black")
        d.text((6, 4), txt, fill="yellow", font=font)
        tiles.append(im)
        index[label] = {"video": os.path.basename(video), "t": round(t, 2)}
th = max(t.size[1] for t in tiles)
rows = (len(tiles) + cols - 1) // cols
sheet = Image.new("RGB", (cols * (tw + 6), rows * (th + 6)), (25, 25, 25))
for i, t in enumerate(tiles):
    sheet.paste(t, ((i % cols) * (tw + 6), (i // cols) * (th + 6)))
sheet.save(out, quality=88)
json.dump(index, open(os.path.splitext(out)[0] + ".json", "w"), indent=1)
print(out, len(tiles), "poses")
