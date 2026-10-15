"""Restore faces with GFPGAN v1.4 (CPU). OPTIONAL and risky: on blurry phone footage it can redraw a real
person's eyes, nose and brows. Always show a side-by-side (original / upscaled / restored) and get approval
before batch use; prefer --weight 0.3-0.5 or skip it.

Usage: python enhance_face.py <in_dir_or_file> <out_dir> [--weight 0.6]
Get the model with: python fetch_tools.py --only gfpgan
"""
import argparse, glob, os, sys, types

import torchvision.transforms.functional as _F
sys.modules.setdefault("torchvision.transforms.functional_tensor", types.SimpleNamespace(rgb_to_grayscale=_F.rgb_to_grayscale))
import cv2
from gfpgan import GFPGANer

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _paths import models_dir

MODEL = os.path.join(models_dir("gfpgan"), "GFPGANv1.4.pth")
ap = argparse.ArgumentParser()
ap.add_argument("src"); ap.add_argument("out")
ap.add_argument("--weight", type=float, default=0.6, help="0 = keep original face, 1 = fully restored")
a = ap.parse_args()
files = [a.src] if os.path.isfile(a.src) else sorted(glob.glob(os.path.join(a.src, "*.png")) + glob.glob(os.path.join(a.src, "*.jpg")))
os.makedirs(a.out, exist_ok=True)
# facexlib helper weights (face detector, parser) download next to the GFPGAN model.
os.chdir(models_dir("gfpgan"))
restorer = GFPGANer(model_path=MODEL, upscale=1, arch="clean", channel_multiplier=2, bg_upsampler=None, device="cpu")
for i, f in enumerate(files):
    img = cv2.imread(os.path.abspath(f), cv2.IMREAD_COLOR)
    _, _, out = restorer.enhance(img, has_aligned=False, only_center_face=False, paste_back=True, weight=a.weight)
    cv2.imwrite(os.path.join(os.path.abspath(a.out), os.path.splitext(os.path.basename(f))[0] + ".png"), out)
    print(f"{i + 1}/{len(files)} {os.path.basename(f)}", flush=True)
