import React from 'react';
import { Freeze, useCurrentFrame, useVideoConfig } from 'remotion';

/** [master seconds, output seconds] pairs, both increasing. */
export type Anchors = readonly (readonly [number, number])[];

/** Piecewise-linear map through the anchor pairs; `from` 0 maps master→output, 1 maps output→master. */
export const warpTime = (anchors: Anchors, t: number, from: 0 | 1 = 1): number => {
  const to = (1 - from) as 0 | 1;
  if (t <= anchors[0][from]) return anchors[0][to] + (t - anchors[0][from]);
  for (let i = 1; i < anchors.length; i++) {
    const a = anchors[i - 1];
    const b = anchors[i];
    if (t <= b[from]) return a[to] + ((t - a[from]) / (b[from] - a[from])) * (b[to] - a[to]);
  }
  const l = anchors[anchors.length - 1];
  return l[to] + (t - l[from]);
};

/**
 * Re-time a whole timeline to a different voiceover without rebuilding it.
 *
 * Build the scenes once, timed to the master VO (e.g. English). For another VO (another language, another voice),
 * list matching moments as anchors: [[0, 0], [2.64, 2.83], [4.8, 4.64], ..., [40, 41.2]] = "the master's 2.64 s
 * ($500) is said at 2.83 s in this VO". Children then play on the master clock, sped up or slowed down per
 * segment, so every beat still lands on its word. Fractional frames are fine: springs, interpolate and
 * videos all accept them.
 *
 * Keep the VO, captions and sound effects OUTSIDE the warp (they run on the real clock), and map SFX times
 * with warpTime(anchors, t, 0).
 */
export const TimeWarp: React.FC<{ anchors: Anchors; children: React.ReactNode }> = ({ anchors, children }) => {
  const f = useCurrentFrame();
  const { fps } = useVideoConfig();
  const master = Math.max(0, warpTime(anchors, f / fps, 1) * fps);
  return <Freeze frame={master}>{children}</Freeze>;
};
