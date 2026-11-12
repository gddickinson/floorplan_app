// SVG symbols for openings, furniture, fixtures and stairs (plan coordinates in inches; k = 1 / pixels-per-inch,
// used to keep hairlines and text a constant size on screen).
import { esc } from './core.js';
import { footprint, isStair, openingCenter, wallLength } from './geometry.js';
import { isDoor, isWindow } from './model.js';
import { formatDimension } from './units.js';

const f = v => +v.toFixed(2);
const pts = a => a.map(p => `${f(p.x)},${f(p.y)}`).join(' ');

// Wall colours by style (gui/viewer_3d.py _get_wall_color), used in 2D and 3D.
export const STYLE_COLORS = { solid: '#D3D3D3', brick: '#B22222', concrete: '#808080', glass: '#87CEEB',
  curtain: '#B0C4DE', wood_frame: '#DEB887', metal_stud: '#C0C0C0', stone: '#696969' };

// Fixture colour groups as gui/canvas_drawing.py: kitchen silver, bathroom light blue, others grey.
const KITCHEN = ['refrigerator', 'stove', 'oven', 'dishwasher', 'microwave'];
const BATH = ['toilet', 'sink', 'bathtub', 'shower', 'vanity'];
export function fixtureColor(t) {
  if (t.includes('kitchen') || KITCHEN.includes(t)) return '#C0C0C0';
  if (BATH.includes(t)) return '#ADD8E6';
  return '#808080';
}

// Opening: a gap cut in the wall plus the door/window symbol.
export function openingSvg(o, w, cls, k, gapColor) {
  const L = wallLength(w);
  if (L < 1e-6) return '';
  const ux = (w.end.x - w.start.x) / L, uy = (w.end.y - w.start.y) / L, nx = -uy, ny = ux;
  const c = openingCenter(w, o.position), h = o.width / 2;
  const a = { x: c.x - ux * h, y: c.y - uy * h }, b = { x: c.x + ux * h, y: c.y + uy * h };
  const t = w.thickness / 2;
  const P = (p, s, d = 0) => ({ x: p.x + nx * s + ux * d, y: p.y + ny * s + uy * d });
  let g = `<line class="gap" x1="${f(a.x)}" y1="${f(a.y)}" x2="${f(b.x)}" y2="${f(b.y)}" stroke="${gapColor}" stroke-width="${f(w.thickness + 2 * k)}"/>`;
  g += `<line class="jamb" x1="${f(P(a, -t).x)}" y1="${f(P(a, -t).y)}" x2="${f(P(a, t).x)}" y2="${f(P(a, t).y)}"/>`;
  g += `<line class="jamb" x1="${f(P(b, -t).x)}" y1="${f(P(b, -t).y)}" x2="${f(P(b, t).x)}" y2="${f(P(b, t).y)}"/>`;
  const ty = o.opening_type;
  const leaf = (hinge, len, dir) => {  // hinged leaf opening to the +normal side, arc back to the wall
    const tip = P(hinge, len);
    const end = { x: hinge.x + ux * len * dir, y: hinge.y + uy * len * dir };
    const sweep = dir > 0 ? 0 : 1;  // n is u turned +90 degrees: back to +u is counter-clockwise
    return `<line class="leaf" x1="${f(hinge.x)}" y1="${f(hinge.y)}" x2="${f(tip.x)}" y2="${f(tip.y)}"/>` +
      `<path class="swing" d="M${f(tip.x)} ${f(tip.y)} A${f(len)} ${f(len)} 0 0 ${sweep} ${f(end.x)} ${f(end.y)}"/>`;
  };
  if (isDoor(ty)) {
    if (ty === 'door_double' || ty === 'door_french') g += leaf(a, h, 1) + leaf(b, h, -1);
    else if (ty === 'door_sliding' || ty === 'door_pocket') {
      const s = t * 0.45;
      g += `<line class="leaf" x1="${f(P(a, -s).x)}" y1="${f(P(a, -s).y)}" x2="${f(P(a, -s, o.width * 0.6).x)}" y2="${f(P(a, -s, o.width * 0.6).y)}"/>`;
      g += `<line class="leaf" x1="${f(P(b, s).x)}" y1="${f(P(b, s).y)}" x2="${f(P(b, s, -o.width * 0.6).x)}" y2="${f(P(b, s, -o.width * 0.6).y)}"/>`;
    } else if (ty === 'door_bifold') {
      const q = o.width / 4, d = Math.min(q, 10);
      const z = [a, P(a, d, q), P(a, 0, 2 * q), P(a, d, 3 * q), b];
      g += `<polyline class="leaf" points="${pts(z)}"/>`;
    } else if (ty === 'door_garage') {
      g += `<line class="leaf dash" x1="${f(a.x)}" y1="${f(a.y)}" x2="${f(b.x)}" y2="${f(b.y)}"/>`;
    } else g += leaf(a, o.width, 1);
  } else if (isWindow(ty)) {
    const s = t * 0.5;
    const cls2 = ty === 'window_skylight' ? 'pane dash' : 'pane';
    for (const off of [-s, 0, s]) {
      const p1 = P(a, off), p2 = P(b, off);
      g += `<line class="${cls2}" x1="${f(p1.x)}" y1="${f(p1.y)}" x2="${f(p2.x)}" y2="${f(p2.y)}"/>`;
    }
  } else {
    g += `<line class="pane dash" x1="${f(a.x)}" y1="${f(a.y)}" x2="${f(b.x)}" y2="${f(b.y)}"/>`;
  }
  // wide invisible target for clicking
  g += `<line class="hit" x1="${f(a.x)}" y1="${f(a.y)}" x2="${f(b.x)}" y2="${f(b.y)}" stroke-width="${f(w.thickness + 8 * k)}"/>`;
  const label = `${ty.replace(/_/g, ' ')} ${formatDimension(o.width, 'in')}`;
  return `<g class="opening ${isDoor(ty) ? 'door' : isWindow(ty) ? 'window' : 'arch'} ${cls}" data-kind="opening" data-id="${esc(o.id)}"><title>${esc(label)}</title>${g}</g>`;
}

