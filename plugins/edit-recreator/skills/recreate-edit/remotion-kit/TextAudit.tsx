import { getInputProps } from 'remotion';

/** Text audit mode (used only by scripts/text-audit.mjs): hides everything except the one text layer named in
 *  the `textAudit` prop, on black, so its exact on-screen edges (glow included) can be measured.
 *  Put <TextAudit /> once inside your root composition. Normal renders never pass the prop. */
export const TextAudit: React.FC = () => {
  const { textAudit } = getInputProps() as { textAudit?: string };
  if (!textAudit) return null;
  const q = textAudit.replace(/"/g, '\\"');
  return (
    <style>{`html, body { background: #000 !important; }
      body * { visibility: hidden !important; }
      [data-text-layer="${q}"], [data-text-layer="${q}"] * { visibility: visible !important; }`}</style>
  );
};
