/** Smooth keyframe curve through measured points, like After Effects' auto-bezier keyframes.
 *  Monotone cubic (Fritsch–Carlson): passes exactly through every point, never overshoots, and holds the
 *  first/last value outside the range. Points: [[frame, value], ...] sorted by frame. */
export const curve = (frame: number, points: readonly (readonly [number, number])[]): number => {
  const n = points.length;
  if (n === 0) return 0;
  if (frame <= points[0][0]) return points[0][1];
  if (frame >= points[n - 1][0]) return points[n - 1][1];
  if (n === 2) {
    const [[x0, y0], [x1, y1]] = points;
    return y0 + ((frame - x0) / (x1 - x0)) * (y1 - y0);
  }
  const xs = points.map((p) => p[0]);
  const ys = points.map((p) => p[1]);
  const d = xs.slice(0, -1).map((x, i) => (ys[i + 1] - ys[i]) / (xs[i + 1] - x));
  const m = xs.map((_, i) => (i === 0 ? d[0] : i === n - 1 ? d[n - 2] : d[i - 1] * d[i] <= 0 ? 0 : (d[i - 1] + d[i]) / 2));
  for (let i = 0; i < n - 1; i++) {
    if (d[i] === 0) {
      m[i] = 0;
      m[i + 1] = 0;
      continue;
    }
    const a = m[i] / d[i];
    const b = m[i + 1] / d[i];
    const s = a * a + b * b;
    if (s > 9) {
      const t = 3 / Math.sqrt(s);
      m[i] = t * a * d[i];
      m[i + 1] = t * b * d[i];
    }
  }
  let i = 0;
  while (frame > xs[i + 1]) i++;
  const h = xs[i + 1] - xs[i];
  const t = (frame - xs[i]) / h;
  const t2 = t * t;
  const t3 = t2 * t;
  return (
    (2 * t3 - 3 * t2 + 1) * ys[i] + (t3 - 2 * t2 + t) * h * m[i] + (-2 * t3 + 3 * t2) * ys[i + 1] + (t3 - t2) * h * m[i + 1]
  );
};
