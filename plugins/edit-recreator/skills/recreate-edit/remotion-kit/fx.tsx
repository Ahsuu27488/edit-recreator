import { AbsoluteFill, Easing, interpolate, random, useCurrentFrame } from 'remotion';

export const clamp = { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' } as const;

/** Layered text-shadow that reads as a neon/bloom glow. */
export const glow = (color: string, strength = 1) =>
  [6, 14, 28, 52]
    .map((r, i) => `0 0 ${r * strength}px ${i < 2 ? '#fff8' : color}`)
    .join(', ');

/** Deterministic camera shake: returns a CSS translate for this frame, decaying over `duration` frames. */
export const shake = (frame: number, start: number, duration: number, amount: number, seed = 'shake') => {
  const t = frame - start;
  if (t < 0 || t > duration) return '0px 0px';
  const decay = 1 - t / duration;
  const x = (random(`${seed}-x-${t}`) - 0.5) * 2 * amount * decay;
  const y = (random(`${seed}-y-${t}`) - 0.5) * 2 * amount * decay;
  return `${x.toFixed(1)}px ${y.toFixed(1)}px`;
};

/** Blur that ramps up into a cut and back down after it (soft "defocus" transitions). */
export const blurAround = (frame: number, cut: number, before = 5, after = 4, max = 28) =>
  interpolate(frame, [cut - before, cut, cut + after], [0, max, 0], clamp);

/** A full-frame colour flash, e.g. white or yellow, peaking at `at`. */
export const Flash: React.FC<{ at: number; color?: string; length?: number; max?: number }> = ({
  at,
  color = '#fff',
  length = 6,
  max = 1,
}) => {
  const frame = useCurrentFrame();
  const opacity = interpolate(frame, [at - 1, at, at + length], [0, max, 0], {
    ...clamp,
    easing: Easing.out(Easing.quad),
  });
  return <AbsoluteFill style={{ background: color, opacity, pointerEvents: 'none' }} />;
};

/** Screen-blends a texture or overlay on top of everything below it. */
export const blend = (mode: React.CSSProperties['mixBlendMode'], opacity = 1): React.CSSProperties => ({
  mixBlendMode: mode,
  opacity,
});
