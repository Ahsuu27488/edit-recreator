import { AbsoluteFill, Img, staticFile, useCurrentFrame } from 'remotion';
import { slotIndex } from './slotIndex';
import { SLOT_ROOT, SLOTS, type SlotName } from '../slots.gen';

/** Which footage edges must not show inside the screen (they would cut through the subject's hair or body). */
export type Pin = { top?: boolean; bottom?: boolean };

/** Where the subject's face should be on screen (output px): centre x/y and face height.
 *  Measured per frame from the reference with scripts/face_track.py. */
export type FaceTarget = { x: number; y: number; h: number };

const W = 1920;
const H = 1080;

/** Placement of a slot so its (median) face lands on `face`. With `cover`, the placement is nudged so the
 *  full frame still covers the whole screen (no empty edges) — use the same placement for full + cut layers. */
export const placeSlot = (slot: SlotName, face: FaceTarget, cover: boolean, pin: Pin = {}) => {
  const info = SLOTS[slot];
  let scale = face.h / (info.face.h * info.height);
  if (cover) scale = Math.max(scale, W / info.width, H / info.height);
  // The body runs off the bottom of the footage: grow (about the face) until that edge is below the screen.
  if (pin.bottom) scale = Math.max(scale, (H - face.y) / ((1 - info.face.cy) * info.height));
  // Both edges pinned: the footage must span the full screen height.
  if (pin.top && pin.bottom) scale = Math.max(scale, H / info.height);
  const w = info.width * scale;
  const h = info.height * scale;
  let left = face.x - info.face.cx * w;
  let top = face.y - info.face.cy * h;
  if (cover) {
    left = Math.min(0, Math.max(W - w, left));
    top = Math.min(0, Math.max(H - h, top));
  }
  // Selfies cut the hair at the footage's top edge: lift the footage so that edge sits on the screen's top edge.
  if (pin.top && top > 0) top = 0;
  if (pin.top && pin.bottom && top + h < H) top = H - h;
  return { left, top, width: w, height: h };
};

/** For a clip that pans from face x `xStart` to `xEnd`: the smallest face height (>= hWanted) and the x shift
 *  that let the whole pan happen inside the footage without revealing an edge. The shift keeps the motion
 *  identical to the reference; only the framing is nudged when the footage has no spare room. */
export const panFit = (slot: SlotName, xStart: number, xEnd: number, hWanted: number) => {
  const info = SLOTS[slot];
  const need = Math.abs(xStart - xEnd);
  const sMin = (W + need) / info.width;
  const s = Math.max(sMin, hWanted / (info.face.h * info.height));
  const w = info.width * s;
  const maxX = info.face.cx * w;
  const minX = W - (1 - info.face.cx) * w;
  const hi = Math.max(xStart, xEnd);
  const lo = Math.min(xStart, xEnd);
  const shift = hi > maxX ? maxX - hi : lo < minX ? minX - lo : 0;
  return { h: info.face.h * info.height * s, shift };
};

type Props = {
  readonly slot: SlotName;
  readonly face: FaceTarget;
  readonly layer?: 'full' | 'cut';
  /** Strict cover: enlarge until the footage alone fills the screen (zooms close-up selfies in a lot).
   *  Off by default: the face is placed at the reference size, and for the full layer any screen area the footage
   *  doesn't reach is filled with a soft blurred copy of the same frame. */
  readonly cover?: boolean;
  /** Keep these footage edges off-screen. Cut layers pin the bottom by default (the body continues below). */
  readonly pin?: Pin;
  readonly offset?: number;
  readonly playbackRate?: number;
  readonly freeze?: number;
  readonly style?: React.CSSProperties;
};

/** Feathered edges for the sharp layer: only edges that sit inside the screen get faded (into the blurred fill). */
const featherMask = (box: { left: number; top: number; width: number; height: number }, top = true) => {
  const f = (inside: boolean, size: number) => (inside ? Math.round(size * 0.12) : 0);
  const l = f(box.left > 1, box.width);
  const r = f(box.left + box.width < W - 1, box.width);
  // A cut-out's top edge is above the head (the hair would fade), so cut layers never feather it.
  const t = top ? f(box.top > 1, box.height) : 0;
  const b = f(box.top + box.height < H - 1, box.height);
  const x = `linear-gradient(to right, transparent 0px, #000 ${l}px, #000 calc(100% - ${r}px), transparent 100%)`;
  const y = `linear-gradient(to bottom, transparent 0px, #000 ${t}px, #000 calc(100% - ${b}px), transparent 100%)`;
  return { WebkitMaskImage: `${x}, ${y}`, maskImage: `${x}, ${y}`, WebkitMaskComposite: 'source-in', maskComposite: 'intersect' } as React.CSSProperties;
};

/** A prepared slot framed by the subject's face: the reference's framing, applied to whatever footage is in the slot. */
export const Framed: React.FC<Props> = ({ slot, face, layer = 'full', cover = false, pin, offset = 0, playbackRate = 1, freeze, style }) => {
  const frame = useCurrentFrame();
  const info = SLOTS[slot];
  // Positions are in source frames (30 fps). Slots made with RIFE slow motion store `interp` frames per source
  // frame, so fractional positions (slow motion, motion-blur sub-frames) land on real in-between frames.
  const index = slotIndex(info, freeze ?? frame * playbackRate + offset);
  const ext = layer === 'cut' ? 'webp' : 'jpg';
  const src = staticFile(`${SLOT_ROOT}/${slot}/${layer}/${String(index).padStart(4, '0')}.${ext}`);
  const box = placeSlot(slot, face, cover, pin ?? (layer === 'cut' ? { bottom: true } : {}));
  const gap = box.left > 1 || box.top > 1 || box.left + box.width < W - 1 || box.top + box.height < H - 1;
  const fill = layer === 'full' && gap;
  return (
    <AbsoluteFill style={{ overflow: 'hidden', ...style }}>
      {fill && (
        <Img src={src} style={{ position: 'absolute', ...placeSlot(slot, face, true), filter: 'blur(90px) brightness(0.9) saturate(1.15)', scale: '1.15' }} />
      )}
      {/* Full layer: feather into the blurred fill. Cut layer: feather any footage edge that falls inside the screen
          (a selfie's frame edge slicing a shoulder or scarf), so it fades instead of showing a straight line. */}
      <Img src={src} style={{ position: 'absolute', ...box, ...(fill ? featherMask(box) : layer === 'cut' && gap ? featherMask(box, false) : null) }} />
    </AbsoluteFill>
  );
};
