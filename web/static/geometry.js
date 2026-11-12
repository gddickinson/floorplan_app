// Plan geometry: JS port of core/snapping.py and core/room_geometry.py (held to the Python results by
// geometry.test.mjs and tests/fixtures/geometry_fixture.json), plus footprints of furniture/fixtures/stairs.
// Points are {x, y} in inches, y down.
import { pyRound } from './units.js';

export const GRID_SIZE = 12.0, SNAP_TOLERANCE = 6.0, OPENING_MIN_T = 0.1, OPENING_MAX_T = 0.9, JOIN_TOLERANCE = 1.0;

export const dist = (a, b) => ((a.x - b.x) ** 2 + (a.y - b.y) ** 2) ** 0.5;
export const wallLength = w => dist(w.start, w.end);
export const midpoint = w => ({ x: (w.start.x + w.end.x) / 2, y: (w.start.y + w.end.y) / 2 });

// ---- snapping (core/snapping.py) -------------------------------------------------------------------------------
export const snapToGrid = (p, g = GRID_SIZE) => ({ x: pyRound(p.x / g) * g, y: pyRound(p.y / g) * g });

export function findSnapPoint(p, walls, g = GRID_SIZE, tol = SNAP_TOLERANCE) {
  for (const w of walls) for (const e of [w.start, w.end]) if (dist(p, e) < tol) return { x: e.x, y: e.y };
  return snapToGrid(p, g);
}

export function pointNearLine(p, a, b, tol) {
  const dx = b.x - a.x, dy = b.y - a.y, len = (dx * dx + dy * dy) ** 0.5;
  if (len < 0.1) return dist(p, a) < tol;
  let t = ((p.x - a.x) * dx + (p.y - a.y) * dy) / (len ** 2);
  t = Math.max(0, Math.min(1, t));
  return dist(p, { x: a.x + t * dx, y: a.y + t * dy }) < tol;
}
export const wallAtPoint = (p, walls, tol) => walls.find(w => pointNearLine(p, w.start, w.end, tol)) || null;

export function openingPosition(w, p) {
  const dx = w.end.x - w.start.x, dy = w.end.y - w.start.y;
  const t = ((p.x - w.start.x) * dx + (p.y - w.start.y) * dy) / (wallLength(w) ** 2);
  return Math.max(OPENING_MIN_T, Math.min(OPENING_MAX_T, t));
}
export const openingCenter = (w, t) => ({ x: w.start.x + (w.end.x - w.start.x) * t, y: w.start.y + (w.end.y - w.start.y) * t });

// ---- room outline (core/room_geometry.py) ------------------------------------------------------------------------
export function pointSegmentDistance(p, a, b) {
  const dx = b.x - a.x, dy = b.y - a.y, l2 = dx * dx + dy * dy;
  if (l2 < 1e-12) return dist(p, a);
  const t = Math.max(0, Math.min(1, ((p.x - a.x) * dx + (p.y - a.y) * dy) / l2));
  return Math.hypot(p.x - (a.x + t * dx), p.y - (a.y + t * dy));
}

export function lineIntersection(w1, w2) {
  const [x1, y1, x2, y2] = [w1.start.x, w1.start.y, w1.end.x, w1.end.y];
  const [x3, y3, x4, y4] = [w2.start.x, w2.start.y, w2.end.x, w2.end.y];
  const den = (x1 - x2) * (y3 - y4) - (y1 - y2) * (x3 - x4);
  const l1 = Math.hypot(x2 - x1, y2 - y1), l2 = Math.hypot(x4 - x3, y4 - y3);
  if (l1 < 1e-9 || l2 < 1e-9 || Math.abs(den) < 1e-9 * l1 * l2) return null;
  const a = x1 * y2 - y1 * x2, b = x3 * y4 - y3 * x4;
  return { x: (a * (x3 - x4) - (x1 - x2) * b) / den, y: (a * (y3 - y4) - (y1 - y2) * b) / den };
}

function legacyPolygon(walls) {
  const pts = [], seen = new Set();
  const r2 = v => Math.round(v * 100) / 100;
  for (const w of walls) for (const p of [w.start, w.end]) {
    const k = r2(p.x) + ',' + r2(p.y);
    if (!seen.has(k)) { seen.add(k); pts.push({ x: p.x, y: p.y }); }
  }
  return pts;
}

function segmentIntersection(w1, w2) {
  const p = lineIntersection(w1, w2);
  if (!p) return null;
  if (pointSegmentDistance(p, w1.start, w1.end) > 1e-6 || pointSegmentDistance(p, w2.start, w2.end) > 1e-6) return null;
  return p;
}

function contacts(w, others, tol) {
  const pts = [];
  for (const o of others) {
    for (const e of [o.start, o.end]) if (pointSegmentDistance(e, w.start, w.end) <= tol) pts.push(e);
    for (const e of [w.start, w.end]) if (pointSegmentDistance(e, o.start, o.end) <= tol) pts.push(e);
    const x = segmentIntersection(w, o);
    if (x) pts.push(x);
  }
  return pts;
}

function nextTip(w, junction, targets, tol) {
  let best = null, bestD = 0;
  for (const p of contacts(w, targets, tol)) {
    const d = dist(p, junction);
    if (d > tol && (best === null || d < bestD)) { best = p; bestD = d; }
  }
  if (best) return best;
  return dist(w.start, junction) >= dist(w.end, junction) ? w.start : w.end;
}

