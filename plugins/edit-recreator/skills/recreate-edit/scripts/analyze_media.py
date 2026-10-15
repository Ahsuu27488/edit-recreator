"""Score every photo and video frame in a folder for face quality, and build contact sheets.

Usage: python analyze_media.py <media_dir> <out_dir> [--fps 2]
(face-detector weights download once to $EDIT_RECREATOR_MODELS, default ~/.cache/edit-recreator/models)

Writes <out_dir>/scores.csv plus one contact sheet per video and one for all photos.
Scores per frame:
  face_h    face height as a fraction of the frame height (bigger = closer shot)
  sharp     variance of the Laplacian on the face crop, normalised to 256 px (higher = sharper)
  bright    mean luma of the face crop (0-255)
  frontal   1.0 = nose centred between the eyes, lower = turned away
  roll      head tilt in degrees; near +/-90 means the footage is stored sideways
"""
import argparse, csv, glob, json, os, subprocess, sys, tempfile, types

import torchvision.transforms.functional as _F
sys.modules.setdefault("torchvision.transforms.functional_tensor",
                       types.SimpleNamespace(rgb_to_grayscale=_F.rgb_to_grayscale))

import cv2
import numpy as np
import torch
from PIL import Image, ImageDraw, ImageFont
from facexlib.detection import init_detection_model

IMG_EXT = {".jpg", ".jpeg", ".png", ".webp", ".bmp"}
VID_EXT = {".mp4", ".mov", ".m4v", ".3gp", ".mkv", ".webm", ".avi"}
DET_SIDE = 640  # detect on a downscaled copy for speed

ap = argparse.ArgumentParser()
ap.add_argument("src"); ap.add_argument("out")
ap.add_argument("--fps", type=float, default=2.0)
a = ap.parse_args()
os.makedirs(a.out, exist_ok=True)

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _paths import models_dir
det = init_detection_model("retinaface_resnet50", half=False, device="cpu", model_rootpath=models_dir("facexlib"))
from _paths import font as _font
FONT = _font(16)


def score(img):
    h, w = img.shape[:2]
    k = DET_SIDE / max(h, w)
    small = cv2.resize(img, (int(w * k), int(h * k))) if k < 1 else img
    k = min(k, 1.0)
    with torch.no_grad():
        faces = det.detect_faces(small, 0.9)
    if faces is None or len(faces) == 0:
        return dict(faces=0, face_h=0, sharp=0, bright=0, frontal=0, roll=0, box=None)
    f = max(faces, key=lambda b: (b[2] - b[0]) * (b[3] - b[1]))
    x1, y1, x2, y2 = (np.array(f[:4]) / k).astype(int)
    x1, y1 = max(x1, 0), max(y1, 0)
    crop = img[y1:y2, x1:x2]
    if crop.size == 0:
        return dict(faces=len(faces), face_h=0, sharp=0, bright=0, frontal=0, roll=0, box=None)
    g = cv2.cvtColor(cv2.resize(crop, (256, 256)), cv2.COLOR_BGR2GRAY)
    lm = np.array(f[5:15]).reshape(5, 2) / k  # eyes, nose, mouth corners
    eye_l, eye_r, nose = lm[0], lm[1], lm[2]
    eyes = eye_r - eye_l
    # Where the nose projects along the eye line: 0.5 = centred, i.e. facing the camera.
    t = float(np.dot(nose - eye_l, eyes) / (np.dot(eyes, eyes) + 1e-6))
    frontal = max(0.0, 1 - abs(t - 0.5) * 2)
    # Head tilt in degrees; around ±90 means the footage itself is sideways.
    roll = float(np.degrees(np.arctan2(eyes[1], eyes[0])))
    return dict(faces=len(faces), face_h=round((y2 - y1) / h, 3),
                sharp=round(float(cv2.Laplacian(g, cv2.CV_64F).var()), 1),
                bright=round(float(g.mean()), 1), frontal=round(frontal, 2),
                roll=round(roll), box=[int(x1), int(y1), int(x2), int(y2)])


def sheet(items, path, cols=6, tw=320):
    """items: list of (bgr_image, label, good:bool)."""
    if not items:
        return
    th = tw * 9 // 16 if items[0][0].shape[1] >= items[0][0].shape[0] else tw * 16 // 9
    rows = (len(items) + cols - 1) // cols
    out = Image.new("RGB", (cols * tw, rows * (th + 22)), (30, 30, 30))
    d = ImageDraw.Draw(out)
    for i, (im, label, good) in enumerate(items):
        pil = Image.fromarray(cv2.cvtColor(im, cv2.COLOR_BGR2RGB))
        pil.thumbnail((tw, th))
        x, y = (i % cols) * tw, (i // cols) * (th + 22)
        out.paste(pil, (x + (tw - pil.width) // 2, y))
        d.text((x + 4, y + th + 2), label, fill=(120, 255, 120) if good else (230, 230, 230), font=FONT)
    out.save(path, quality=88)


rows = []
files = sorted(f for f in glob.glob(os.path.join(a.src, "*")) if os.path.isfile(f))
photo_items = []
for f in files:
    name, ext = os.path.basename(f), os.path.splitext(f)[1].lower()
    if ext in IMG_EXT:
        img = cv2.imdecode(np.fromfile(f, np.uint8), cv2.IMREAD_COLOR)
        if img is None:
            continue
        s = score(img)
        rows.append(dict(file=name, kind="photo", t="", w=img.shape[1], h=img.shape[0], **s))
        photo_items.append((img, f"{len(photo_items)}: sh{s['sharp']:.0f} fh{s['face_h']}", s["sharp"] > 120 and s["face_h"] > 0.12))
        print(f"photo {name}: {s}", flush=True)
    elif ext in VID_EXT:
        with tempfile.TemporaryDirectory() as td:
            # ffmpeg applies rotation metadata automatically, so frames come out upright
            subprocess.run(["ffmpeg", "-v", "error", "-i", f, "-vf", f"fps={a.fps},scale='min(1280,iw)':-2",
                            os.path.join(td, "%05d.png")], check=True)
            frames = sorted(glob.glob(os.path.join(td, "*.png")))
            items = []
            for i, fr in enumerate(frames):
                img = cv2.imread(fr)
                t = round(i / a.fps, 2)
                s = score(img)
                rows.append(dict(file=name, kind="video", t=t, w=img.shape[1], h=img.shape[0], **s))
                items.append((img, f"{t:5.1f}s sh{s['sharp']:.0f} fh{s['face_h']}", s["sharp"] > 120 and s["face_h"] > 0.12))
            sheet(items, os.path.join(a.out, f"video_{os.path.splitext(name)[0]}.jpg"))
            print(f"video {name}: {len(frames)} frames scored", flush=True)

sheet(photo_items, os.path.join(a.out, "photos.jpg"), cols=6, tw=300)
with open(os.path.join(a.out, "scores.csv"), "w", newline="", encoding="utf-8") as fh:
    wr = csv.DictWriter(fh, fieldnames=["file", "kind", "t", "w", "h", "faces", "face_h", "sharp", "bright", "frontal", "roll", "box"])
    wr.writeheader()
    for r in rows:
        r = dict(r); r["box"] = json.dumps(r["box"]); wr.writerow(r)
print(f"done: {len(rows)} rows -> {a.out}")
