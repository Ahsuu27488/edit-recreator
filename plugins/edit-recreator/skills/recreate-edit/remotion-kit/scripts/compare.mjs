// Render chosen frames of your composition and stack each one under the matching reference frame.
// Usage (from your Remotion project): node <kit>/scripts/compare.mjs 30 90 150 ...
// Reads edit.config.json: { "composition": "MyEdit", "reference": "../ref.mp4", "offset": 0, "fps": 30, "props": {} }
// Your frame f lines up with reference frame f + offset. Output: work/compare/cmp_<f>.jpg and sheet.jpg.
import { bundle } from '@remotion/bundler';
import { renderStill, selectComposition } from '@remotion/renderer';
import { execFileSync } from 'node:child_process';
import { mkdirSync, readFileSync } from 'node:fs';
import path from 'node:path';

const cfg = JSON.parse(readFileSync(path.resolve('edit.config.json'), 'utf-8'));
const frames = process.argv.slice(2).map(Number).filter((n) => !Number.isNaN(n));
if (!frames.length) {
  console.error('usage: node compare.mjs <frame> [frame...]');
  process.exit(1);
}
const OUT = path.resolve('work/compare');
const REF = path.resolve(cfg.reference);
const fps = cfg.fps ?? 30;
// Seek to just BEFORE the frame's timestamp: +0.001 s lands one frame late.
const refTime = (f) => ((f + (cfg.offset ?? 0)) / fps - 0.001).toFixed(4);
mkdirSync(OUT, { recursive: true });

const serveUrl = await bundle({ entryPoint: path.resolve(cfg.entry ?? 'src/index.ts') });
const inputProps = cfg.props ?? {};
const composition = await selectComposition({ serveUrl, id: cfg.composition, inputProps });
const tiles = [];
for (const f of frames) {
  const ours = path.join(OUT, `ours_${f}.jpg`);
  await renderStill({ composition, serveUrl, output: ours, frame: f, imageFormat: 'jpeg', jpegQuality: 85, scale: 0.5, inputProps });
  const tile = path.join(OUT, `cmp_${f}.jpg`);
  execFileSync('ffmpeg', [
    '-v', 'error', '-y', '-ss', refTime(f), '-i', REF, '-i', ours,
    '-filter_complex', '[0]scale=960:540[a];[1]scale=960:540[b];[a][b]vstack',
    '-frames:v', '1', tile,
  ]);
  tiles.push(tile);
  console.log(`frame ${f}: ${tile} (top = reference, bottom = ours)`);
}
if (tiles.length > 1) {
  const cols = Math.min(4, tiles.length);
  const rows = Math.ceil(tiles.length / cols);
  const n = cols * rows;
  const pads = Array.from({ length: n - tiles.length }, () => ['-f', 'lavfi', '-i', 'color=c=black:s=960x1080:d=1']).flat();
  const layout = Array.from({ length: n }, (_, i) => `${(i % cols) * 960}_${Math.floor(i / cols) * 1080}`).join('|');
  execFileSync('ffmpeg', [
    '-v', 'error', '-y', ...tiles.flatMap((t) => ['-i', t]), ...pads,
    '-filter_complex', `${Array.from({ length: n }, (_, i) => `[${i}]`).join('')}xstack=inputs=${n}:layout=${layout},scale=iw/2:-1`,
    '-frames:v', '1', path.join(OUT, 'sheet.jpg'),
  ]);
  console.log(`sheet: ${path.join(OUT, 'sheet.jpg')}`);
}
