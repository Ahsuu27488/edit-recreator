// No cut-off text: render every text layer ALONE on black (the textAudit prop, see TextAudit.tsx) at a frame
// where it is fully shown, then report how close its letters and its glow come to each frame edge.
// Usage (from your Remotion project): node <kit>/scripts/text-audit.mjs [only-this-layer]
// Reads edit.config.json: { "composition": "MyEdit", "python": "python", "textChecks": [["TITLE", 120], ...] }
// Each text element needs data-text-layer="<name>". Output: work/audit/*.png and a margins table.
import { bundle } from '@remotion/bundler';
import { renderStill, selectComposition } from '@remotion/renderer';
import { execFileSync } from 'node:child_process';
import { mkdirSync, readFileSync, writeFileSync } from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const here = path.dirname(fileURLToPath(import.meta.url));
const cfg = JSON.parse(readFileSync(path.resolve('edit.config.json'), 'utf-8'));
const only = process.argv[2];
const OUT = path.resolve('work/audit');
mkdirSync(OUT, { recursive: true });
const serveUrl = await bundle({ entryPoint: path.resolve(cfg.entry ?? 'src/index.ts') });
const manifest = [];
for (const [i, [layer, frame]] of cfg.textChecks.entries()) {
  if (only && layer !== only) continue;
  const inputProps = { ...(cfg.props ?? {}), textAudit: layer };
  const composition = await selectComposition({ serveUrl, id: cfg.composition, inputProps });
  const file = path.join(OUT, `${String(i).padStart(2, '0')}_${frame}.png`);
  await renderStill({ composition, serveUrl, output: file, frame, imageFormat: 'png', inputProps });
  manifest.push({ layer, frame, file });
  process.stdout.write('.');
}
writeFileSync(path.join(OUT, 'manifest.json'), JSON.stringify(manifest, null, 2), 'utf-8');
console.log('');
const textBounds = path.resolve(here, '..', '..', 'scripts', 'text_bounds.py');
execFileSync(cfg.python ?? 'python', [textBounds, path.join(OUT, 'manifest.json')], { stdio: 'inherit' });
