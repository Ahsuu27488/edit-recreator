"""Track the subject's face through every frame of the reference edit.

Usage: python face_track.py <reference.mp4> <out.csv> [--offset 0] [--width 1920] [--height 1080] [--fps 30]

One row per frame in YOUR frame numbering (reference frame i -> your frame i - offset), in output-resolution
pixels: frame, faces, cx, cy, h (centre and height of the largest face), score, all boxes as JSON.
Feed these as face targets to Framed.tsx so the new footage gets the reference's framing, zooms and pans.
"""
import argparse, csv, json, os, subprocess, sys, types

import torchvision.transforms.functional as _F
sys.modules.setdefault("torchvision.transforms.functional_tensor", types.SimpleNamespace(rgb_to_grayscale=_F.rgb_to_grayscale))
import numpy as np
import torch
from facexlib.detection import init_detection_model

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _paths import models_dir

ap = argparse.ArgumentParser()
ap.add_argument("ref"); ap.add_argument("out")
ap.add_argument("--offset", type=int, default=0)
ap.add_argument("--width", type=int, default=1920); ap.add_argument("--height", type=int, default=1080)
ap.add_argument("--fps", type=float, default=30)
a = ap.parse_args()
W, H = 960, int(960 * a.height / a.width)  # detection size
raw = subprocess.run(["ffmpeg", "-v", "error", "-i", a.ref, "-vf", f"fps={a.fps},scale={W}:{H}", "-f", "rawvideo",
                      "-pix_fmt", "bgr24", "-"], capture_output=True).stdout
frames = np.frombuffer(raw, np.uint8).reshape(-1, H, W, 3)
det = init_detection_model("retinaface_resnet50", half=False, device="cpu", model_rootpath=models_dir("facexlib"))
k = a.width / W
with open(a.out, "w", newline="", encoding="utf-8") as fh:
    wr = csv.writer(fh)
    wr.writerow(["frame", "faces", "cx", "cy", "h", "score", "boxes"])
    for i, img in enumerate(frames):
        with torch.no_grad():
            faces = det.detect_faces(np.ascontiguousarray(img), 0.6)
        boxes = [] if faces is None else [[round(float(v) * k, 1) for v in b[:4]] + [round(float(b[4]), 3)] for b in faces]
        boxes.sort(key=lambda b: (b[2] - b[0]) * (b[3] - b[1]), reverse=True)
        if boxes:
            x1, y1, x2, y2, s = boxes[0]
            wr.writerow([i - a.offset, len(boxes), round((x1 + x2) / 2, 1), round((y1 + y2) / 2, 1), round(y2 - y1, 1), s, json.dumps(boxes)])
        else:
            wr.writerow([i - a.offset, 0, "", "", "", "", "[]"])
        if i % 50 == 0:
            print(f"{i}/{len(frames)}", flush=True)
print("done ->", a.out)
