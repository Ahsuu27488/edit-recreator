# Phase 3: build the scenes and compare

## Structure
- One component per scene, a `<Sequence>` per scene in the root composition at the measured cut frames.
  Scenes that overlap at a transition (a wipe or iris over the next scene) can render the neighbour inside
  themselves, or the root can overlap the sequences. Fix the timeline rather than faking a cut.
- Keyframes in **global frame numbers** (`const g = useCurrentFrame() + START`), copied from measurements,
  through `curve(g, [[frame, value], ...])`. Leave the measured numbers in comments.
- Layer order exactly as measured (e.g. wall → words → stars → person: the words pass BEHIND her).
- Fast whips, spins and zooms: wrap in `CameraMotionBlur` (`@remotion/motion-blur`). Sub-frame renders give
  fractional frames; the slot loaders floor them.
- Text: glow never uses a hard `clip-path` (it cuts the glow off at the letter box). Write-ons use a
  feathered `mask-image` on a box padded by the glow radius. Give every text element
  `data-text-layer="<name>"` and add it to `textChecks` in `edit.config.json`.

## Framing the new footage
`<Framed slot="s01" face={{ x, y, h }} />` puts the slot's median face at the reference's face position and
size (from `face_track.py`).
- Natural full-frame scenes: add `cover` so no edge ever shows.
- Cut-out scenes: `layer="cut"`; the bottom edge is pinned by default; add `pin={{ top: true }}` when the
  clip cuts the hair at its top edge. Never let the subject cover the lyric words: if the new clip is
  tighter than the reference's, scale the face target down (e.g. `h * 0.6`).
- Full-length shots have small faces: framing them at the reference's face size blows them up and blurs
  them. Frame waist-up instead (face around 0.55 to 0.7 of the reference size).

## Compare (every round)
```
npx remotion render <Comp> ../work/ours --sequence --frames=263-312 --image-format=jpeg --scale=0.25 --props='{"variant":"original"}'
python scripts/pair_sheet.py work/ref work/ours 263 312 work/s06/dense.jpg 10 192 1
python scripts/pair_hi.py ref.mp4 work/ours work/s06/key.jpg 275 287 299 --offset N
```
Read the sheets yourself, row by row: position (use the 10% ruler), size, colour (sample pixels),
layer order, timing (which frame something appears), motion. Write down each difference, fix, repeat.

Between rounds, `python scripts/sync_check.py old.mp4 new.mp4` proves the audio and cuts did not move
(people sometimes feel a sync change that is really a content change; measure before answering).

## Parallel work
Scenes are independent files, so several sub-agents can each own a scene (only its file and new
`lib/sNN*.tsx` files), render only their frame range at low scale, and report measurements and sheet paths.
The coordinator reviews their sheets, fixes the shared timeline, and commits.
