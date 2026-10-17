# Phase 4: sound (music sync, voiceover, effects, loudness)

Recreated edits usually ride the reference's song. Promos, ads and explainer reels add a voiceover, sound
effects and a trending sound on top. Everything here is measured, the same way as the picture.
Setup: `pip install -r requirements-audio.txt` (librosa, faster-whisper).

## Music: put the drop where it hits hardest
```
python scripts/song_map.py song.mp3 --land 28.9            # land the biggest drop on the video's 28.9 s
python scripts/song_map.py song.mp3 --hook 40 --land 28.9 --drop 173.2   # pick a specific drop
```
- It prints the tempo, an energy bar per 2 s, the biggest drops, and **the song start** (drop − land, snapped
  to a beat). Choose the land moment from the picture: the reveal, the before/after, the title.
- `--hook S` lists where an 8 s phrase repeats. The last return of the hook, right after a quiet break, is
  usually the strongest drop and the part people recognise.
- `beats.json` holds the beat grid in video time. Put cuts, whips and zoom kicks on beats; for a kick that
  follows the music, use the phase `((t - drop) / beat) % 1` on the real output clock.
- **Licensing:** a commercial song can't be baked into a file you post as an ad. Render the post version with
  VO + SFX only, render a private preview with the song mixed in to check the sync, and add the song in the
  app (Instagram/TikTok) with its trim start set to the printed time. If the person is on a business account
  or will boost the post, use a royalty-free track instead.
- If the person picks the song by name, check which section the trend actually uses before assuming.

## Voiceover
- **Pick a voice the platform's creators actually use.** Generic "narrator" voices sound like ads. In
  ElevenLabs, filter the voice library by language and sort by usage ("most used, 1 year"), then read the
  descriptions for reels/shorts use. Make one take each from 2-3 candidates and let the person choose by ear.
- **Timing comes from the take you got, not the script.** Get word timings:
  `python scripts/vo_words.py vo.mp3 vo.words.json --lang en`
  - Long or non-English takes: whisper may stop early or garble words. Transcribe slices with
    `--from/--to` and join them, or take **phrase starts from silences**:
    `ffmpeg -i vo.mp3 -af silencedetect=n=-32dB:d=0.12 -f null -` (speech runs between the silences) and
    spread each phrase's words by length.
  - Captions in a language the viewer reads in Latin letters (Hinglish, Roman Urdu): keep the timings,
    replace each word with its romanised form, 1:1.
- **Slow, pause-heavy reads:** `python scripts/tighten_pauses.py vo.mp3 vo_tight.wav 0.28` caps every pause.
  Re-run the word timings on the tightened file.
- **Cut scenes on words.** Scene boundaries and key animations sit on the word starts ("No…" → stamp slams in).

## A second language or voice without rebuilding: TimeWarp
Build the whole video once on the master VO. For another take, list matching moments as anchors
`[[master s, new s], ...]` (every scene start and every word a graphic reacts to) and wrap the scenes:
```tsx
<TimeWarp anchors={HI}><Scenes /></TimeWarp>          // remotion-kit/TimeWarp.tsx
<Captions words={wordsHi} />                          // real clock, outside the warp
<Audio src={staticFile('vo_hi.wav')} />
{SFX.map(([n, t]) => <Sequence from={Math.round(warpTime(HI, t, 0) * fps)}>…)}
```
Each segment speeds up or slows down a little; nothing is re-timed by hand. Set the new composition's
duration from the last anchor, and recompute the song start for the new drop moment.

## Sound effects
`python scripts/make_sfx.py public/sfx` synthesises whoosh, hit, stamp, click, riser, ding and glitch (no
downloads, no licences). Typical placement: whoosh on every scene whip, stamp + hit on text slams, clicks
every 2 characters while text types, a riser ending just before the drop, a hit on the drop, ding on a
"match/done". Volumes 0.2-0.6 each.

## Loudness (people notice this first)
- AI voices often come out quiet (around −26 LUFS). Level the VO before use:
  `ffmpeg -i vo.mp3 -af "highpass=f=80,acompressor=threshold=-24dB:ratio=3:attack=5:release=120:makeup=4,loudnorm=I=-14:TP=-1.5:LRA=7" -ar 48000 vo.wav`
- Post version (VO + SFX): master the whole mix to **−14 LUFS, true peak −1 dB** (the Reels/Shorts norm):
  `loudnorm=I=-14:TP=-1:LRA=9`.
- With-music version: keep the music at the level the person approves (don't duck it unless they ask), and
  only limit the peaks (`alimiter=limit=0.89`). Check with `ffmpeg -i out.mp4 -af ebur128=peak=true -f null -`.
- Audio-only changes don't need a full re-render: render `--codec=wav`, process it, and mux it onto the
  existing video with `-map 0:v -map 1:a -c:v copy`.

## Checks before sending
- Watch the drop: does it land on the planned frame in the preview?
- Every caption chunk appears with its words, and none sits in the app's UI zones.
- Loudness numbers as above, no clipping (peak below −0.5 dBFS).
- Files under ~30 MB if the person reviews on a phone (re-encode a copy with `-crf 23`).
