"""Download the open-source tools and model weights the pipeline uses (once), into $EDIT_RECREATOR_HOME.

Usage: python fetch_tools.py [--only rife,realesrgan,birefnet,gfpgan]

Everything comes from its official release (licences: RIFE ncnn MIT, Real-ESRGAN BSD-3, BiRefNet MIT,
GFPGAN Apache-2.0). Large files download in parallel byte ranges, which is much faster than one stream on
slow links (the same trick a download manager uses). Nothing is bundled in this repo.
"""
import argparse, os, platform, subprocess, sys, urllib.request, zipfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _paths import bin_dir, models_dir

OS = {"Windows": "windows", "Darwin": "macos", "Linux": "ubuntu"}[platform.system()]
TOOLS = {
    "rife": dict(kind="zip", dest=bin_dir("rife"),
                 url=f"https://github.com/nihui/rife-ncnn-vulkan/releases/download/20221029/rife-ncnn-vulkan-20221029-{OS}.zip",
                 keep=("rife-ncnn-vulkan", "rife-v4.6/", ".dll", "LICENSE")),
    "realesrgan": dict(kind="zip", dest=bin_dir("realesrgan"),
                       url=f"https://github.com/xinntao/Real-ESRGAN/releases/download/v0.2.5.0/realesrgan-ncnn-vulkan-20220424-{OS}.zip",
                       keep=None),
    "birefnet": dict(kind="file", dest=os.path.join(models_dir("birefnet"), "birefnet-portrait.onnx"),
                     url="https://huggingface.co/onnx-community/BiRefNet-portrait-ONNX/resolve/main/onnx/model.onnx"),
    "gfpgan": dict(kind="file", dest=os.path.join(models_dir("gfpgan"), "GFPGANv1.4.pth"),
                   url="https://github.com/TencentARC/GFPGAN/releases/download/v1.3.0/GFPGANv1.4.pth"),
}


def size_of(url):
    req = urllib.request.Request(url, method="HEAD")
    with urllib.request.urlopen(req) as r:
        return int(r.headers["Content-Length"])


def fetch(url, dest):
    if os.path.exists(dest) and os.path.getsize(dest) > 0:
        print("have", dest); return
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    script = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fetch_parallel.sh")
    try:
        subprocess.run(["bash", script, url, str(size_of(url)), dest, "8"], check=True)
    except (FileNotFoundError, subprocess.CalledProcessError):
        print("parallel download unavailable, falling back to a single stream")
        urllib.request.urlretrieve(url, dest)
    print("got", dest)


ap = argparse.ArgumentParser()
ap.add_argument("--only", default=",".join(TOOLS))
a = ap.parse_args()
for name in a.only.split(","):
    t = TOOLS[name]
    if t["kind"] == "file":
        fetch(t["url"], t["dest"])
        continue
    z = os.path.join(t["dest"], "download.zip")
    fetch(t["url"], z)
    with zipfile.ZipFile(z) as zf:
        for m in zf.namelist():
            if m.endswith("/") or (t["keep"] and not any(k in m for k in t["keep"])):
                continue
            out = os.path.join(t["dest"], m.split("/", 1)[-1] if "/" in m else m)
            os.makedirs(os.path.dirname(out), exist_ok=True)
            with open(out, "wb") as fh:
                fh.write(zf.read(m))
    os.remove(z)
    if OS != "windows":
        for root, _, files in os.walk(t["dest"]):
            for f in files:
                if f.endswith("ncnn-vulkan"):
                    os.chmod(os.path.join(root, f), 0o755)
    print("installed", name, "->", t["dest"])
