"""Report how close each audited text layer comes to the frame edges (see remotion/scripts/text-audit.mjs).

ink  = the letters themselves (bright pixels)
glow = everything visibly lit around them
A negative or zero margin means the layer touches/leaves the frame on that side, i.e. it is cut off.
"""
import json, sys

sys.stdout.reconfigure(encoding="utf-8")

import numpy as np
from PIL import Image

GLOW = 20  # any channel above this counts as visibly lit
INK_FRACTION = 0.45  # letters = pixels at least this bright relative to the layer's brightest pixels (works for dark text too)
SAFE = 40  # px of breathing room we want between the letters and the frame edge


def bbox(mask):
    ys, xs = np.nonzero(mask)
    if len(xs) == 0:
        return None
    return int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())


manifest = json.load(open(sys.argv[1], encoding="utf-8"))
print(f"{'layer':<16}{'frame':>6}   {'ink box (x0,y0)-(x1,y1)':<28}{'ink margins L/T/R/B':<24}{'glow margins L/T/R/B':<24} verdict")
for m in manifest:
    im = np.asarray(Image.open(m["file"]).convert("RGB")).astype(np.float32)
    h, w = im.shape[:2]
    level = im.max(axis=2)  # brightest channel, so dark-green or dark-pink letters still register
    peak = np.percentile(level[level > GLOW], 99) if (level > GLOW).any() else 0
    ink = bbox(level > max(GLOW, peak * INK_FRACTION))
    glow = bbox(level > GLOW)
    if ink is None:
        print(f"{m['layer']:<16}{m['frame']:>6}   (nothing visible: check the frame)")
        continue
    im_ = (ink[0], ink[1], w - 1 - ink[2], h - 1 - ink[3])
    gm = (glow[0], glow[1], w - 1 - glow[2], h - 1 - glow[3])
    sides = "LTRB"
    cut = [sides[i] for i, v in enumerate(im_) if v <= 0]
    tight = [sides[i] for i, v in enumerate(im_) if 0 < v < SAFE]
    glow_cut = [sides[i] for i, v in enumerate(gm) if v <= 0]
    verdict = ("LETTERS CUT " + "".join(cut)) if cut else ("tight " + "".join(tight)) if tight else "ok"
    if glow_cut and not cut:
        verdict += f" (glow reaches edge {''.join(glow_cut)})"
    print(f"{m['layer']:<16}{m['frame']:>6}   {str(ink[:2]) + '-' + str(ink[2:]):<28}{'/'.join(map(str, im_)):<24}{'/'.join(map(str, gm)):<24} {verdict}")
