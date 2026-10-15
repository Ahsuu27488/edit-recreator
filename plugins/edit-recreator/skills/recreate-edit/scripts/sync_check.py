"""Compare two renders for sync: audio identity/offset, scene-cut frame positions and motion alignment.
Usage: sync_check.py <a.mp4> <b.mp4>"""
import subprocess, sys
import numpy as np



def audio(p, sr=8000):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", p, "-ac", "1", "-ar", str(sr), "-f", "s16le", "-"],
                         capture_output=True).stdout
    return np.frombuffer(raw, np.int16).astype(np.float32)


def frames(p, w=96, h=54):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", p, "-vf", f"scale={w}:{h}", "-f", "rawvideo", "-pix_fmt", "gray", "-"],
                         capture_output=True).stdout
    return np.frombuffer(raw, np.uint8).reshape(-1, h, w).astype(np.float32)


def cuts(fr, thresh=28):
    d = np.abs(np.diff(fr, axis=0)).mean(axis=(1, 2))
    return [i + 1 for i in np.nonzero(d > thresh)[0]], d


a_path, b_path = sys.argv[1], sys.argv[2]
A, B = audio(a_path), audio(b_path)
n = min(len(A), len(B))
print(f"audio samples {len(A)} vs {len(B)}; max abs diff {np.abs(A[:n] - B[:n]).max():.0f}; identical={np.array_equal(A[:n], B[:n])}")
# cross-correlation lag (in ms) between the two audio tracks
c = np.correlate(A[:n:4], B[:n:4], "full")
lag = (np.argmax(c) - (n // 4 - 1)) * 4 / 8000 * 1000
print(f"audio lag a->b: {lag:.1f} ms")

FA, FB = frames(a_path), frames(b_path)
ca, da = cuts(FA)
cb, db = cuts(FB)
print("cuts a:", ca)
print("cuts b:", cb)
# where do the two renders differ most in their frame-to-frame motion pattern?
m = min(len(da), len(db))
corr_shift = []
for s in (-3, -2, -1, 0, 1, 2, 3):
    x = da[max(0, s):m + min(0, s)]
    y = db[max(0, -s):m - max(0, s)]
    corr_shift.append((s, float(np.corrcoef(x, y)[0, 1])))
print("motion-pattern correlation by frame shift (b relative to a):", corr_shift)
