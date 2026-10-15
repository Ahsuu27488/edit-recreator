# edit-recreator

Recreate a short-form video edit (TikTok, Reels, Shorts, CapCut or After Effects template) frame by frame in
Remotion, with your own photos and clips swapped in. Claude measures the reference (every cut, flash and
transition, the speed graph of each move, slow motion and speed ramps, the subject's framing, text positions
and colours), prepares your footage (smooth RIFE slow motion, clean BiRefNet cut-outs, several enhancement
versions), builds the scenes in Remotion, and checks its render against the reference side by side, frame by
frame, until they match.

## Use it

Ask Claude things like:
- "Recreate `reference.mp4` with the clips in `my-clips/`."
- "Find every transition in this edit and study each one frame by frame."
- "Make a pose sheet from my clips so I can pick a moment per scene."
- "Compare scene 6 with the reference and fix what differs."

More examples, with what Claude does for each: [EXAMPLES.md](EXAMPLES.md).

## What it runs, downloads and sends

- **Runs locally:** Python scripts and Node scripts in this plugin, ffmpeg, Remotion renders, and (if you
  install them) the open-source RIFE and Real-ESRGAN binaries. Nothing runs automatically: there are no hooks
  and no MCP servers; Claude runs a script only when the skill needs it in your session.
- **Downloads (only when you run `scripts/fetch_tools.py`, or a model on first use):** RIFE and Real-ESRGAN
  from their official GitHub releases, BiRefNet-portrait from Hugging Face (onnx-community), GFPGAN from its
  GitHub release, face-detector weights via facexlib, and rembg models via rembg. All are stored in
  `~/.cache/edit-recreator`.
- **Sends:** nothing. No data leaves your machine. The optional "external enhancer" workflow only prepares
  files for an app you choose to use yourself.

## Licence

MIT (see [LICENSE](LICENSE)). Third-party tools keep their own licences. Remotion is source-available: free
for individuals and companies of up to 3 people; larger companies need a Remotion company licence.
