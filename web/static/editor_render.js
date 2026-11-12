// SVG rendering of a plan: grid, rooms with name + area, walls (joined with round caps, as the desktop canvas
// draws them), openings, objects, dimension labels, selection handles and tool previews.
// renderPlan(S, opts) returns the inner markup of the <svg>; opts.paper = light print style for export.
import { esc } from './core.js';
import { footprint, isStair, labelPoint, midpoint, roomPolygon, wallLength, objCenter } from './geometry.js';
import { roomArea } from './stats.js';
import { formatDimension, fmt1 } from './units.js';
import { STYLE_COLORS, objectSvg, openingSvg, polyPoints, fx } from './editor_symbols.js';
import { findSel } from './editor_state.js';

export const ROTATE_HANDLE_PX = 30, HANDLE_PX = 8;

function gridSvg(S, k) {
  const v = S.view, x0 = -v.ox / v.s, y0 = -v.oy / v.s, x1 = (v.w - v.ox) / v.s, y1 = (v.h - v.oy) / v.s;
  let out = '';
  for (const [step, cls] of [[12, 'minor'], [120, 'major']]) {
    if (step * v.s < 6) continue;
    let d = '';
    for (let x = Math.floor(x0 / step) * step; x <= x1; x += step) d += `M${fx(x)} ${fx(y0)}V${fx(y1)}`;
    for (let y = Math.floor(y0 / step) * step; y <= y1; y += step) d += `M${fx(x0)} ${fx(y)}H${fx(x1)}`;
    out += `<path class="gridln ${cls}" d="${d}"/>`;
  }
  return out;
}

// Length label beside a wall, kept upright.
function dimLabel(w, k, unit) {
  const L = wallLength(w);
  if (L < 1) return '';
  const m = midpoint(w);
  let ang = Math.atan2(w.end.y - w.start.y, w.end.x - w.start.x) * 180 / Math.PI;
  if (ang > 90) ang -= 180; else if (ang <= -90) ang += 180;
  const r = ang * Math.PI / 180, off = w.thickness / 2 + 9 * k;
  const x = m.x + Math.sin(r) * off, y = m.y - Math.cos(r) * off;
  return `<text class="dim" x="${fx(x)}" y="${fx(y)}" font-size="${fx(11 * k)}" transform="rotate(${fx(ang)} ${fx(x)} ${fx(y)})">${esc(formatDimension(L, unit))}</text>`;
}

export function renderPlan(S, opts = {}) {
  const p = S.plan, k = 1 / S.view.s, paper = !!opts.paper;
  const sel = paper ? null : S.sel, selObj = paper ? null : findSel(S);
  const byId = new Map(p.walls.map(w => [w.id, w]));
  let svg = `<defs><marker id="arr" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse"><path d="M0 0L10 5L0 10z" class="arrhead"/></marker></defs>`;
  svg += `<g transform="translate(${fx(S.view.ox)} ${fx(S.view.oy)}) scale(${S.view.s})">`;
  if (S.showGrid && !opts.noGrid) svg += gridSvg(S, k);
  // rooms
  let labels = '';
  for (const r of p.rooms) {
    const poly = roomPolygon(r, p, undefined, byId);
    if (poly.length < 3) continue;
    const on = sel && sel.kind === 'room' && sel.id === r.id;
    svg += `<polygon class="room${on ? ' sel' : ''}" data-kind="room" data-id="${esc(r.id)}" points="${polyPoints(poly)}" fill="${esc(r.color || '#F0F0F0')}"><title>${esc(r.name)}</title></polygon>`;
    const c = labelPoint(poly), a = roomArea(r, p, byId);
    labels += `<text class="rname" x="${fx(c.x)}" y="${fx(c.y)}" font-size="${fx(13 * k)}">${esc(r.name)}</text>`;
    if (S.showAreas && a) labels += `<text class="rarea" x="${fx(c.x)}" y="${fx(c.y + 15 * k)}" font-size="${fx(11 * k)}">${fmt1(a)} sq ft</text>`;
  }
  // walls: outline pass then fill pass so joined walls read as one solid
  const wl = w => `x1="${fx(w.start.x)}" y1="${fx(w.start.y)}" x2="${fx(w.end.x)}" y2="${fx(w.end.y)}"`;
  for (const w of p.walls) svg += `<line class="wall-out" ${wl(w)} stroke-width="${fx(w.thickness + 2.4 * k)}"/>`;
  for (const w of p.walls) {
    const on = (sel && sel.kind === 'wall' && sel.id === w.id) || S.roomPick.includes(w.id);
    svg += `<line class="wall${on ? ' sel' : ''}" data-kind="wall" data-id="${esc(w.id)}" ${wl(w)} stroke-width="${fx(w.thickness)}" style="--wc:${STYLE_COLORS[w.wall_style] || '#D3D3D3'}"><title>${esc(w.wall_type.replace(/_/g, ' '))} wall, ${esc(formatDimension(wallLength(w), S.unit))}</title></line>`;
  }
  const gap = paper ? '#ffffff' : '#0a1226';
  for (const o of p.openings) {
    const w = byId.get(o.wall_id);
    if (w) svg += openingSvg(o, w, sel && sel.kind === 'opening' && sel.id === o.id ? 'sel' : '', k, gap);
  }
  for (const [list, kind] of [[p.furniture, 'furniture'], [p.fixtures, 'fixture'], [p.stairs, 'stair']]) {
    for (const o of list) svg += objectSvg(o, kind, sel && sel.kind === kind && sel.id === o.id ? 'sel' : '', k, true);
  }
  svg += labels;
  if (S.showDims) for (const w of p.walls) svg += dimLabel(w, k, S.unit);
  if (!paper) svg += overlays(S, selObj, k);
  return svg + '</g>';
}

