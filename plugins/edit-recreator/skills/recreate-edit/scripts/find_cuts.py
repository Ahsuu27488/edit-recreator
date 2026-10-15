"""Find hard cuts and flashes in a video (frame-to-frame difference spikes).

Usage: python find_cuts.py <video.mp4> [--threshold 28] [--offset 0]
Prints frame numbers (shifted by --offset into your timeline) and seconds, plus one-frame flashes
(frames that differ strongly from BOTH neighbours: negative flashes, white/B&W hits).
"""
import argparse, subprocess
import numpy as np

ap = argparse.ArgumentParser()
ap.add_argument("video"); ap.add_argument("--threshold", type=float, default=28); ap.add_argument("--offset", type=int, default=0)
ap.add_argument("--fps", type=float, default=30)
a = ap.parse_args()
w, h = 96, 54
raw = subprocess.run(["ffmpeg", "-v", "error", "-i", a.video, "-vf", f"fps={a.fps},scale={w}:{h}", "-f", "rawvideo",
                      "-pix_fmt", "rgb24", "-"], capture_output=True).stdout
fr = np.frombuffer(raw, np.uint8).reshape(-1, h, w, 3).astype(np.float32)
d = np.abs(np.diff(fr, axis=0)).mean(axis=(1, 2, 3))
cuts = [i + 1 for i in np.nonzero(d > a.threshold)[0]]
flashes = [i for i in range(1, len(fr) - 1) if d[i - 1] > a.threshold and d[i] > a.threshold]
print("cuts:   ", ", ".join(f"{c - a.offset} ({c / a.fps:.2f}s)" for c in cuts))
print("flashes:", ", ".join(f"{c - a.offset} ({c / a.fps:.2f}s)" for c in flashes) or "none")
