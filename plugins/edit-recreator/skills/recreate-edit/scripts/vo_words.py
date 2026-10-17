"""Word timings for a voiceover (for captions and cutting scenes on words), with faster-whisper.

Usage: python vo_words.py <vo.mp3|wav> <out.json> [--model small] [--lang en] [--from 0] [--to 0]
Writes [{"w": word, "s": start, "e": end}, ...] in seconds (UTF-8). --from/--to transcribe a slice and keep
times in the full file's clock: use it when whisper stops early or garbles a long take (it happens with
Hindi and other non-English reads), then join the slices.
If whisper can't read a language well, use phrase starts from silencedetect instead (see reference/sound.md).
"""
import argparse, json, subprocess
import numpy as np
from faster_whisper import WhisperModel

ap = argparse.ArgumentParser()
ap.add_argument("audio"); ap.add_argument("out")
ap.add_argument("--model", default="small"); ap.add_argument("--lang", default="en")
ap.add_argument("--from", dest="t0", type=float, default=0.0); ap.add_argument("--to", dest="t1", type=float, default=0.0)
a = ap.parse_args()

cmd = ["ffmpeg", "-v", "error", "-ss", str(a.t0), "-i", a.audio]
if a.t1 > a.t0:
    cmd += ["-t", str(a.t1 - a.t0)]
raw = subprocess.run(cmd + ["-f", "s16le", "-ac", "1", "-ar", "16000", "-"], capture_output=True).stdout
audio = np.frombuffer(raw, np.int16).astype(np.float32) / 32768

model = WhisperModel(a.model, device="cpu", compute_type="int8")
segs, _ = model.transcribe(audio, language=a.lang, word_timestamps=True, vad_filter=False)
words = [{"w": w.word.strip(), "s": round(w.start + a.t0, 3), "e": round(w.end + a.t0, 3)} for s in segs for w in s.words]
json.dump(words, open(a.out, "w", encoding="utf-8"), indent=0, ensure_ascii=False)
print(f"{len(words)} words, {words[0]['s'] if words else 0:.2f}s to {words[-1]['e'] if words else 0:.2f}s -> {a.out}")