// Furniture / fixture / stair footprint with its label.
export function objectSvg(o, kind, cls, k, showLabels) {
  const fp = footprint(o);
  let fill = '#8B7355';
  if (kind === 'fixture') fill = fixtureColor(o.fixture_type);
  if (isStair(o)) fill = '#A0522D';
  let body = `<polygon class="body" points="${pts(fp)}" fill="${fill}" stroke="${fill}"/>`;
  if (isStair(o)) {
    const n = Math.max(1, Math.round(o.num_steps));
    for (let i = 1; i < n; i++) {
      const t = i / n, p = { x: fp[0].x + (fp[3].x - fp[0].x) * t, y: fp[0].y + (fp[3].y - fp[0].y) * t };
      const q = { x: fp[1].x + (fp[2].x - fp[1].x) * t, y: fp[1].y + (fp[2].y - fp[1].y) * t };
      body += `<line class="tread" x1="${f(p.x)}" y1="${f(p.y)}" x2="${f(q.x)}" y2="${f(q.y)}"/>`;
    }
    body += `<line class="arrow" x1="${f(o.start.x)}" y1="${f(o.start.y)}" x2="${f(o.end.x)}" y2="${f(o.end.y)}" marker-end="url(#arr)"/>`;
  }
  const name = isStair(o) ? o.stair_type.replace(/_/g, ' ') + ' stair' : o.name;
  const c = fp.reduce((s, p) => ({ x: s.x + p.x / 4, y: s.y + p.y / 4 }), { x: 0, y: 0 });
  const fs = Math.min(11 * k, o.width / 4.5, 14);
  const text = showLabels && fs > 2.5 * k
    ? `<text class="olabel" x="${f(c.x)}" y="${f(c.y)}" font-size="${f(fs)}">${esc(name)}</text>` : '';
  return `<g class="obj ${kind} ${cls}" data-kind="${kind}" data-id="${esc(o.id)}"><title>${esc(name)}</title>${body}${text}</g>`;
}

export const polyPoints = pts;
export const fx = f;
