"""Per-frame motion profile of the reference: where the transitions and effects are, and their speed graphs.

Usage: python motion_profile.py <reference.mp4> <out_dir> [--offset 0] [--pad 3] [--fps 30]

Edits hide effects that last 1 to 4 frames (flashes, glitches, whip blurs, shakes, zoom punches). If you
sample the reference with gaps you WILL miss them and the easing will be wrong. This script looks at EVERY
frame and writes:
  profile.csv     frame, change (pixel difference to the previous frame), flow (mean optical-flow speed px/frame),
                  flow_x, flow_y (mean direction), zoom (radial flow: + zooming in, - out), event (cut/flash/move)
  windows.txt     frame ranges to study ONE FRAME AT A TIME (every transition, padded by --pad frames)
  graph.png       the speed graph (flow per frame) with cuts and windows marked, like a graph editor
Then: for each window, run pair_sheet.py with step 1 (and pair_hi.py on its key frames), measure positions
per frame, and copy the speed curve's shape (ease-in, ease-out, overshoot) into curve() keyframes.
"""
import argparse, csv, os, subprocess, sys

import cv2
import numpy as np
from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _paths import font as _font

ap = argparse.ArgumentParser()
ap.add_argument("ref"); ap.add_argument("out")
ap.add_argument("--offset", type=int, default=0)
ap.add_argument("--pad", type=int, default=3)
ap.add_argument("--fps", type=float, default=30)
a = ap.parse_args()
os.makedirs(a.out, exist_ok=True)
W, H = 320, 180
raw = subprocess.run(["ffmpeg", "-v", "error", "-i", a.ref, "-vf", f"fps={a.fps},scale={W}:{H}", "-f", "rawvideo",
                      "-pix_fmt", "gray", "-"], capture_output=True).stdout
fr = np.frombuffer(raw, np.uint8).reshape(-1, H, W)
n = len(fr)
yy, xx = np.mgrid[0:H, 0:W]
rx, ry = (xx - W / 2), (yy - H / 2)
rn = np.sqrt(rx ** 2 + ry ** 2) + 1e-6
rows = [dict(frame=-a.offset, change=0.0, flow=0.0, flow_x=0.0, flow_y=0.0, zoom=0.0)]
for i in range(1, n):
    p, c = fr[i - 1], fr[i]
    change = float(np.abs(c.astype(np.float32) - p).mean())
    f = cv2.calcOpticalFlowFarneback(p, c, None, 0.5, 3, 15, 3, 5, 1.2, 0)
    mag = np.sqrt(f[..., 0] ** 2 + f[..., 1] ** 2)
    zoom = float(((f[..., 0] * rx + f[..., 1] * ry) / rn).mean())
    rows.append(dict(frame=i - a.offset, change=round(change, 2), flow=round(float(mag.mean()), 2),
                     flow_x=round(float(f[..., 0].mean()), 2), flow_y=round(float(f[..., 1].mean()), 2), zoom=round(zoom, 2)))
ch = np.array([r["change"] for r in rows]); fl = np.array([r["flow"] for r in rows])
cut_t = max(28.0, float(np.percentile(ch, 97)))
move_t = max(2.5, float(np.percentile(fl, 85)))
for i, r in enumerate(rows):
    ev = ""
    if ch[i] > cut_t:
        ev = "flash" if 0 < i < n - 1 and ch[i + 1] > cut_t else "cut"
    elif fl[i] > move_t:
        ev = "move"
    r["event"] = ev
with open(os.path.join(a.out, "profile.csv"), "w", newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)

# Windows: every event, padded, merged.
marks = [i for i, r in enumerate(rows) if r["event"]]
wins = []
for i in marks:
    s, e = max(0, i - a.pad), min(n - 1, i + a.pad)
    if wins and s <= wins[-1][1] + 1:
        wins[-1][1] = max(wins[-1][1], e)
    else:
        wins.append([s, e])
with open(os.path.join(a.out, "windows.txt"), "w") as fh:
    for s, e in wins:
        kinds = sorted({rows[i]["event"] for i in range(s, e + 1) if rows[i]["event"]})
        fh.write(f"{s - a.offset}-{e - a.offset}  ({(s) / a.fps:.2f}-{(e) / a.fps:.2f}s)  {','.join(kinds)}  -> study EVERY frame\n")

# Speed graph.
GW, GH, M = 1800, 420, 40
img = Image.new("RGB", (GW, GH), (18, 18, 22)); d = ImageDraw.Draw(img); ft = _font(14)
for s, e in wins:
    d.rectangle([M + s * (GW - 2 * M) / n, 0, M + (e + 1) * (GW - 2 * M) / n, GH], fill=(40, 40, 70))
top = max(fl.max(), 1)
pts = [(M + i * (GW - 2 * M) / n, GH - M - fl[i] / top * (GH - 2 * M)) for i in range(n)]
d.line(pts, fill=(90, 200, 255), width=2)
for i, r in enumerate(rows):
    if r["event"] in ("cut", "flash"):
        x = M + i * (GW - 2 * M) / n
        d.line([(x, M), (x, GH - M)], fill=(255, 90, 90) if r["event"] == "cut" else (255, 220, 60), width=1)
for t in range(0, int(n / a.fps) + 1):
    x = M + t * a.fps * (GW - 2 * M) / n
    d.text((x, GH - M + 6), f"{t}s", fill="white", font=ft)
d.text((M, 8), "speed graph: optical-flow px/frame (blue), cuts (red), flashes (yellow), study windows (shaded)", fill="white", font=ft)
img.save(os.path.join(a.out, "graph.png"))
print(f"{n} frames, {len(wins)} windows to study frame by frame -> {a.out}")
