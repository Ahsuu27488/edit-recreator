# Examples of use

Each example shows what you say to Claude and what the skill makes it do. File names are placeholders.

## 1. The whole job: "same edit, my clips"

> "Here's an edit I love: `reference/ref.mp4`. My clips are in `media/`. Recreate it with my clips, 1920x1080."

Claude will:
1. Ask a few setup questions (output size, which parts to keep, whether to cut a TikTok outro).
2. Extract every reference frame, run the motion profile and list the scenes with exact cut frames.
3. Write `scene-plan.md`: per scene, what's on screen, the layer order, the text, and the kind of shot it needs.
4. Send you a **pose sheet** of your clips with codes (A1, A2… B1…) and propose a code per scene.
5. Prepare the footage (slow-motion frames, cut-outs), build each scene, and send reference-vs-ours sheets.
6. Render, compare, fix, and repeat per scene; then send the full render.

## 2. Find every transition (the bit people miss)

> "Study the transitions in `ref.mp4`. Don't skip frames."

```
python scripts/motion_profile.py ref.mp4 work/motion
```
You get `windows.txt` (for example `82-91 (2.80-3.10s) cut -> study EVERY frame`) and `graph.png`, the speed
graph of the whole edit. Claude then makes a dense sheet for each window and measures position, scale, blur and
opacity at every frame, so 1-to-4-frame flashes, glitches and whip blurs are copied, not missed.

## 3. Pick footage by picture, not by description

> "Show me my clips so I can choose what goes where."

```
python scripts/pose_sheet.py poses.jpg 0.5 300 6 A=media/selfie.mp4 B=media/full_length.mp4
```
You answer with codes: "HATH scene = B11 to B14, title scene = A9". Before re-preparing anything, Claude sends
a plan sheet (NOW vs NEW per scene) and waits for "approved".

## 4. Smooth slow motion

> "The reference plays this shot at quarter speed. Mine stutters."

In `slots.json` set `"interp": 4` for that slot and re-run prep. RIFE adds three in-between frames per real
frame; the scene keeps its timing (`playbackRate={0.25}`) and plays smoothly.

## 5. Clean cut-outs, even white on white

> "Her hands and the white scarf disappear in the cut-out."

Set `"model": "birefnet"` for that slot. BiRefNet keeps hair, raised hands and white fabric against a white wall,
where u2net and isnet fail. It masks only the real frames and lets RIFE fill the in-between masks, so it stays
affordable on a laptop CPU.

## 6. Try enhancement versions side by side

> "My clips are blurry WhatsApp videos. Make them sharper, but don't change her face."

Claude prepares `original`, `x4` (Real-ESRGAN x4plus) and, only with your approval, `x4gfp` (adds GFPGAN face
restoration), shows the same face from each side by side, and renders the version you pick:
```
npx remotion render MyEdit out/v1.mp4 --props='{"variant":"x4"}'
```
Using a phone app enhancer instead? `external_enhance.py join` puts all clips into one video per orientation so
one free run covers everything, and `split` cuts them back with exact frame counts.

## 7. Check a scene against the reference

> "Compare scene 6 (frames 263-312) with the reference."

```
npx remotion render MyEdit work/ours --sequence --frames=263-312 --scale=0.25
python scripts/pair_sheet.py work/ref work/ours 263 312 work/s06/dense.jpg 10 192 1
python scripts/pair_hi.py ref.mp4 work/ours work/s06/key.jpg 275 287 299
```
Claude reads both sheets row by row and lists every difference (position on the 10% ruler, size, sampled
colour, timing, layer order) before fixing.

## 8. "Is it out of sync?"

> "The new version feels a bit out of sync compared to the last one."

```
python scripts/sync_check.py out/round3.mp4 out/round4.mp4
```
It compares the audio sample by sample, the cut positions, and the motion pattern at -3 to +3 frames of shift,
so Claude can tell you with numbers whether anything moved, and if not, what changed in the content instead.

## 9. No cut-off text

> "Make sure no letters are cut off by the frame."

Give each text element `data-text-layer="<name>"`, list them in `edit.config.json`, and run
`node <kit>/scripts/text-audit.mjs`. It prints each layer's margin to every frame edge, for the letters and the
glow separately.

## 10. Make an ad or promo reel, synced to a trending sound, in two languages

> "Make a 40-second reel ad for my app, with a voiceover in English and in Hinglish, and time it to Memory Reboot."

Claude will:
1. Research what hooks and pacing work for the niche, then write a beat-by-beat storyboard and both scripts.
2. Generate the voiceovers (for example with ElevenLabs), pick voices creators in that language actually use,
   and level them (`-14 LUFS`). Pause-heavy takes are tightened with `tighten_pauses.py`.
3. Get word timings (`vo_words.py`) and cut every scene on a word.
4. Map the song (`song_map.py song.mp3 --land 28.9`) so its drop hits the reveal, and put cuts on beats.
5. Build the English version, then the second language with `TimeWarp` (no scene rebuilt) and romanised captions.
6. Render a post version (voice + synthesised SFX, no song) and a private preview with the song, and tell you
   the exact trim start to set when you add the song in Instagram.

The launch reel in the README was made exactly this way.

