"""Turn the footage chosen for each scene ("slot") into image sequences a Remotion project can play.

Usage:
    python prep_slots.py <slots.json> --project <remotion_dir> --variant original [--only s01,s02] [--force]
                         [--external-dir work/external/split] [--gpu 0]

Variants (one full set of slots each; render one with --props='{"variant":"<name>"}'):
    original  the footage untouched
    external  the footage after an app/online enhancer (see external_enhance.py); read from --external-dir
    x4        Real-ESRGAN x4plus upscale only (faithful to faces, slow)
    x4gfp     Real-ESRGAN x4plus, then GFPGAN face restore (sharpest, but CAN CHANGE A REAL FACE; get approval)
All variants get RIFE slow-motion frames when a slot asks for them.

slots.json maps a slot name to (paths relative to the slots.json file):
    src       video or photo
    start     seconds into the video (videos only)
    dur       seconds to extract
    rotate    0 / 90 / 180 / 270 extra clockwise rotation (footage stored sideways without metadata)
    cut       true to also write a background-removed copy (cut/ folder, WebP with alpha)
    model     cut-out model: "birefnet" (best, slow) or a rembg model name (u2net_human_seg, isnet-general-use)
    interp    N: add N-1 RIFE in-between frames per real frame (smooth slow motion). Scene code keeps
              counting SOURCE frames; slotIndex() maps them onto the in-between files.

Output: <project>/public/slots/<variant>/<slot>/full/0000.jpg, cut/0000.webp, face.json, meta.json,
and <project>/src/slots.gen.ts (every variant's frame counts, sizes, median face box; VARIANT from props).
"""
import argparse, glob, json, os, shutil, statistics, subprocess, sys, types

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from _paths import bin_dir, find_exe, models_dir

VARIANTS = ("original", "external", "x4", "x4gfp")
FPS = 30
MAX_SIDE = 2160  # cap stored frame size: enough for a 1080p output with some zoom
IMG_EXT = {".jpg", ".jpeg", ".png", ".webp", ".bmp"}
ROT = {90: "transpose=1", 180: "transpose=1,transpose=1", 270: "transpose=2"}
os.environ.setdefault("U2NET_HOME", models_dir("rembg"))


def run(cmd, **kw):
    subprocess.run(cmd, check=True, **kw)


def source_for(a, cfg, base_dir):
    src, rot = os.path.join(base_dir, cfg["src"]), cfg.get("rotate")
    stem, ext = os.path.splitext(os.path.basename(src))
    if a.variant == "external" and ext.lower() not in IMG_EXT:
        ext_src = os.path.join(a.external_dir, stem + ".mp4")
        if not os.path.exists(ext_src):
            raise SystemExit(f"no enhanced version of {src} in {a.external_dir} (run external_enhance.py split)")
        return ext_src, None  # external_enhance.py already stored it upright
    return src, rot


def extract(src, rot, cfg, tmp):
    vf = [ROT[rot]] if rot else []
    vf.append(f"scale='if(gt(iw,ih),min({MAX_SIDE},iw),-2)':'if(gt(iw,ih),-2,min({MAX_SIDE},ih))'")
    out = os.path.join(tmp, "%04d.png")
    if os.path.splitext(src)[1].lower() in IMG_EXT:
        run(["ffmpeg", "-v", "error", "-y", "-i", src, "-vf", ",".join(vf), "-frames:v", "1", out.replace("%04d", "0001")])
    else:
        vf.insert(0, f"fps={FPS}")
        run(["ffmpeg", "-v", "error", "-y", "-ss", str(cfg.get("start", 0)), "-t", str(cfg["dur"]), "-i", src, "-vf", ",".join(vf), out])
    return sorted(glob.glob(os.path.join(tmp, "*.png")))


def upscale(frames_dir, out_dir, gpu):
    from PIL import Image
    exe = find_exe(bin_dir("realesrgan"), "realesrgan-ncnn-vulkan")
    os.makedirs(out_dir, exist_ok=True)
    # x4plus only works reliably at -s 4 (at -s 2 its tiles come out scrambled); shrink afterwards.
    run([exe, "-i", frames_dir, "-o", out_dir, "-n", "realesrgan-x4plus", "-s", "4", "-g", str(gpu), "-f", "png"],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, cwd=os.path.dirname(exe))
    for f in glob.glob(os.path.join(out_dir, "*.png")):
        im = Image.open(f)
        if max(im.size) > MAX_SIDE:
            im.thumbnail((MAX_SIDE, MAX_SIDE), Image.LANCZOS)
            im.save(f)


