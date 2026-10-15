"""List the fonts and text-layer contents stored in an After Effects .aep file.

Usage: python aep_text.py <file.aep> [out.txt]
AE keeps each text document in Adobe's text-engine format: the font list as /CoolTypeFont entries,
and the text itself as "/1 [ << /0 << /0 (<UTF-16BE text>\r)". Font sizes follow as "/1 <size>" in the style run.
"""
import re, sys

BS = bytes([92])


def u16(b):
    b = b.replace(BS + b"(", b"(").replace(BS + b")", b")").replace(BS + BS, BS)
    if b.startswith(b"\xfe\xff"):
        b = b[2:]
    return b.decode("utf-16-be", "replace")


d = open(sys.argv[1], "rb").read()
out = open(sys.argv[2] if len(sys.argv) > 2 else "aep_text.txt", "w", encoding="utf-8")

fonts = [(m.start(), u16(m.group(1))) for m in re.finditer(rb"/CoolTypeFont /0 << /0 \((.*?)\) ", d, re.S)]
out.write("== fonts (position, name) ==\n")
for p, f in fonts:
    out.write(f"{p:>10}  {f}\n")

out.write("\n== text documents (position, text, nearest font before it, font sizes in its style runs) ==\n")
for m in re.finditer(rb"/1 \[ << /0 << /0 \((\xfe\xff.*?)\) /5", d, re.S):
    text = u16(m.group(1)).replace("\r", " / ").strip(" /")
    if not text:
        continue
    before = [f for p, f in fonts if p < m.start()]
    tail = d[m.end(): m.end() + 1500]
    sizes = sorted({round(float(x), 1) for x in re.findall(rb"/1 ([0-9]+\.[0-9]+) /2", tail)})
    out.write(f"{m.start():>10}  {text!r}  font~{before[-1] if before else '?'}  sizes={sizes[:6]}\n")
out.close()
print("written")
