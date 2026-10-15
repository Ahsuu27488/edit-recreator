# Phase 0: setup and project memory

## Tools
- **ffmpeg / ffprobe**, **Node 18+**, **Python 3.10+** (use a venv inside the project).
- Python packages: `pip install -r ${CLAUDE_SKILL_DIR}/requirements.txt` (core). Face tracking and
  GFPGAN need the heavier `requirements-face.txt` (torch, facexlib, gfpgan).
- Open-source binaries and weights, once: `python ${CLAUDE_SKILL_DIR}/scripts/fetch_tools.py`
  - RIFE v4.6 (slow-motion frames), Real-ESRGAN x4plus (upscaling), BiRefNet-portrait (cut-outs),
    GFPGAN v1.4 (optional face restore). They go to `~/.cache/edit-recreator` (`EDIT_RECREATOR_HOME`).
  - Big files download in 8 parallel ranges; on slow links that is several times faster than one stream.
  - The ncnn binaries use the GPU through Vulkan (`--gpu 0`; `-1` = CPU). Laptops with two GPUs: try 1.
- New Remotion project: `npx create-video@latest`, then copy `remotion-kit/*.ts(x)` into `src/lib/`.
  Remotion is source-available: free for individuals and companies up to 3 people; bigger companies
  need a licence (remotion.dev/license).

## Project layout (suggested)
```
my-edit/
  reference/ref.mp4            the edit to copy (never modified, never committed)
  media/                       the person's footage (never committed) + slots.json
  remotion/                    the Remotion project (+ edit.config.json)
  work/                        all generated frames, sheets, logs (never committed)
  HANDOFF.md TODO.md DECISIONS.md
```

## Project memory (sessions end; the work shouldn't restart)
Keep three short files and update them whenever work finishes:
- `HANDOFF.md`: status per scene, the method, gotchas, what's running.
- `TODO.md`: ordered tasks; "done" only after a reference comparison.
- `DECISIONS.md`: what the person decided and why. Don't reverse these without asking.

Optional: `templates/docs_check.sh` as a Claude Code **Stop hook** blocks the end of a reply once when
source files changed after HANDOFF.md, so the docs never drift (see the comment at its top).

Commit milestones to a **local** git repo with a `.gitignore` that excludes media, renders, `work/`,
models and the reference (template in `templates/gitignore.txt`).

## Timeline alignment
Measure once whether the reference's audio starts later than your song file (cross-correlate the two
tracks; `sync_check.py` prints the lag). Express it as a frame `offset` and pass it to every script and
to `edit.config.json`. Then "frame f" means the same moment everywhere.
