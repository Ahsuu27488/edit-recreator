---
name: recreate-edit
description: "Recreate a short-form video edit (TikTok / Reels / Shorts / CapCut / After Effects template) frame-accurately in Remotion, with the person's own photos and clips swapped in. Use when someone gives a reference edit and wants 'the same edit but with my footage': matching cuts, timing, slow motion, text, effects and framing, checked frame by frame against the reference."
license: MIT
metadata:
  version: "0.1.1"
  requires: "ffmpeg, Node 18+, Python 3.10+, Remotion 4"
---

# Recreate an edit, frame by frame

You rebuild a reference edit in **Remotion** (React video, rendered by code) and swap in the user's media.
The bar is "looks like the same edit", so **measure the reference, never eyeball it**, and **check every
change against the reference in side-by-side frames before calling it done**.

All helper scripts live in `${CLAUDE_SKILL_DIR}/scripts/`, the Remotion building blocks in
`${CLAUDE_SKILL_DIR}/remotion-kit/`. Read the reference docs when you reach that phase:

| Phase | Read |
|---|---|
| 0. Setup and project memory | [reference/setup.md](reference/setup.md) |
| 1. Analyse the reference | [reference/analyse.md](reference/analyse.md) |
| 2. Choose and prepare the user's media | [reference/media.md](reference/media.md) |
| 3. Build scenes and compare | [reference/build.md](reference/build.md) |
| Pitfalls we hit (read once, early) | [reference/lessons.md](reference/lessons.md) |

## The loop (every scene, every round)

1. **Dense reference frames:** `extract_ref.py` writes EVERY reference frame named by your frame numbers.
   **No gaps.** Edits hide effects that last 1 to 4 frames (flashes, glitches, whip blur, shake, zoom
   punches). Sampling at 2 fps or every 3rd frame skips them and gets the easing wrong. Overview sheets may
   skip frames; anything you measure or build from must be studied at EVERY frame.
2. **Find the transitions:** `motion_profile.py` scores every frame and writes `windows.txt` (the ranges to
   study one frame at a time) and `graph.png` (the speed graph, like an After Effects graph editor). Copy
   each move's curve shape (ease-in, ease-out, overshoot, hold) into `curve()` keyframes per frame.
3. **Measure:** cuts (`find_cuts.py`), face track (`face_track.py`), retiming (`speed_match.py`), text
   positions (ruled sheets from `pair_hi.py`), colours (sample pixels; don't guess hex values).
4. **Build** each layer on measured keyframes with `curve()` (monotone cubic, like After Effects auto-bezier).
5. **Render the range** you changed: `npx remotion render <Comp> work/ours --sequence --frames=A-B --scale=0.25`.
6. **Compare:** `pair_sheet.py` with step 1 (every frame) and `pair_hi.py` (big, ruled, key frames). Look at them.
7. **Audit text:** `remotion-kit/scripts/text-audit.mjs`. No letter may be cut by the frame edge.
8. Fix, re-render, re-compare. Only then show the person.

## Working with the person

- **Show, don't describe.** Send images: pose sheets (`pose_sheet.py`) so they pick moments by code
  (e.g. "D12"), plan sheets (`plan_sheet.py`) of NOW vs NEW before re-preparing anything, and the
  reference-vs-ours pairs after. People judge pictures far better than paragraphs.
- **They choose the footage**; you propose with reasons. Never silently replace their pick.
- **Ask before** spending app credits, downloading big models, uploading someone's photos to a cloud
  service, or making a change that is hard to undo. Use a structured question with a recommended option.
- **Never let an enhancer change a real person's face.** Face-restoration models (GFPGAN, CodeFormer)
  can redraw eyes, nose and brows on blurry phone footage. Always show original / upscaled / restored
  side by side on the worst clip first. Offer several versions (see media.md: variants).
- **Keep it private.** The person's media, the reference edit, the song and any template assets stay out
  of git and out of anything published.
- Long jobs (cut-outs, upscaling, renders) run in the background; give short progress updates with
  numbers ("2 of 5 scenes done, ~30 min left"), and set up an overnight script when the person sleeps.

## Remotion building blocks (copy `remotion-kit/` into `src/lib/`)

- `Framed.tsx`: place a prepared clip so the subject's face lands on a screen target `{x, y, h}`
  (from the reference's face track). Handles full-frame `cover`, edge `pin`ning, feathered edges and a
  blurred fill. Works for the full clip and the background-removed `cut` layer alike.
- `SlotFrames.tsx` + `slotIndex.ts`: play a prepared image sequence at any speed (slow motion uses the
  RIFE in-between frames; scene code counts source frames).
- `curve.ts`: measured keyframes → smooth eased values. `fx.tsx`: clamp, glow, shake, defocus helpers.
- `Extruded.tsx` / `extrude.ts`: real CSS-3D extruded title text.
- `TextAudit.tsx` + `scripts/text-audit.mjs`, `scripts/compare.mjs`: checks driven by `edit.config.json`.

## Definition of done

Every scene has a dense pair sheet that matches the reference (positions, sizes, colours, timing, motion),
the text audit passes, `sync_check.py` shows the audio and cuts unchanged between rounds, the person has
approved the footage choices, and nothing private is committed.
