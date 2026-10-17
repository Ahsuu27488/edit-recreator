"""Map a song: tempo, beat grid, loudness per 2 s, the biggest drops, and where to start it.

Usage: python song_map.py <song.mp3> [--out beats.json] [--land 28.9] [--drop 173.2] [--hook 40]
  --land T   your video moment (seconds) that the drop must hit, e.g. the big reveal
  --drop S   which drop to use (song seconds); default: the biggest energy jump
  --hook S   print where else this 8 s phrase repeats (the chorus/hook coming back)
Prints the song start offset (start = drop - land, snapped to a beat) and the beat grid in video time,
so cuts can sit on beats. Needs librosa (requirements-audio.txt).
"""
import argparse, json
import numpy as np, librosa

ap = argparse.ArgumentParser()
ap.add_argument("song"); ap.add_argument("--out", default="beats.json")
ap.add_argument("--land", type=float); ap.add_argument("--drop", type=float); ap.add_argument("--hook", type=float)
a = ap.parse_args()

y, sr = librosa.load(a.song, sr=22050, mono=True)
tempo, beats = librosa.beat.beat_track(y=y, sr=sr)
tempo = float(np.atleast_1d(tempo)[0])
bt = librosa.frames_to_time(beats, sr=sr)
rms = librosa.feature.rms(y=y)[0]
t = librosa.frames_to_time(np.arange(len(rms)), sr=sr)
print(f"tempo {tempo:.1f} BPM, {len(bt)} beats, beat = {60 / tempo:.3f}s")

mx = rms.max()
for s in np.arange(0, t[-1], 2.0):
    m = (t >= s) & (t < s + 2)
    print(f"{s:6.1f}s {'#' * int(40 * rms[m].mean() / mx)}")

# drops: mean energy of the next 4 s minus the previous 4 s
w = int(4 * sr / 512)
jumps = sorted(((rms[i:i + w].mean() - rms[i - w:i].mean(), t[i]) for i in range(w, len(rms) - w)), reverse=True)
drops = []
for d, tt in jumps:
    if all(abs(tt - p) > 8 for _, p in drops):
        drops.append((d, tt))
    if len(drops) == 6:
        break
print("biggest drops (song s):", ", ".join(f"{tt:.2f}" for _, tt in drops))

if a.hook is not None:
    c = librosa.feature.chroma_cqt(y=y, sr=sr, hop_length=2048)
    fps = sr / 2048
    ref = c[:, int(a.hook * fps):int((a.hook + 8) * fps)]
    n = ref.shape[1]
    sims = []
    for s in np.arange(0, len(y) / sr - 8, 1.0):
        win = c[:, int(s * fps):int(s * fps) + n]
        if win.shape[1] == n:
            sims.append((float(np.corrcoef(ref.ravel(), win.ravel())[0, 1]), s))
    sims.sort(reverse=True)
    print("hook repeats at (s, similarity):", ", ".join(f"{s:.0f} ({v:.2f})" for v, s in sims[:8]))

out = {"tempo": tempo, "beats": bt.round(3).tolist(), "drops": [round(tt, 2) for _, tt in drops]}
if a.land is not None:
    drop = a.drop if a.drop is not None else drops[0][1]
    drop = float(min(bt, key=lambda b: abs(b - drop)))  # snap to the nearest beat
    start = drop - a.land
    print(f"drop {drop:.3f}s -> start the song at {start:.3f}s ({int(start // 60)}:{start % 60:04.1f}) "
          f"so it hits video {a.land:.2f}s")
    grid = [round(b - start, 3) for b in bt if 0 <= b - start <= a.land + 30]
    print("beats in video time:", ", ".join(f"{g:.2f}" for g in grid[:40]), "...")
    out.update({"drop": drop, "start": round(start, 3), "video_beats": grid})
json.dump(out, open(a.out, "w"))
print("wrote", a.out)
