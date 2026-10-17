import React from 'react';
import { AbsoluteFill, Easing, interpolate, useCurrentFrame, useVideoConfig } from 'remotion';

/** One spoken word with its start/end in seconds (scripts/vo_words.py writes this format). */
export type Word = { w: string; s: number; e: number };

/** Group words into short caption chunks: break on a pause over 0.3 s, after , . : or at maxWords. */
export const toChunks = (words: Word[], maxWords = 3): Word[][] => {
  const out: Word[][] = [];
  let cur: Word[] = [];
  words.forEach((w, i) => {
    const next = words[i + 1];
    cur.push(w);
    if (!next || next.s - w.e > 0.3 || /[.,:!?]$/.test(w.w) || cur.length >= maxWords) {
      out.push(cur);
      cur = [];
    }
  });
  return out;
};

/**
 * Reels-style word-by-word captions: a chunk pops in, the spoken word lights up in `accent`.
 * Place them in the Reels/Shorts safe zone (y about 1250-1450 on 1080x1920): the app's own UI covers the bottom
 * ~320 px and the right ~120 px. For a language the viewer reads in Latin letters (Hinglish, Roman Urdu),
 * pass romanised words with the transcript's timings.
 */
export const Captions: React.FC<{
  words: Word[];
  y?: number;
  accent?: string;
  font?: string;
  size?: number;
  hide?: (frame: number) => boolean;
}> = ({ words, y = 1330, accent = '#d97757', font = 'Inter, sans-serif', size = 76, hide }) => {
  const chunks = React.useMemo(() => toChunks(words), [words]);
  const f = useCurrentFrame();
  const { fps } = useVideoConfig();
  const t = f / fps;
  if (hide?.(f)) return null;
  const i = chunks.findIndex((c, k) => t >= c[0].s - 0.05 && (k === chunks.length - 1 || t < chunks[k + 1][0].s - 0.05));
  if (i < 0) return null;
  const c = chunks[i];
  if (t > c[c.length - 1].e + 0.6) return null;
  const local = f - Math.round((c[0].s - 0.05) * fps);
  const pop = interpolate(local, [0, 4], [0.82, 1], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: Easing.bezier(0.16, 1, 0.3, 1) });
  return (
    <AbsoluteFill style={{ alignItems: 'center', pointerEvents: 'none' }}>
      <div style={{ position: 'absolute', top: y, width: 940, textAlign: 'center', transform: `scale(${pop})`, fontFamily: font, fontWeight: 900, fontSize: size, lineHeight: 1.08, textTransform: 'uppercase' }}>
        {c.map((w, k) => {
          const on = t >= w.s - 0.03;
          const active = on && (k === c.length - 1 || t < c[k + 1].s - 0.03);
          return (
            <span
              key={k}
              style={{
                color: active ? accent : on ? '#f5f3ee' : 'rgba(245,243,238,0.35)',
                WebkitTextStroke: '3px rgba(0,0,0,0.85)',
                paintOrder: 'stroke fill',
                textShadow: '0 6px 24px rgba(0,0,0,0.75)',
                marginRight: 18,
                display: 'inline-block',
                transform: active ? 'translateY(-4px) scale(1.06)' : undefined,
              }}
            >
              {w.w.replace(/[,.:!?]$/, '')}
            </span>
          );
        })}
      </div>
    </AbsoluteFill>
  );
};
