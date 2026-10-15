"""Before/after plan sheet: for each scene, the current render frame next to the proposed source moment.
Show it to the person BEFORE re-preparing anything, so they approve exact moments, not descriptions.

Usage: python plan_sheet.py <plan.json> <out.jpg>
plan.json: {"render": "out/v1.mp4", "rows": [
    {"label": "6  Title scene", "now": 13.3, "clip": "media/clipD.mp4", "at": 4.6, "note": "D11->D14, whole head in frame"}, ...]}
"""
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
from _paths import font as _font

import json, os, subprocess, sys, tempfile
from PIL import Image, ImageDraw, ImageFont

plan, out = json.load(open(sys.argv[1], encoding="utf-8")), sys.argv[2]
font, small = _font(26), _font(22, bold=False)
tmp, TH, LW = tempfile.mkdtemp(), 300, 420
rows = []
for i, r in enumerate(plan["rows"]):
    a, b = os.path.join(tmp, f"a{i}.png"), os.path.join(tmp, f"b{i}.png")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", str(r["now"]), "-i", plan["render"], "-frames:v", "1", a], check=True)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", str(r["at"]), "-i", r["clip"], "-frames:v", "1", b], check=True)
    ia, ib = Image.open(a).convert("RGB"), Image.open(b).convert("RGB")
    rows.append((r["label"], r.get("note", ""), ia.resize((int(ia.width * TH / ia.height), TH)), ib.resize((int(ib.width * TH / ib.height), TH))))
wa, wb = max(r[2].width for r in rows), max(r[3].width for r in rows)
sheet = Image.new("RGB", (LW + wa + 60 + wb + 20, 50 + len(rows) * (TH + 16)), (22, 22, 22))
d = ImageDraw.Draw(sheet)
xa, xb = LW, LW + wa + 60
d.text((xa, 10), "NOW", fill="#ff8080", font=font)
d.text((xb, 10), "NEW", fill="#80ff80", font=font)
for i, (label, note, ia, ib) in enumerate(rows):
    y = 50 + i * (TH + 16)
    d.text((14, y + 20), label, fill="yellow", font=font)
    line, ly = "", y + 70
    for w in note.split():
        if d.textlength(line + " " + w, font=small) > LW - 30:
            d.text((14, ly), line.strip(), fill="white", font=small); ly += 30; line = ""
        line += " " + w
    d.text((14, ly), line.strip(), fill="white", font=small)
    sheet.paste(ia, (xa, y)); d.text((xb - 45, y + TH // 2 - 20), "->", fill="white", font=font); sheet.paste(ib, (xb, y))
sheet.save(out, quality=88)
print(out, sheet.size)
