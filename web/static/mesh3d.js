// Triangle mesh of a plan for the WebGL preview: floor slab, room floors, walls with door/window openings cut
// out (lintels above doors, sills below and heads above windows), furniture/fixture blocks and stepped stairs.
// World axes: X = plan x, Z = plan y, Y = up (inches). Wall heights, opening heights/sills and the ceiling height
// come from the plan; furniture/fixture heights are not in the file format, so OBJECT_HEIGHT gives display values.
import { extent, footprint, isStair, pointSegmentDistance, roomPolygon, wallLength } from './geometry.js';
import { isDoor, isWindow } from './model.js';
import { STYLE_COLORS, fixtureColor } from './editor_symbols.js';

export const OBJECT_HEIGHT = { bed_single: 24, bed_double: 24, bed_queen: 24, bed_king: 24, sofa: 32, loveseat: 32,
  chair: 34, armchair: 34, table_dining: 30, table_coffee: 18, table_side: 24, desk: 30, dresser: 34, nightstand: 26,
  bookshelf: 72, cabinet: 36, wardrobe: 78, tv_stand: 24, toilet: 30, sink: 34, sink_double: 34, bathtub: 20,
  shower: 4, shower_corner: 4, vanity: 34, refrigerator: 70, stove: 36, oven: 36, dishwasher: 34, microwave: 18,
  sink_kitchen: 36, washer: 38, dryer: 38, water_heater: 60, furnace: 48, ac_unit: 36 };

export const hexRgb = h => {
  const m = /^#?([0-9a-f]{6})$/i.exec(h || '');
  const n = m ? parseInt(m[1], 16) : 0xd3d3d3;
  return [(n >> 16 & 255) / 255, (n >> 8 & 255) / 255, (n & 255) / 255];
};

class Builder {
  constructor() { this.pos = []; this.col = []; this.nrm = []; }
  tri(a, b, c, rgb) {
    const u = [b[0] - a[0], b[1] - a[1], b[2] - a[2]], v = [c[0] - a[0], c[1] - a[1], c[2] - a[2]];
    let n = [u[1] * v[2] - u[2] * v[1], u[2] * v[0] - u[0] * v[2], u[0] * v[1] - u[1] * v[0]];
    const l = Math.hypot(...n) || 1; n = n.map(x => x / l);
    for (const p of [a, b, c]) { this.pos.push(...p); this.col.push(...rgb); this.nrm.push(...n); }
  }
  quad(a, b, c, d, rgb) { this.tri(a, b, c, rgb); this.tri(a, c, d, rgb); }
  // Prism over a 2D footprint (plan points) from y0 to y1.
  prism(fp, y0, y1, rgb) {
    const P = (p, y) => [p.x, y, p.y];
    for (let i = 0; i < fp.length; i++) {
      const a = fp[i], b = fp[(i + 1) % fp.length];
      this.quad(P(a, y0), P(b, y0), P(b, y1), P(a, y1), rgb.map(c => c * 0.92));
    }
    for (const [i, j, k] of triangulate(fp)) {
      this.tri(P(fp[i], y1), P(fp[j], y1), P(fp[k], y1), rgb);
      if (y0 > 0.01) this.tri(P(fp[i], y0), P(fp[j], y0), P(fp[k], y0), rgb.map(c => c * 0.8));
    }
  }
  arrays() {
    return { position: new Float32Array(this.pos), color: new Float32Array(this.col), normal: new Float32Array(this.nrm),
      count: this.pos.length / 3 };
  }
}

// Ear-clipping triangulation of a simple polygon; returns index triples.
export function triangulate(pts) {
  const n = pts.length;
  if (n < 3) return [];
  let area = 0;
  for (let i = 0; i < n; i++) { const a = pts[i], b = pts[(i + 1) % n]; area += a.x * b.y - b.x * a.y; }
  const idx = [...Array(n).keys()];
  if (area < 0) idx.reverse();
  const cross = (a, b, c) => (b.x - a.x) * (c.y - a.y) - (b.y - a.y) * (c.x - a.x);
  const inside = (p, a, b, c) => cross(a, b, p) >= 0 && cross(b, c, p) >= 0 && cross(c, a, p) >= 0;
  const out = [];
  let guard = 0;
  while (idx.length > 3 && guard++ < 10000) {
    let clipped = false;
    for (let i = 0; i < idx.length; i++) {
      const i0 = idx[(i + idx.length - 1) % idx.length], i1 = idx[i], i2 = idx[(i + 1) % idx.length];
      const a = pts[i0], b = pts[i1], c = pts[i2];
      if (cross(a, b, c) <= 1e-9) continue;
      if (idx.some(j => j !== i0 && j !== i1 && j !== i2 && inside(pts[j], a, b, c))) continue;
      out.push([i0, i1, i2]); idx.splice(i, 1); clipped = true; break;
    }
    if (!clipped) break;  // degenerate polygon: stop rather than loop
  }
  if (idx.length === 3) out.push([idx[0], idx[1], idx[2]]);
  return out;
}

