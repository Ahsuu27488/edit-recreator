# Lessons (each one cost us a round)

**Measuring**
- Seeking ffmpeg to `t + 0.001` lands one frame LATE; seek to `t - 0.001` (frame index f is at f/fps).
  An off-by-one here shifts every measurement you take with it.
- Name reference frames by YOUR timeline's frame numbers (offset applied once), so sheets line up.
- A sheet that shows "missing" frames may just be a filename-padding mismatch (`element-5` vs `element-005`).

**Faces and enhancement**
- GFPGAN on blurry phone footage changed a real person's features. The person was (rightly) upset.
  Side-by-side test first; keep an "original" version; never batch-process before approval.
- The fast Real-ESRGAN anime model looks painted on faces. x4plus is faithful but slow; only at `-s 4`.
- App enhancers often keep the input resolution: they retouch, they don't upscale.

**Cut-outs**
- u2net keeps background furniture; isnet sometimes cuts hands; both lose white fabric on a white wall.
  BiRefNet-portrait fixed all of these.
- Feathering the TOP edge of a cut-out fades the hair. Feather only edges where the footage frame itself
  cuts through the subject, never the edge above the head.
- Fill small holes in the mask (see-through hair), but not big ones (the gap between an arm and the body).

**Framing**
- Close-up selfies placed at the reference's face size become huge and cover the text.
- A portrait clip in a 16:9 frame: the blurred-copy fill shows a ghost of the face. People prefer `cover`.
- A clip that continues across a transition must continue its own frames; switching to another clip under
  an overlay reads as a jump.

**Text**
- Hard `clip-path` on glow text cuts the glow at the letter box; people notice. Use a feathered mask.
- People are strict about cut-off letters. Audit after every text move.

**Process**
- Show labelled sheets and plan images; ask the person to choose by code. Rounds got shorter immediately.
- Slow downloads: GitHub release assets can crawl; Hugging Face mirrors plus parallel byte ranges help a lot.
- Disk fills up with RIFE frames and intermediate PNGs; clear `work/prep` once slots are written.
- Long renders: run in the background, poll a log, and report numbers. For overnight runs, chain prep and
  render in one script that logs failures instead of stopping silently.
