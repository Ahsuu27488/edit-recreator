# Phase 2: choose and prepare the person's media

## Let the person choose (with labelled sheets)
1. `python scripts/analyze_media.py media/ work/analysis` scores every photo and video frame (face size,
   sharpness, frontal, roll). Clips with roll near ±90 are stored sideways: rotate them.
2. `python scripts/pose_sheet.py out.jpg 0.5 300 6 A=clip1.mp4 B=clip2.mp4` makes a labelled sheet
   (codes like A12 = clip1 at 5.5 s). Send it; ask for a code per scene. Note which ranges they say are
   unusable and never use those.
3. Before re-preparing, send a plan sheet (`plan_sheet.py plan.json`): NOW (current render) vs NEW
   (proposed moment) per scene, and wait for "approved".

Footage rules that saved us rounds:
- **Cut-out scenes need clips where the whole head and body are inside the frame** (portrait or medium
  shots). Close-up selfies cut the hair or arms at the frame edge, which looks "cut with scissors".
- Natural full-frame scenes suit landscape selfies; a portrait clip in a 16:9 frame leaves empty sides.
  Either zoom to fill (`cover`) or use a landscape clip. The person usually prefers no blurred sides.
- Pale hands, white fabric or a white veil on a white wall break the weaker cut-out models. Use BiRefNet.

## Enhancement: offer versions, never force one
Phone and WhatsApp footage is soft. Prepare one slot set per **variant** and render each; let the person pick:
- `original`: untouched. Often the most faithful.
- `external`: an app/online enhancer (e.g. a phone "AI quality" app). Many apps give free runs per video
  regardless of length: `external_enhance.py join` puts ALL clips into one video per orientation, you run
  each through the app once, `external_enhance.py split` cuts them back with exact frame counts.
  Check the app's privacy terms first; ask before spending credits.
- `x4`: Real-ESRGAN x4plus (slow, faithful). The fast anime model looks painted on faces; avoid it.
- `x4gfp`: x4 plus GFPGAN. Sharpest, but it CAN CHANGE THE FACE. Show a side-by-side and get approval.

## Slots
`slots.json` (see templates) names each scene's footage: `src`, `start`, `dur`, `rotate`, `cut`, `model`,
`interp`. Then:
```
python scripts/prep_slots.py media/slots.json --project remotion --variant original [--only s06,s07] [--force]
```
It writes `public/slots/<variant>/<slot>/full|cut/*.jpg|webp`, a median face box per slot, and
`src/slots.gen.ts`. Render a variant with `--props='{"variant":"original"}'`.

- **Slow motion (`interp: 4`)**: RIFE makes 3 in-between frames per real frame, after enhancement (so
  only real frames are enhanced). Scene code keeps counting source frames; `slotIndex()` maps them.
  Without interpolation, 0.25x slow motion stutters badly.
- **Cut-outs (`cut: true`)**: `model: "birefnet"` is far better than u2net/isnet on hair, hands and
  white-on-white, but ~20 s/frame on CPU, so it masks only the real frames and RIFE interpolates the masks.
  `solid_mask.py` then fills see-through hair and small holes and drops loose specks.
- Re-check the cut-out on a coloured background for every new shot (hands, hair top, stray objects at the
  frame edge such as a door or a passer-by).
