# Phase 1: analyse the reference

Goal: a written scene plan with measured numbers, before building anything.

1. **Basics:** `ffprobe` size, fps, duration. Find where the edit ends (TikTok reposts add an outro; cut it).
2. **Every frame:** `python scripts/extract_ref.py ref.mp4 work/ref --offset N`
3. **Transitions and effects, every frame:** `python scripts/motion_profile.py ref.mp4 work/motion --offset N`.
   Open `graph.png` and `windows.txt`. For EVERY window: dense pair sheet at step 1, big zoomed pairs on
   its frames, and per-frame measurements (position, scale, rotation, blur amount, opacity, colour).
   Short effects (1 to 4 frames) are easy to miss and are what makes an edit feel "right". Never study a
   window with gaps between frames.
4. **Cuts and flashes:** `python scripts/find_cuts.py ref.mp4 --offset N`. One-frame flashes (negative,
   white, B&W) are listed separately; measure exactly which frames they cover.
5. **Contact sheet** (overview only, gaps are fine here) to see the structure: `ffmpeg -i ref.mp4 -vf fps=2,scale=256:-1,tile=6x9 sheet.jpg`
6. **Scene plan** (`scene-plan.md`): for each scene, the time range, what's on screen, layer order (what
   passes in front of what), text, colours, and what footage it needs from the person (close-up, waist-up,
   hand near face, a clean outline for a cut-out...).
7. **Text:** copy the exact words and spelling. If you have the template's `.aep`, `scripts/aep_text.py`
   lists every text layer and its font. Note which fonts are licensed for redistribution (most "free for
   personal use" fonts are not).
8. **Face track:** `python scripts/face_track.py ref.mp4 work/ref_faces.csv --offset N`. Face centre and
   height per frame give the framing, zooms and pans to copy.
9. **Retiming:** if the template ships the creator's source clip, `scripts/speed_match.py` finds which
   source frame each reference frame shows: slow motion (0.25 to 0.5x is common), freezes, reverse
   playback, speed ramps. Without the source, estimate from motion and confirm with the person.
10. **Motion (graph editor):** pans via phase correlation or face-track slopes; zooms from face height; whips and spins
   usually have heavy motion blur (use `@remotion/motion-blur` `CameraMotionBlur`). Read the curve
   shape from `profile.csv` (flow per frame): where it accelerates and decelerates is your easing.
11. **Colours:** sample pixels (PIL `getpixel`) in the reference at known frames. Write the hex values
    into the code comments, so the next round can check them.
