"""BiRefNet-portrait background removal (onnx-community export of BiRefNet, MIT), CPU via onnxruntime.

    from birefnet_cut import mask_for;  mask = mask_for(pil_image)  # "L" mask, same size

CLI: python birefnet_cut.py <in.png> <out.png>   (writes an RGBA cut-out)

Much better than u2net / isnet on hair, pale hands and white fabric against a white wall. Slow on CPU
(~20 s per frame on a laptop i7), so prep_slots.py masks only the REAL frames and lets RIFE interpolate
the in-between masks. Get the model with: python fetch_tools.py --only birefnet
"""
import os, sys
import numpy as np
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _paths import models_dir

MODEL = os.environ.get("BIREFNET_MODEL") or os.path.join(models_dir("birefnet"), "birefnet-portrait.onnx")
MEAN = np.array([0.485, 0.456, 0.406], np.float32)
STD = np.array([0.229, 0.224, 0.225], np.float32)
_sess = None


def _session():
    global _sess
    if _sess is None:
        if not os.path.exists(MODEL):
            raise SystemExit(f"BiRefNet model missing at {MODEL}; run: python fetch_tools.py --only birefnet")
        import onnxruntime as ort
        opts = ort.SessionOptions()
        opts.intra_op_num_threads = os.cpu_count() or 4
        _sess = ort.InferenceSession(MODEL, opts, providers=ort.get_available_providers())
    return _sess


def mask_for(img: Image.Image) -> Image.Image:
    s = _session()
    x = np.asarray(img.convert("RGB").resize((1024, 1024), Image.BILINEAR), np.float32) / 255.0
    x = ((x - MEAN) / STD).transpose(2, 0, 1)[None]
    out = s.run(None, {s.get_inputs()[0].name: x})[-1]
    m = out.reshape(out.shape[-2], out.shape[-1])
    if m.min() < 0 or m.max() > 1:  # logits
        m = 1 / (1 + np.exp(-m))
    return Image.fromarray((m * 255).clip(0, 255).astype(np.uint8)).resize(img.size, Image.BILINEAR)


if __name__ == "__main__":
    im = Image.open(sys.argv[1]).convert("RGB")
    out = im.convert("RGBA")
    out.putalpha(mask_for(im))
    out.save(sys.argv[2])