// Selection handles, tool previews, measurements.
function overlays(S, obj, k) {
  let g = '';
  const hs = HANDLE_PX * k;
  if (obj && S.sel && ['furniture', 'fixture', 'stair'].includes(S.sel.kind)) {
    const fp = footprint(obj);
    g += `<polygon class="selbox" points="${polyPoints(fp)}"/>`;
    for (const q of fp) g += `<rect class="handle" x="${fx(q.x - hs / 2)}" y="${fx(q.y - hs / 2)}" width="${fx(hs)}" height="${fx(hs)}"/>`;
    const rh = rotateHandle(obj, k);
    const top = { x: (fp[0].x + fp[1].x) / 2, y: (fp[0].y + fp[1].y) / 2 };
    g += `<line class="selbox" x1="${fx(top.x)}" y1="${fx(top.y)}" x2="${fx(rh.x)}" y2="${fx(rh.y)}"/><circle class="handle rot" cx="${fx(rh.x)}" cy="${fx(rh.y)}" r="${fx(hs * 0.7)}"/>`;
  }
  if (obj && S.sel && S.sel.kind === 'wall') {
    for (const q of [obj.start, obj.end]) g += `<circle class="handle" cx="${fx(q.x)}" cy="${fx(q.y)}" r="${fx(hs * 0.7)}"/>`;
  }
  const t = S.temp, h = S.hover;
  if (t && t.kind === 'wall' && h) {
    g += `<line class="rubber" x1="${fx(t.start.x)}" y1="${fx(t.start.y)}" x2="${fx(h.x)}" y2="${fx(h.y)}"/>`;
    g += dimLabel({ start: t.start, end: h, thickness: 0 }, k, S.unit).replace('class="dim"', 'class="dim live"');
  }
  if (t && t.kind === 'stair' && h) g += `<line class="rubber" x1="${fx(t.start.x)}" y1="${fx(t.start.y)}" x2="${fx(h.x)}" y2="${fx(h.y)}"/>`;
  for (const m of S.measurements.concat(t && t.kind === 'measure' && h ? [{ start: t.start, end: h, live: true }] : [])) {
    const d = Math.hypot(m.end.x - m.start.x, m.end.y - m.start.y);
    const ang = ((Math.atan2(m.end.y - m.start.y, m.end.x - m.start.x) * 180 / Math.PI) + 360) % 360;
    const mx = (m.start.x + m.end.x) / 2, my = (m.start.y + m.end.y) / 2;
    g += `<g class="measure${m.live ? ' live' : ''}"><line x1="${fx(m.start.x)}" y1="${fx(m.start.y)}" x2="${fx(m.end.x)}" y2="${fx(m.end.y)}"/>`;
    g += `<circle cx="${fx(m.start.x)}" cy="${fx(m.start.y)}" r="${fx(4 * k)}"/><circle cx="${fx(m.end.x)}" cy="${fx(m.end.y)}" r="${fx(4 * k)}"/>`;
    g += `<text x="${fx(mx)}" y="${fx(my - 8 * k)}" font-size="${fx(11 * k)}">${esc(formatDimension(d, S.unit))}</text>`;
    g += `<text x="${fx(mx)}" y="${fx(my + 14 * k)}" font-size="${fx(11 * k)}">${fmt1(ang)}°</text></g>`;
  }
  if (S.libItem && h && S.tool === 'place' && S.libItem.kind !== 'stair') {
    const ghost = { position: h, width: S.libItem.width, depth: S.libItem.depth, rotation: 0 };
    g += `<polygon class="ghost" points="${polyPoints(footprint(ghost))}"/>`;
  }
  if (h && S.tool !== 'select' && S.tool !== 'pan') g += `<circle class="hover" cx="${fx(h.x)}" cy="${fx(h.y)}" r="${fx(5 * k)}"/>`;
  return g;
}

// Rotation handle: ROTATE_HANDLE_PX screen pixels beyond the middle of the object's top edge.
export function rotateHandle(o, k) {
  const fp = footprint(o), c = objCenter(o);
  const top = { x: (fp[0].x + fp[1].x) / 2, y: (fp[0].y + fp[1].y) / 2 };
  const d = Math.hypot(top.x - c.x, top.y - c.y) || 1;
  return { x: top.x + (top.x - c.x) / d * ROTATE_HANDLE_PX * k, y: top.y + (top.y - c.y) / d * ROTATE_HANDLE_PX * k };
}
export { isStair };