def interpolate(frames_dir, out_dir, k, gpu):
    """RIFE v4.6: k output frames per input frame across the sequence."""
    exe = find_exe(bin_dir("rife"), "rife-ncnn-vulkan")
    n = len(glob.glob(os.path.join(frames_dir, "*.png")))
    os.makedirs(out_dir, exist_ok=True)
    model = os.path.join(os.path.dirname(exe), "rife-v4.6")
    run([exe, "-i", frames_dir, "-o", out_dir, "-m", model, "-n", str((n - 1) * k + 1), "-g", str(gpu), "-f", "%08d.png"],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, cwd=os.path.dirname(exe))


_detector = None


def measure_face(full_dir):
    """Median face box over the slot, normalised to the frame: {cx, cy, h}."""
    global _detector
    import numpy as np
    import torchvision.transforms.functional as _F
    sys.modules.setdefault("torchvision.transforms.functional_tensor", types.SimpleNamespace(rgb_to_grayscale=_F.rgb_to_grayscale))
    import cv2, torch
    from facexlib.detection import init_detection_model
    if _detector is None:
        _detector = init_detection_model("retinaface_resnet50", half=False, device="cpu", model_rootpath=models_dir("facexlib"))
    files = sorted(glob.glob(os.path.join(full_dir, "*.jpg")))
    cxs, cys, hs = [], [], []
    for f in files[:: max(1, len(files) // 12)] or files:
        img = cv2.imread(f)
        h, w = img.shape[:2]
        k = 640 / max(h, w)
        with torch.no_grad():
            faces = _detector.detect_faces(cv2.resize(img, (int(w * k), int(h * k))), 0.8)
        if faces is None or len(faces) == 0:
            continue
        b = max(faces, key=lambda b: (b[2] - b[0]) * (b[3] - b[1]))
        x1, y1, x2, y2 = np.array(b[:4]) / k
        cxs.append((x1 + x2) / 2 / w); cys.append((y1 + y2) / 2 / h); hs.append((y2 - y1) / h)
    if not hs:
        return None
    return {"cx": round(float(statistics.median(cxs)), 4), "cy": round(float(statistics.median(cys)), 4), "h": round(float(statistics.median(hs)), 4)}


def write_gen_ts(public, gen_ts, names):
    from PIL import Image
    sets = {}
    for vdir in sorted(glob.glob(os.path.join(public, "*"))):
        v = os.path.basename(vdir)
        if v not in VARIANTS:
            continue
        info = {}
        for d in sorted(glob.glob(os.path.join(vdir, "*"))):
            full = sorted(glob.glob(os.path.join(d, "full", "*.jpg")))
            if not full:
                continue
            w, h = Image.open(full[0]).size
            face = json.load(open(os.path.join(d, "face.json"))) if os.path.exists(os.path.join(d, "face.json")) else None
            meta = json.load(open(os.path.join(d, "meta.json"))) if os.path.exists(os.path.join(d, "meta.json")) else {}
            k = int(meta.get("interp", 1))
            info[os.path.basename(d)] = dict(frames=(len(full) - 1) // k + 1, files=len(full), interp=k, width=w, height=h,
                                             cut=os.path.isdir(os.path.join(d, "cut")), face=face or {"cx": 0.5, "cy": 0.35, "h": 0.2})
        sets[v] = info
    default = next(iter(sets), "original")
    lines = [
        "// Generated by prep_slots.py. Do not edit by hand.",
        "import { getInputProps } from 'remotion';",
        "",
        f"export const SLOT_NAMES = {json.dumps(names)} as const;",
        "export type SlotName = (typeof SLOT_NAMES)[number];",
        "export type SlotInfo = { frames: number; files: number; interp: number; width: number; height: number; cut: boolean; face: { cx: number; cy: number; h: number } };",
        f"export const SLOT_SETS: Record<string, Partial<Record<SlotName, SlotInfo>>> = {json.dumps(sets, indent=2)};",
        "const wanted = (getInputProps() as { variant?: string }).variant;",
        f"export const VARIANT = wanted && wanted in SLOT_SETS ? wanted : {json.dumps(default)};",
        "export const SLOT_ROOT = `slots/${VARIANT}`;",
        "const MISSING: SlotInfo = { frames: 1, files: 1, interp: 1, width: 1920, height: 1080, cut: false, face: { cx: 0.5, cy: 0.35, h: 0.2 } };",
        "export const SLOTS = new Proxy({} as Record<SlotName, SlotInfo>, { get: (_, k: string) => SLOT_SETS[VARIANT]?.[k as SlotName] ?? MISSING });",
    ]
    os.makedirs(os.path.dirname(gen_ts), exist_ok=True)
    open(gen_ts, "w", encoding="utf-8").write("\n".join(lines) + "\n")
    print(f"wrote {gen_ts} ({', '.join(f'{v}: {len(i)}' for v, i in sets.items())})")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("config")
    ap.add_argument("--project", required=True, help="Remotion project directory")
    ap.add_argument("--variant", choices=VARIANTS, required=True)
    ap.add_argument("--external-dir", default="work/external/split")
    ap.add_argument("--only", default="")
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--gpu", default="0", help="Vulkan GPU index for RIFE / Real-ESRGAN (-1 = CPU)")
    a = ap.parse_args()
    from PIL import Image
    sys.path.insert(0, HERE)
    from solid_mask import solidify

    cfg_path = os.path.abspath(a.config)
    base_dir = os.path.dirname(cfg_path)
    slots = json.load(open(cfg_path, encoding="utf-8"))
    only = set(filter(None, a.only.split(",")))
    public = os.path.join(os.path.abspath(a.project), "public", "slots")
    work = os.path.join(base_dir, "work", "prep")
    sessions = {}
    for slot, cfg in slots.items():
        if slot.startswith("_") or (only and slot not in only):
            continue
        dest = os.path.join(public, a.variant, slot)
        if os.path.isdir(dest) and not a.force:
            print(f"[{slot}] exists, skipping (use --force)"); continue
        shutil.rmtree(dest, ignore_errors=True)
        tmp = os.path.join(work, a.variant, slot)
        shutil.rmtree(tmp, ignore_errors=True)
        os.makedirs(os.path.join(tmp, "raw"))
        src, rot = source_for(a, cfg, base_dir)
        frames = extract(src, rot, cfg, os.path.join(tmp, "raw"))
        print(f"[{a.variant}/{slot}] {len(frames)} frames from {os.path.basename(src)}", flush=True)
        src_dir = os.path.join(tmp, "raw")
        if a.variant in ("x4", "x4gfp"):
            upscale(src_dir, os.path.join(tmp, "up"), a.gpu)
            src_dir = os.path.join(tmp, "up")
            if a.variant == "x4gfp":
                run([sys.executable, os.path.join(HERE, "enhance_face.py"), src_dir, os.path.join(tmp, "enh"), "--weight", "0.5"])
                src_dir = os.path.join(tmp, "enh")
            print(f"[{slot}] enhanced ({a.variant})", flush=True)

        k = int(cfg.get("interp", 1)) if len(frames) > 1 else 1
        model = cfg.get("model", "birefnet")
        mask_dir = None
        if cfg.get("cut") and model == "birefnet":
            from birefnet_cut import mask_for
            mask_dir = os.path.join(tmp, "mask")
            os.makedirs(mask_dir)
            for f in sorted(glob.glob(os.path.join(src_dir, "*.png"))):
                mask_for(Image.open(f)).convert("RGB").save(os.path.join(mask_dir, os.path.basename(f)))
            print(f"[{slot}] BiRefNet masks", flush=True)
        if k > 1:
            interpolate(src_dir, os.path.join(tmp, "rife"), k, a.gpu)
            src_dir = os.path.join(tmp, "rife")
            if mask_dir:  # the in-between masks come from RIFE too (BiRefNet is slow on CPU)
                interpolate(mask_dir, os.path.join(tmp, "rife_mask"), k, a.gpu)
                mask_dir = os.path.join(tmp, "rife_mask")
            print(f"[{slot}] RIFE x{k}", flush=True)

        os.makedirs(os.path.join(dest, "full"))
        session = None
        if cfg.get("cut"):
            os.makedirs(os.path.join(dest, "cut"))
            if model != "birefnet":
                from rembg import new_session
                session = sessions.setdefault(model, new_session(model))
        masks = sorted(glob.glob(os.path.join(mask_dir, "*.png"))) if mask_dir else None
        for i, f in enumerate(sorted(glob.glob(os.path.join(src_dir, "*.png")))):
            im = Image.open(f).convert("RGB")
            if max(im.size) > MAX_SIDE:
                im.thumbnail((MAX_SIDE, MAX_SIDE), Image.LANCZOS)
            im.save(os.path.join(dest, "full", f"{i:04d}.jpg"), quality=92)
            if cfg.get("cut"):
                if masks:
                    cut = im.convert("RGBA")
                    cut.putalpha(Image.open(masks[i]).convert("L").resize(im.size, Image.BILINEAR))
                else:
                    from rembg import remove
                    cut = remove(im, session=session, post_process_mask=True)
                # solidify: no see-through hair or fingers, no loose background specks
                solidify(cut).save(os.path.join(dest, "cut", f"{i:04d}.webp"), quality=90)
        face = measure_face(os.path.join(dest, "full"))
        json.dump(face, open(os.path.join(dest, "face.json"), "w"))
        json.dump({"interp": k, "source_frames": len(frames)}, open(os.path.join(dest, "meta.json"), "w"))
        print(f"[{slot}] written to {dest} (face {face})", flush=True)

    write_gen_ts(public, os.path.join(os.path.abspath(a.project), "src", "slots.gen.ts"),
                 [n for n in slots if not n.startswith("_")])


if __name__ == "__main__":
    main()
