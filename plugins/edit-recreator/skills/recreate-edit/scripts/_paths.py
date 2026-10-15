"""Where downloaded tools and model weights live (never inside the user's project, never in git).

EDIT_RECREATOR_HOME (default ~/.cache/edit-recreator) holds:
    models/<name>/   model weights (facexlib, gfpgan, birefnet, rembg)
    bin/<tool>/      ncnn-vulkan binaries (realesrgan, rife)
Run fetch_tools.py once to populate it.
"""
import os


def home() -> str:
    return os.environ.get("EDIT_RECREATOR_HOME", os.path.join(os.path.expanduser("~"), ".cache", "edit-recreator"))


def models_dir(name: str = "") -> str:
    p = os.environ.get("EDIT_RECREATOR_MODELS") or os.path.join(home(), "models")
    p = os.path.join(p, name) if name else p
    os.makedirs(p, exist_ok=True)
    return p


def bin_dir(name: str = "") -> str:
    p = os.path.join(home(), "bin", name) if name else os.path.join(home(), "bin")
    os.makedirs(p, exist_ok=True)
    return p


def find_exe(folder: str, stem: str) -> str:
    """Locate e.g. realesrgan-ncnn-vulkan(.exe) anywhere under folder."""
    for root, _, files in os.walk(folder):
        for f in files:
            if f in (stem, stem + ".exe"):
                return os.path.join(root, f)
    raise SystemExit(f"{stem} not found under {folder}; run fetch_tools.py first")


def font(size: int, bold: bool = True):
    """A readable label font on Windows, macOS or Linux (falls back to Pillow's built-in font)."""
    from PIL import ImageFont
    names = ["arialbd.ttf", "Arial Bold.ttf", "DejaVuSans-Bold.ttf"] if bold else ["arial.ttf", "Arial.ttf", "DejaVuSans.ttf"]
    for n in names:
        try:
            return ImageFont.truetype(n, size)
        except OSError:
            continue
    try:
        return ImageFont.load_default(size)
    except TypeError:
        return ImageFont.load_default()
