"""Shorten long pauses in a voiceover without touching the speech.

Usage: python tighten_pauses.py <in.mp3|wav> <out.wav> [max_pause_s=0.25] [threshold_db=-35]
Each silence longer than max_pause is cut down to max_pause (half kept at each end). The cuts fall inside
silence, so they don't click. AI voices often read with 0.5-1 s gaps between phrases (non-English reads
especially); this can take a 51 s read down to 38 s without changing a word. Listen to the result, and keep
any dramatic pause you want by editing that one afterwards.
"""
import sys, subprocess, wave
import numpy as np

src, dst = sys.argv[1], sys.argv[2]
max_pause = float(sys.argv[3]) if len(sys.argv) > 3 else 0.25
thr_db = float(sys.argv[4]) if len(sys.argv) > 4 else -35.0
SR = 48000
raw = subprocess.run(["ffmpeg", "-v", "error", "-i", src, "-f", "s16le", "-ac", "1", "-ar", str(SR), "-"], capture_output=True).stdout
x = np.frombuffer(raw, np.int16).astype(np.float32) / 32768

win = int(0.02 * SR)
rms = np.sqrt(np.convolve(x * x, np.ones(win) / win, mode="same"))
quiet = 20 * np.log10(rms + 1e-9) < thr_db
edges = np.diff(np.concatenate([[0], quiet.astype(int), [0]]))
starts, ends = np.where(edges == 1)[0], np.where(edges == -1)[0]
keep = np.ones(len(x), bool)
cuts = 0
for s, e in zip(starts, ends):
    if s == 0 or e == len(x):
        continue  # leave the head and tail alone
    if (e - s) / SR > max_pause:
        half = int(max_pause * SR / 2)
        keep[s + half:e - half] = False
        cuts += 1
y = x[keep]
print(f"{cuts} pauses shortened; {len(x) / SR:.2f}s -> {len(y) / SR:.2f}s")
with wave.open(dst, "wb") as w:
    w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes((np.clip(y, -1, 1) * 32767).astype(np.int16).tobytes())
