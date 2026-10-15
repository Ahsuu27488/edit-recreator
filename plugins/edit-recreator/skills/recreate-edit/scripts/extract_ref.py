"""Extract EVERY frame of the reference edit, named by YOUR timeline's frame numbers.

Usage: python extract_ref.py <reference.mp4> <out_dir> [--offset 0] [--width 480] [--fps 30]

If the reference's song starts N frames later than your timeline (measure it once with an audio
cross-correlation, see sync_check.py), pass --offset N: reference frame index i is written as
(i - N).jpg, so ref/0123.jpg always lines up with your frame 123.
"""
import argparse, glob, os, shutil, subprocess, tempfile

ap = argparse.ArgumentParser()
ap.add_argument("ref"); ap.add_argument("out")
ap.add_argument("--offset", type=int, default=0)
ap.add_argument("--width", type=int, default=480)
ap.add_argument("--fps", type=float, default=30)
a = ap.parse_args()
os.makedirs(a.out, exist_ok=True)
tmp = tempfile.mkdtemp()
subprocess.run(["ffmpeg", "-v", "error", "-i", a.ref, "-vf", f"fps={a.fps},scale={a.width}:-2", "-q:v", "3",
                "-start_number", "0", os.path.join(tmp, "%05d.jpg")], check=True)
n = 0
for p in sorted(glob.glob(os.path.join(tmp, "*.jpg"))):
    f = int(os.path.basename(p)[:5]) - a.offset
    if f >= 0:
        shutil.move(p, os.path.join(a.out, f"{f:04d}.jpg")); n += 1
shutil.rmtree(tmp, ignore_errors=True)
print(f"{n} reference frames in {a.out}")