function chain(walls, tol) {
  const touches = (p, w) => pointSegmentDistance(p, w.start, w.end) <= tol;
  const first = walls[0], rest = walls.slice(1);
  const start = rest.some(w => touches(first.end, w)) ? first.start : first.end;
  let tip = nextTip(first, start, rest, tol), current = first;
  const order = [], remaining = rest.slice();
  while (remaining.length) {
    const cands = remaining.filter(w => touches(tip, w));
    if (!cands.length) return null;
    const key = w => Math.min(dist(tip, w.start), dist(tip, w.end));
    let nxt = cands[0];
    for (const c of cands) if (key(c) < key(nxt)) nxt = c;
    order.push([current, tip]);
    remaining.splice(remaining.indexOf(nxt), 1);
    tip = nextTip(nxt, tip, remaining.length ? remaining : [first], tol);
    current = nxt;
  }
  if (!touches(tip, first)) return null;
  order.push([current, tip]);
  return order;
}

const wallsById = plan => new Map(plan.walls.map(w => [w.id, w]));

// core.room_geometry.room_outline: {pts, closed}; pts = outline vertices (wall centre lines) in walking order.
export function roomOutline(room, plan, tol = JOIN_TOLERANCE, byId = wallsById(plan)) {
  const walls = room.wall_ids.map(i => byId.get(i)).filter(Boolean);
  if (walls.length < 3) return { pts: legacyPolygon(walls), closed: false };
  const order = chain(walls, tol);
  if (!order) return { pts: legacyPolygon(walls), closed: false };
  const pts = [], n = order.length;
  for (let i = 0; i < n; i++) {
    const [w, junction] = order[i], nxt = order[(i + 1) % n][0];
    let p = lineIntersection(w, nxt);
    if (!p || dist(p, junction) > Math.max(tol, 0.5 * w.thickness + nxt.thickness)) p = junction;
    if (!pts.length || dist(p, pts[pts.length - 1]) > 1e-9) pts.push({ x: p.x, y: p.y });
  }
  if (pts.length > 1 && dist(pts[0], pts[pts.length - 1]) <= 1e-9) pts.pop();
  return { pts: pts.slice(-1).concat(pts.slice(0, -1)), closed: true };
}
export const roomPolygon = (room, plan, tol, byId) => roomOutline(room, plan, tol, byId).pts;

export function polygonArea(pts) {
  const n = pts.length;
  if (n < 3) return 0;
  let s = 0;
  for (let i = 0; i < n; i++) { const j = (i + 1) % n; s += pts[i].x * pts[j].y - pts[j].x * pts[i].y; }
  return Math.abs(s) / 2;
}

export function pointInPolygon(p, pts) {
  let inside = false;
  for (let i = 0, j = pts.length - 1; i < pts.length; j = i++) {
    const a = pts[i], b = pts[j];
    if ((a.y > p.y) !== (b.y > p.y)) {
      const x = (b.x - a.x) * (p.y - a.y) / (b.y - a.y) + a.x;
      if (p.x < x) inside = !inside;
    }
  }
  return inside;
}

export function labelPoint(pts) {
  if (!pts.length) return null;
  return { x: pts.reduce((s, p) => s + p.x, 0) / pts.length, y: pts.reduce((s, p) => s + p.y, 0) / pts.length };
}

// FloorPlan.get_bounds(): wall endpoints only, or null.
export function bounds(plan) {
  if (!plan.walls.length) return null;
  const xs = plan.walls.flatMap(w => [w.start.x, w.end.x]), ys = plan.walls.flatMap(w => [w.start.y, w.end.y]);
  return { minX: Math.min(...xs), minY: Math.min(...ys), maxX: Math.max(...xs), maxY: Math.max(...ys) };
}

// Everything drawn (walls, objects) for fitting the view; falls back to a 20 ft square at the origin.
export function extent(plan) {
  const pts = plan.walls.flatMap(w => [w.start, w.end]);
  for (const o of [...plan.furniture, ...plan.fixtures, ...plan.stairs]) pts.push(...footprint(o));
  if (!pts.length) return { minX: 0, minY: 0, maxX: 240, maxY: 240 };
  return { minX: Math.min(...pts.map(p => p.x)), minY: Math.min(...pts.map(p => p.y)),
    maxX: Math.max(...pts.map(p => p.x)), maxY: Math.max(...pts.map(p => p.y)) };
}

// ---- objects (gui/object_selection.py SelectableObject) ----------------------------------------------------------
export const isStair = o => 'stair_type' in o;
export function objCenter(o) {
  return isStair(o) ? { x: (o.start.x + o.end.x) / 2, y: (o.start.y + o.end.y) / 2 } : o.position;
}
export const objDepth = o => (isStair(o) ? dist(o.start, o.end) : o.depth);

// Corners of the rotated rectangle (rotation in degrees, clockwise on screen as Qt's painter.rotate).
// Stairs: width across the run, length from start to end, oriented along start -> end.
export function footprint(o) {
  const c = objCenter(o), hw = o.width / 2, hd = objDepth(o) / 2;
  let ang;
  if (isStair(o)) ang = Math.atan2(o.end.y - o.start.y, o.end.x - o.start.x) - Math.PI / 2;
  else ang = o.rotation * Math.PI / 180;
  const cs = Math.cos(ang), sn = Math.sin(ang);
  return [[-hw, -hd], [hw, -hd], [hw, hd], [-hw, hd]].map(([x, y]) => ({ x: c.x + x * cs - y * sn, y: c.y + x * sn + y * cs }));
}
export const containsPoint = (o, p) => pointInPolygon(p, footprint(o));
