"""Make a cut-out's alpha solid inside her outline: firm up half-transparent pixels (dark hair against a bright wall
comes out see-through) and fill enclosed holes, keeping only a soft outer edge."""
import numpy as np
from PIL import Image, ImageFilter
from scipy import ndimage


def solidify(rgba: Image.Image) -> Image.Image:
    a = np.asarray(rgba.getchannel("A"), dtype=np.float32) / 255.0
    core = a > 0.12                                   # anything the model thought might be her
    core = ndimage.binary_closing(core, iterations=2)  # bridge thin gaps in hair strands
    # Fill only SMALL enclosed holes (see-through hair, fingers); big ones are real gaps (arm/body, legs).
    holes = ndimage.binary_fill_holes(core) & ~core
    hl, hn = ndimage.label(holes)
    if hn:
        hs = ndimage.sum(holes, hl, range(1, hn + 1))
        small = np.nonzero(hs < core.size * 0.002)[0] + 1
        core = core | np.isin(hl, small)
    core = ndimage.binary_opening(core, iterations=1)  # drop single-pixel specks
    # keep the largest connected blobs only (her), so loose background bits vanish
    lab, n = ndimage.label(core)
    if n > 1:
        sizes = ndimage.sum(core, lab, range(1, n + 1))
        keep = sizes >= max(sizes.max() * 0.08, 50)
        core = np.isin(lab, np.nonzero(keep)[0] + 1)
    soft = Image.fromarray((core * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(1.2))
    out = rgba.copy()
    out.putalpha(soft)
    return out


if __name__ == "__main__":
    import sys
    solidify(Image.open(sys.argv[1]).convert("RGBA")).save(sys.argv[2])
