/** Image index inside a prepared slot for a position given in SOURCE frames (30 fps).
 *  `files` images were written; `interp` of them per source frame when the slot was slowed down with RIFE. */
export const slotIndex = (info: { readonly files?: number; readonly frames: number; readonly interp?: number }, pos: number) => {
  const k = info.interp ?? 1;
  const files = info.files ?? info.frames;
  return Math.max(0, Math.min(files - 1, Math.floor(pos * k + 1e-6)));
};