// Wall box pieces: solid spans plus the parts above/below each opening.
function addWall(B, w, plan) {
  const L = wallLength(w);
  if (L < 0.1) return;
  const H = w.height, ux = (w.end.x - w.start.x) / L, uy = (w.end.y - w.start.y) / L, t = w.thickness / 2;
  const joins = p => plan.walls.some(o => o !== w && pointSegmentDistance(p, o.start, o.end) <= 1.0);
  const s0 = joins(w.start) ? -t : 0, s1 = L + (joins(w.end) ? t : 0);
  const rgb = hexRgb(STYLE_COLORS[w.wall_style]);
  const box = (a, b, y0, y1) => {
    if (b - a < 0.01 || y1 - y0 < 0.01) return;
    const fp = [[a, -t], [b, -t], [b, t], [a, t]].map(([s, n]) => ({ x: w.start.x + ux * s - uy * n, y: w.start.y + uy * s + ux * n }));
    B.prism(fp, y0, y1, rgb);
  };
  const ops = plan.openings.filter(o => o.wall_id === w.id)
    .map(o => ({ o, a: Math.max(s0, o.position * L - o.width / 2), b: Math.min(s1, o.position * L + o.width / 2) }))
    .filter(r => r.b > r.a).sort((p, q) => p.a - q.a);
  let s = s0;
  for (const { o, a, b } of ops) {
    if (a > s) box(s, a, 0, H);
    const lo = Math.max(a, s);
    if (isWindow(o.opening_type)) {
      const sill = Math.min(H, Math.max(0, o.sill_height));
      box(lo, b, 0, sill);
      box(lo, b, Math.min(H, sill + o.height), H);
    } else box(lo, b, Math.min(H, o.height), H);   // doors and archways: lintel above
    s = Math.max(s, b);
  }
  if (s1 > s) box(s, s1, 0, H);
}

export function buildMesh(plan) {
  const B = new Builder(), e = extent(plan), pad = 24;
  const slab = [{ x: e.minX - pad, y: e.minY - pad }, { x: e.maxX + pad, y: e.minY - pad }, { x: e.maxX + pad, y: e.maxY + pad }, { x: e.minX - pad, y: e.maxY + pad }];
  B.prism(slab, -4, 0, hexRgb('#F5F5DC').map(c => c * 0.55));
  const byId = new Map(plan.walls.map(w => [w.id, w]));
  for (const r of plan.rooms) {
    const poly = roomPolygon(r, plan, undefined, byId);
    if (poly.length < 3) continue;
    const rgb = hexRgb(r.color || '#F0F0F0');
    for (const [i, j, k] of triangulate(poly)) B.tri([poly[i].x, 0.4, poly[i].y], [poly[j].x, 0.4, poly[j].y], [poly[k].x, 0.4, poly[k].y], rgb);
  }
  for (const w of plan.walls) addWall(B, w, plan);
  for (const f of plan.furniture) B.prism(footprint(f), 0.5, OBJECT_HEIGHT[f.furniture_type] || 30, hexRgb('#8B7355'));
  for (const f of plan.fixtures) B.prism(footprint(f), 0.5, OBJECT_HEIGHT[f.fixture_type] || 30, hexRgb(fixtureColor(f.fixture_type)));
  for (const s of plan.stairs) {
    const n = Math.max(1, Math.round(s.num_steps)), fp = footprint(s), rise = plan.ceiling_height / n;
    for (let i = 0; i < n; i++) {
      const lerp = (p, q, t) => ({ x: p.x + (q.x - p.x) * t, y: p.y + (q.y - p.y) * t });
      const t0 = i / n, t1 = (i + 1) / n;
      B.prism([lerp(fp[0], fp[3], t0), lerp(fp[1], fp[2], t0), lerp(fp[1], fp[2], t1), lerp(fp[0], fp[3], t1)], 0.5, rise * (i + 1), hexRgb('#A0522D'));
    }
  }
  const m = B.arrays();
  const H = Math.max(96, ...plan.walls.map(w => w.height));
  m.bounds = { minX: e.minX, maxX: e.maxX, minZ: e.minY, maxZ: e.maxY, maxY: H };
  return m;
}

export { isDoor, isStair };
