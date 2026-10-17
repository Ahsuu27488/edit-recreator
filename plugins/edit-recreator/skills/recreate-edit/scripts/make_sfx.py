"""Synthesise motion-graphics sound effects from noise and sine waves (no downloads, no licences):
whoosh (transitions), hit (sub-bass drop), stamp (text slam), click (typing), riser (build into a drop),
ding (a "match" / success), glitch (stutter).

Usage: python make_sfx.py <out_dir>    -> <out_dir>/<name>.wav, 44.1 kHz stereo, peak-normalised
Play each with its own volume in Remotion (<Audio src=... volume={0.3..0.6} />) at the frame it belongs to."""
import sys, os, wave
import numpy as np
from scipy.signal import lfilter

SR = 44100
out = sys.argv[1]
os.makedirs(out, exist_ok=True)
rng = np.random.default_rng(7)


def save(name, x):
    x = x / (np.abs(x).max() + 1e-9) * 0.9
    st = np.stack([x, x], 1)
    with wave.open(os.path.join(out, name + '.wav'), 'wb') as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes((st * 32767).astype(np.int16).tobytes())


def t(d):
    return np.arange(int(SR * d)) / SR


def lp(x, a):
    """One-pole low-pass with a fixed coefficient a in (0, 1)."""
    return lfilter([a], [1, a - 1], x)


def sweep_lp(x, a, blocks=64):
    """Low-pass whose coefficient follows the array a, processed in short blocks."""
    y = np.zeros_like(x)
    zi = np.zeros(1)
    for idx in np.array_split(np.arange(len(x)), blocks):
        c = float(np.clip(a[idx].mean(), 1e-4, 0.999))
        y[idx], zi = lfilter([c], [1, c - 1], x[idx], zi=zi)
    return y


# whoosh: noise through a sweeping band, swelling then fading
d = 0.45; tt = t(d); n = rng.standard_normal(len(tt))
cut = 0.02 + 0.5 * np.sin(np.pi * tt / d) ** 2
save('whoosh', (sweep_lp(n, cut) - sweep_lp(n, cut * 0.15)) * np.sin(np.pi * tt / d) ** 1.5)
# hit: sub drop 70 -> 40 Hz plus a short transient
d = 0.7; tt = t(d)
sub = np.sin(2 * np.pi * np.cumsum(40 + 30 * np.exp(-tt * 12)) / SR) * np.exp(-tt * 5)
click = rng.standard_normal(len(tt)) * np.exp(-tt * 90) * 0.5
save('hit', sub + lp(click, 0.3))
# stamp: mid thump + crack
d = 0.45; tt = t(d)
th = np.sin(2 * np.pi * np.cumsum(120 + 80 * np.exp(-tt * 30)) / SR) * np.exp(-tt * 14)
save('stamp', th + 0.6 * rng.standard_normal(len(tt)) * np.exp(-tt * 60))
# key click
d = 0.035; tt = t(d)
save('click', lp(rng.standard_normal(len(tt)), 0.6) * np.exp(-tt * 180))
# riser: noise + rising tone, swelling
d = 2.6; tt = t(d)
tone = np.sin(2 * np.pi * np.cumsum(200 + 900 * (tt / d) ** 2) / SR)
nz = sweep_lp(rng.standard_normal(len(tt)), 0.05 + 0.6 * (tt / d) ** 2)
save('riser', (0.5 * tone + nz) * (tt / d) ** 2)
# ding: two bright partials
d = 0.9; tt = t(d)
save('ding', (np.sin(2 * np.pi * 1318.5 * tt) + 0.6 * np.sin(2 * np.pi * 1975.5 * tt)) * np.exp(-tt * 5))
# glitch: stuttered noise bursts
d = 0.3; tt = t(d)
g = rng.standard_normal(len(tt)) * (np.sin(2 * np.pi * 28 * tt) > 0)
save('glitch', lp(g, 0.4) * np.exp(-tt * 6))
print('ok')
