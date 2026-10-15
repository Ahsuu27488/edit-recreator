import { AbsoluteFill, Img, staticFile, useCurrentFrame } from 'remotion';
import { slotIndex } from './slotIndex';
import { SLOT_ROOT, SLOTS, type SlotName } from '../slots.gen';

type Props = {
  readonly slot: SlotName;
  /** "full" = the whole enhanced frame, "cut" = background removed (transparent). */
  readonly layer?: 'full' | 'cut';
  /** Source frame to start from. */
  readonly offset?: number;
  readonly playbackRate?: number;
  /** Hold a single frame instead of playing. */
  readonly freeze?: number;
  /** CSS object-position, e.g. "50% 30%" to keep the face in frame when cropping. */
  readonly focus?: string;
  readonly fit?: 'cover' | 'contain';
  readonly style?: React.CSSProperties;
};

/** Plays a prepared slot (an image sequence made by tools/scripts/prep_slots.py) in sync with the timeline. */
export const SlotFrames: React.FC<Props> = ({
  slot,
  layer = 'full',
  offset = 0,
  playbackRate = 1,
  freeze,
  focus = '50% 50%',
  fit = 'cover',
  style,
}) => {
  const frame = useCurrentFrame();
  const info = SLOTS[slot];
  // Positions are in source frames (30 fps). Slots made with RIFE slow motion store `interp` frames per source
  // frame, so fractional positions (slow motion, motion-blur sub-frames) land on real in-between frames.
  const index = slotIndex(info, freeze ?? frame * playbackRate + offset);
  const ext = layer === 'cut' ? 'webp' : 'jpg';
  return (
    <AbsoluteFill style={style}>
      <Img
        src={staticFile(`${SLOT_ROOT}/${slot}/${layer}/${String(index).padStart(4, '0')}.${ext}`)}
        style={{ width: '100%', height: '100%', objectFit: fit, objectPosition: focus }}
      />
    </AbsoluteFill>
  );
};
