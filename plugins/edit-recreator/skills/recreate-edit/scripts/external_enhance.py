"""Use an external/app enhancer (phone or desktop apps that charge per video) on ALL clips with ONE job.

Many enhancement apps give a few free runs per video regardless of length. Join every clip into one video
per orientation, enhance each joined video once in the app, then split the results back into clips.

    python external_enhance.py join  <out_dir> <clip> [clip ...]      # writes landscape.mp4 / portrait.mp4 + split_map.json
    python external_enhance.py split <out_dir> <enhanced_landscape.mp4|-> <enhanced_portrait.mp4|->

Clips are normalised to 30 fps and stored upright (rotation metadata applied; pass clip@90 / clip@270 to
rotate a clip that is stored sideways WITHOUT metadata). split writes <out_dir>/split/<clip-stem>.mp4 with
exactly the original frame counts. Check the app's privacy terms before uploading anyone's footage.
"""
import json, os, subprocess, sys

ROT = {"90": "transpose=1,", "180": "transpose=1,transpose=1,", "270": "transpose=2,"}


def probe_wh(path, pre):
    """Upright size after rotation metadata and any extra transpose: decode one frame and measure it."""
    import tempfile
    from PIL import Image
    tmp = os.path.join(tempfile.mkdtemp(), "f.png")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", path, "-vf", f"{pre}fps=30", "-frames:v", "1", tmp], check=True)
    return Image.open(tmp).size


def frames(path, pre):
    out = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-vf", f"{pre}fps=30", "-f", "null", "-", "-progress", "pipe:1"],
                         capture_output=True, text=True).stdout
    return int([l for l in out.splitlines() if l.startswith("frame=")][-1].split("=")[1])


def join(out_dir, clips):
    os.makedirs(out_dir, exist_ok=True)
    groups, smap = {"landscape": [], "portrait": []}, {}
    for spec in clips:
        path, _, rot = spec.partition("@")
        pre = ROT.get(rot, "")
        w, h = probe_wh(path, pre)
        groups["landscape" if w >= h else "portrait"].append((path, pre, frames(path, pre)))
    for g, items in groups.items():
        if not items:
            continue
        args, fil, start, entries = [], "", 0, []
        for i, (p, pre, n) in enumerate(items):
            args += ["-i", p]
            fil += f"[{i}:v]{pre}fps=30,setsar=1[v{i}];"
            entries.append({"clip": os.path.basename(p), "start": start, "frames": n})
            start += n
        fil += "".join(f"[v{i}]" for i in range(len(items))) + f"concat=n={len(items)}:v=1:a=0"
        dest = os.path.join(out_dir, f"{g}.mp4")
        subprocess.run(["ffmpeg", "-v", "error", "-y", *args, "-filter_complex", fil, "-c:v", "libx264", "-crf", "10",
                        "-preset", "slow", "-pix_fmt", "yuv420p", "-an", dest], check=True)
        smap[g] = entries
        print("wrote", dest, f"({start} frames)")
    json.dump(smap, open(os.path.join(out_dir, "split_map.json"), "w"), indent=1)


def split(out_dir, enhanced):
    smap = json.load(open(os.path.join(out_dir, "split_map.json")))
    os.makedirs(os.path.join(out_dir, "split"), exist_ok=True)
    for g, src in zip(("landscape", "portrait"), enhanced):
        if src == "-" or g not in smap:
            continue
        for e in smap[g]:
            a, b = e["start"], e["start"] + e["frames"] - 1
            dest = os.path.join(out_dir, "split", os.path.splitext(e["clip"])[0] + ".mp4")
            subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", src, "-vf", f"select='between(n\\,{a}\\,{b})',setpts=N/30/TB",
                            "-r", "30", "-c:v", "libx264", "-crf", "10", "-preset", "slow", "-pix_fmt", "yuv420p", "-an", dest], check=True)
            print("split", dest)


if __name__ == "__main__":
    cmd, out_dir = sys.argv[1], sys.argv[2]
    join(out_dir, sys.argv[3:]) if cmd == "join" else split(out_dir, sys.argv[3:5])
