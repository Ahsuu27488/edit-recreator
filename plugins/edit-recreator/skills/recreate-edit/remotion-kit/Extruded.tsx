/** Real 3D extruded text (like After Effects' 3D text layers in the reference): a stack of copies pushed back
 *  in depth, so turning it with rotateY/rotateX shows solid sides. Great for big title words that turn in. */
type Props = {
  readonly text: string;
  readonly fontFamily: string;
  readonly fontSize: number;
  readonly fontWeight?: number | string;
  /** Front face: any CSS background (gradient) painted through the letters. */
  readonly face: string;
  /** Side colour at the front edge and at the back (the extrusion shades between them). */
  readonly sideFront: string;
  readonly sideBack: string;
  /** Extrusion depth in px and how many slices build it (more = smoother sides). */
  readonly depth?: number;
  readonly slices?: number;
  readonly rotateY?: number;
  readonly rotateX?: number;
  readonly perspective?: number;
  /** Squash/stretch of the letters before the 3D turn (the reference squeezes them tall and narrow). */
  readonly scaleX?: number;
  readonly scaleY?: number;
  readonly letterSpacing?: string;
  readonly opacity?: number;
  /** Soft shadow cast on the background, e.g. "drop-shadow(12px 16px 18px #0005)". */
  readonly shadow?: string;
  readonly style?: React.CSSProperties;
  readonly layerName?: string;
};

const mix = (a: string, b: string, t: number) => {
  const pa = [1, 3, 5].map((i) => parseInt(a.slice(i, i + 2), 16));
  const pb = [1, 3, 5].map((i) => parseInt(b.slice(i, i + 2), 16));
  return `#${pa.map((v, i) => Math.round(v + (pb[i] - v) * t).toString(16).padStart(2, '0')).join('')}`;
};

export const Extruded: React.FC<Props> = ({
  text,
  fontFamily,
  fontSize,
  fontWeight = 400,
  face,
  sideFront,
  sideBack,
  depth = 40,
  slices = 16,
  rotateY = 0,
  rotateX = 0,
  perspective = 1600,
  scaleX = 1,
  scaleY = 1,
  letterSpacing = '0',
  opacity = 1,
  shadow,
  style,
  layerName,
}) => {
  const glyph: React.CSSProperties = { fontFamily, fontSize, fontWeight, lineHeight: 1, letterSpacing, whiteSpace: 'nowrap' };
  return (
    <div data-text-layer={layerName ?? text} style={{ position: 'absolute', perspective, opacity, filter: shadow, ...style }}>
      <div
        style={{
          position: 'relative',
          transformStyle: 'preserve-3d',
          transform: `rotateX(${rotateX}deg) rotateY(${rotateY}deg) scale(${scaleX}, ${scaleY})`,
        }}
      >
        {Array.from({ length: slices }, (_, k) => {
          const i = slices - k; // back to front
          return (
            <div
              key={i}
              style={{
                ...glyph,
                position: 'absolute',
                inset: 0,
                color: mix(sideFront, sideBack, i / slices),
                transform: `translateZ(${(-i * depth) / slices}px)`,
              }}
            >
              {text}
            </div>
          );
        })}
        <div style={{ ...glyph, position: 'relative', background: face, WebkitBackgroundClip: 'text', backgroundClip: 'text', color: 'transparent' }}>
          {text}
        </div>
      </div>
    </div>
  );
};
