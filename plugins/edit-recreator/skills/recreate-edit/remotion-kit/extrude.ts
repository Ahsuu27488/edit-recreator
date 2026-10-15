/** Stacked text-shadows that fake a 3D extruded letter (cheap alternative to Extruded.tsx). */
export const extrude = (side: string, depth: number, glowColor?: string, dx = 1, dy = 1.4) => {
  const layers = Array.from({ length: depth }, (_, i) => `${((i + 1) * dx).toFixed(1)}px ${((i + 1) * dy).toFixed(1)}px 0 ${side}`);
  layers.push(`${(depth * dx + 4).toFixed(0)}px ${(depth * dy + 6).toFixed(0)}px 14px #0007`);
  if (glowColor) layers.push(`0 0 30px ${glowColor}`, `0 0 70px ${glowColor}`);
  return layers.join(', ');
};
