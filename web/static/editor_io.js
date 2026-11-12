// Open / save .floorplan files (the desktop JSON format) and export the plan as SVG or PNG.
import { download } from './core.js';
import { fromDict, toFileText } from './model.js';
import { extent } from './geometry.js';
import { renderPlan } from './editor_render.js';

export const safeName = s => (s || 'floorplan').replace(/[^\w.-]+/g, '_').replace(/^_+|_+$/g, '') || 'floorplan';

export function savePlan(S) {
  download(safeName(S.plan.name) + '.floorplan', toFileText(S.plan), 'application/json');
  S.dirty = false;
}

// Parse a .floorplan file's text; throws with a readable message.
export function parsePlanText(text) {
  let d;
  try { d = JSON.parse(text); } catch (e) { throw new Error('not a JSON file: ' + e.message); }
  return fromDict(d);
}

export function openFile(file) {
  return file.text().then(parsePlanText);
}

const PAPER_CSS = `
.gridln{stroke:#e0e0e0;stroke-width:.5px;vector-effect:non-scaling-stroke;fill:none}.gridln.major{stroke:#c8c8c8}
.room{fill-opacity:.45;stroke:none}.wall-out{stroke:#000;stroke-linecap:round}
.wall{stroke:#3a3a3a;stroke-linecap:round}.gap{stroke-linecap:butt}.jamb,.leaf,.pane{stroke:#000;stroke-width:1px;vector-effect:non-scaling-stroke;fill:none}
.swing{stroke:#555;stroke-width:.8px;vector-effect:non-scaling-stroke;fill:none;stroke-dasharray:3 2}.dash{stroke-dasharray:4 3}
.opening.door .leaf{stroke:#8B4513}.opening.window .pane{stroke:#2a7fbf}.hit{stroke:transparent}
.obj .body{fill-opacity:.25;stroke-width:1.4px;vector-effect:non-scaling-stroke}
.tread,.arrow{stroke:#A0522D;stroke-width:.8px;vector-effect:non-scaling-stroke}.arrhead{fill:#A0522D}
text{font-family:Helvetica,Arial,sans-serif;text-anchor:middle;dominant-baseline:middle}
.rname{font-weight:700;fill:#000}.rarea{fill:#333}.olabel{fill:#222}.dim{fill:#444}`;

// A standalone SVG of the whole plan (light "paper" style, fitted with a margin, grid off) with a title line.
export function exportSvgText(S, widthPx = 1600) {
  const e = extent(S.plan), m = 18 + Math.max(0, ...S.plan.walls.map(w => w.thickness));
  const wIn = Math.max(1, e.maxX - e.minX) + 2 * m, hIn = Math.max(1, e.maxY - e.minY) + 2 * m;
  const s = widthPx / wIn, H = Math.round(hIn * s) + 40;
  const view = { s, ox: (m - e.minX) * s, oy: (m - e.minY) * s + 40, w: widthPx, h: H };
  const T = { ...S, view, sel: null, temp: null, hover: null, roomPick: [], measurements: [], showGrid: false };
  const body = renderPlan(T, { paper: true, noGrid: true });
  const title = (S.plan.name || 'Floor plan').replace(/[<&>]/g, c => ({ '<': '&lt;', '>': '&gt;', '&': '&amp;' }[c]));
  return `<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="${widthPx}" height="${H}" viewBox="0 0 ${widthPx} ${H}">
<style>${PAPER_CSS}</style><rect width="100%" height="100%" fill="#fff"/>
<text x="16" y="24" style="text-anchor:start;font-size:18px;font-weight:700;fill:#000">${title}</text>
${body}</svg>`;
}

export function exportSvg(S) {
  download(safeName(S.plan.name) + '.svg', exportSvgText(S), 'image/svg+xml');
}

export function exportPng(S, widthPx = 2400) {
  const text = exportSvgText(S, widthPx);
  const img = new Image();
  const url = URL.createObjectURL(new Blob([text], { type: 'image/svg+xml' }));
  return new Promise((resolve, reject) => {
    img.onload = () => {
      const c = document.createElement('canvas');
      c.width = img.width; c.height = img.height;
      c.getContext('2d').drawImage(img, 0, 0);
      URL.revokeObjectURL(url);
      c.toBlob(b => { download(safeName(S.plan.name) + '.png', b); resolve(); }, 'image/png');
    };
    img.onerror = () => { URL.revokeObjectURL(url); reject(new Error('could not render the plan to PNG')); };
    img.src = url;
  });
}
