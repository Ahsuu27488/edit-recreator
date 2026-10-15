"""Measure the reference edit's retiming (slow motion, freeze, reverse, speed ramps) against its source clip.

Usage: python speed_match.py <reference.mp4> <source_clip.mp4> <first> <last> [--offset 0] [--rotate 0|90|180|270]

For every reference frame in [first, last] (your frame numbers), finds the best-matching source frame by
normalised correlation of small grayscale thumbnails (centre crop, so the edit's zoom/crop matters less).
Prints frame -> source frame and the local speed, e.g. 0.25 = quarter-speed slow motion, 0 = freeze,
negative = reversed. Only works when you HAVE the creator's source clip (template packs often ship it).
"""
import argparse, subprocess
import numpy as np

ap = argparse.ArgumentParser()
ap.add_argument("ref"); ap.add_argument("src"); ap.add_argument("first", type=int); ap.add_argument("last", type=int)
ap.add_argument("--offset", type=int, default=0)
ap.add_argument("--rotate", type=int, default=0)
ap.add_argument("--fps", type=float, default=30)
a = ap.parse_args()
S = 48
ROT = {90: "transpose=1,", 180: "transpose=1,transpose=1,", 270: "transpose=2,"}.get(a.rotate, "")


def thumbs(path, pre=""):
    vf = f"{pre}fps={a.fps},crop='min(iw,ih)':'min(iw,ih)',scale={S}:{S}"
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-vf", vf, "-f", "rawvideo", "-pix_fmt", "gray", "-"],
                         capture_output=True).stdout
    t = np.frombuffer(raw, np.uint8).reshape(-1, S * S).astype(np.float32)
    t -= t.mean(axis=1, keepdims=True)
    t /= np.linalg.norm(t, axis=1, keepdims=True) + 1e-6
    return t


R, X = thumbs(a.ref), thumbs(a.src, ROT)
prev = None
print("frame  src   score  speed")
for f in range(a.first, a.last + 1):
    i = f + a.offset
    if i >= len(R):
        break
    sims = X @ R[i]
    j = int(np.argmax(sims))
    speed = "" if prev is None else f"{j - prev:+d}"
    print(f"{f:5d} {j:5d}  {sims[j]:.2f}  {speed}")
    prev = j
