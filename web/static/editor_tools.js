// Pointer interaction on the 2D plan: select / move / resize / rotate, draw walls, place doors and windows,
// pick walls for a room, measure, place furniture, fixtures and stairs, pan and zoom. Snapping follows the desktop
// canvas: wall endpoints within 6 inches first, else the 1 ft grid (geometry.findSnapPoint).
import { containsPoint, dist, findSnapPoint, footprint, objCenter, openingCenter, openingPosition,
  pointNearLine, pointInPolygon, roomPolygon, wallAtPoint, wallLength, isStair } from './geometry.js';
import { makeFixture, makeFurniture, makeOpening, makeStair, makeWall, isDoor } from './model.js';
import { findSel, toWorld, zoomAt } from './editor_state.js';
import { HANDLE_PX, rotateHandle } from './editor_render.js';
import { formatDimension } from './units.js';

const OBJ_LISTS = [['stairs', 'stair'], ['fixtures', 'fixture'], ['furniture', 'furniture']];
const MIN_SIZE = 6.0;  // inches (SelectableObject minimum)

// What is under point p in select mode: objects first (top-most), then openings, walls, rooms.
export function hitTest(S, p) {
  const k = 1 / S.view.s, P = S.plan;
  for (const [list, kind] of OBJ_LISTS) {
    for (let i = P[list].length - 1; i >= 0; i--) if (containsPoint(P[list][i], p)) return { kind, id: P[list][i].id };
  }
  for (const o of P.openings) {
    const w = P.walls.find(x => x.id === o.wall_id);
    if (!w) continue;
    const c = openingCenter(w, o.position), L = wallLength(w);
    const a = { x: c.x - (w.end.x - w.start.x) / L * o.width / 2, y: c.y - (w.end.y - w.start.y) / L * o.width / 2 };
    const b = { x: 2 * c.x - a.x, y: 2 * c.y - a.y };
    if (pointNearLine(p, a, b, Math.max(10 * k, w.thickness / 2))) return { kind: 'opening', id: o.id };
  }
  for (const w of P.walls) if (pointNearLine(p, w.start, w.end, Math.max(10 * k, w.thickness / 2))) return { kind: 'wall', id: w.id };
  for (let i = P.rooms.length - 1; i >= 0; i--) {
    const poly = roomPolygon(P.rooms[i], P);
    if (poly.length > 2 && pointInPolygon(p, poly)) return { kind: 'room', id: P.rooms[i].id };
  }
  return null;
}

// Handle under p for the selected object/wall: 'rotate', corner index 0..3, 'start'/'end' (wall), or null.
function handleAt(S, p) {
  const obj = findSel(S), k = 1 / S.view.s, r = HANDLE_PX * k;
  if (!obj) return null;
  if (S.sel.kind === 'wall') {
    if (dist(p, obj.start) <= r) return 'start';
    if (dist(p, obj.end) <= r) return 'end';
    return null;
  }
  if (!['furniture', 'fixture', 'stair'].includes(S.sel.kind)) return null;
  const fp = footprint(obj);
  for (let i = 0; i < 4; i++) if (dist(p, fp[i]) <= r) return i;
  if (dist(p, rotateHandle(obj, k)) <= r) return 'rotate';
  return null;
}

export function attachTools(S, svg, ui) {
  let drag = null, spaceDown = false;
  const pt = e => { const b = svg.getBoundingClientRect(); return { sx: e.clientX - b.left, sy: e.clientY - b.top }; };
  const status = msg => ui.status(msg);
  const changed = () => S.emit('plan');
  const once = d => { if (!d.saved) { S.checkpoint(); d.saved = true; } };

  function click(p, raw, e) {
    const P = S.plan, k = 1 / S.view.s;
    switch (S.tool) {
      case 'wall':
        if (!S.temp || S.temp.kind !== 'wall') { S.temp = { kind: 'wall', start: p }; status('Click the wall end point (Esc or double-click to stop)'); return S.emit('view'); }
        if (dist(p, S.temp.start) > 1.0) {
          S.checkpoint();
          const w = makeWall(S.temp.start, p, { thickness: ui.wallThickness(), wall_type: ui.wallType() });
          P.walls.push(w);
          status(`Wall added: ${formatDimension(wallLength(w), S.unit)}`);
          S.temp = { kind: 'wall', start: p };  // keep drawing from the end point
          return changed();
        }
        return;
      case 'opening': {
        const w = wallAtPoint(raw, P.walls, Math.max(10 * k, 3));
        if (!w) return status('Click on a wall to place the ' + (isDoor(S.openingType) ? 'door' : 'window'));
        S.checkpoint();
        const width = isDoor(S.openingType) || S.openingType === 'archway' ? 36.0 : 48.0;
        const o = makeOpening(w.id, openingPosition(w, raw), width, S.openingType);
        P.openings.push(o);
        S.sel = { kind: 'opening', id: o.id };
        status(`${S.openingType.replace(/_/g, ' ')} added to wall`);
        return changed();
      }
      case 'room': {
        const w = wallAtPoint(raw, P.walls, Math.max(10 * k, 3));
        if (!w) return;
        const i = S.roomPick.indexOf(w.id);
        if (i >= 0) S.roomPick.splice(i, 1); else S.roomPick.push(w.id);
        status(`${S.roomPick.length} wall(s) selected: press Enter or "Create room" (needs at least 3)`);
        return S.emit('pick');
      }
      case 'measure':
        if (!S.temp || S.temp.kind !== 'measure') { S.temp = { kind: 'measure', start: p }; status('Click to finish the measurement'); return S.emit('view'); }
        S.measurements.push({ start: S.temp.start, end: p });
        status(`Measured: ${formatDimension(dist(S.temp.start, p), S.unit)}`);
        S.temp = null;
        return S.emit('view');
      case 'place': {
        const it = S.libItem;
        if (!it) return;
        if (it.kind === 'stair') {
          if (!S.temp || S.temp.kind !== 'stair') { S.temp = { kind: 'stair', start: p }; status('Click to set the stair end point'); return S.emit('view'); }
          if (dist(p, S.temp.start) < 1) return;
          S.checkpoint();
          const s = makeStair(S.temp.start, p, it.width, it.type);
          P.stairs.push(s); S.temp = null; S.sel = { kind: 'stair', id: s.id };
          status(`Placed ${it.type.replace(/_/g, ' ')} stair`);
          return changed();
        }
        S.checkpoint();
        const o = it.kind === 'furniture' ? makeFurniture(p, it.width, it.depth, it.type) : makeFixture(p, it.width, it.depth, it.type);
        P[it.kind === 'furniture' ? 'furniture' : 'fixtures'].push(o);
        S.sel = { kind: it.kind, id: o.id };
        status(`Placed ${o.name}`);
        return changed();
      }
      default: break;
    }
  }

  function startSelect(raw) {
    const h = S.sel && handleAt(S, raw);
    const obj = findSel(S);
    if (h !== null && h !== undefined && obj) {
      if (h === 'start' || h === 'end') {
        const at = { ...obj[h] };
        // move every wall endpoint joined at this point (wall joins stay closed)
        const joined = [];
        for (const w of S.plan.walls) for (const e of ['start', 'end']) if (dist(w[e], at) < 1e-6) joined.push([w, e]);
        drag = { mode: 'wall-end', joined, moved: new Set(joined.map(j => j[0].id)) };
      } else {
        drag = { mode: h === 'rotate' ? 'rotate' : 'resize', corner: h, obj, start: raw,
          orig: JSON.parse(JSON.stringify(obj)) };
      }
      return;
    }
    S.sel = hitTest(S, raw);
    S.emit('select');
    const o = findSel(S);
    if (!o) return;
    if (S.sel.kind === 'wall') drag = { mode: 'move-wall', obj: o, start: raw, orig: JSON.parse(JSON.stringify(o)) };
    else if (S.sel.kind === 'opening') drag = { mode: 'slide', obj: o };
    else if (S.sel.kind !== 'room') drag = { mode: 'move', obj: o, start: raw, orig: JSON.parse(JSON.stringify(o)) };
  }

  function dragTo(raw, e) {
    const d = drag, o = d.obj;
    once(d);
    if (d.mode === 'move') {
      const dx = raw.x - d.start.x, dy = raw.y - d.start.y;
      if (isStair(o)) { o.start = { x: d.orig.start.x + dx, y: d.orig.start.y + dy }; o.end = { x: d.orig.end.x + dx, y: d.orig.end.y + dy }; }
      else o.position = { x: d.orig.position.x + dx, y: d.orig.position.y + dy };
    } else if (d.mode === 'move-wall') {
      const dx = raw.x - d.start.x, dy = raw.y - d.start.y;
      const s = findSnapPoint({ x: d.orig.start.x + dx, y: d.orig.start.y + dy }, S.plan.walls.filter(w => w !== o));
      o.start = s; o.end = { x: s.x + d.orig.end.x - d.orig.start.x, y: s.y + d.orig.end.y - d.orig.start.y };
    } else if (d.mode === 'wall-end') {
      const p = findSnapPoint(raw, S.plan.walls.filter(w => !d.moved.has(w.id)));
      for (const [w, end] of d.joined) w[end] = { x: p.x, y: p.y };
      status(`Wall end at ${formatDimension(p.x, S.unit)}, ${formatDimension(p.y, S.unit)}`);
    } else if (d.mode === 'slide') {
      const w = S.plan.walls.find(x => x.id === o.wall_id);
      if (w) o.position = openingPosition(w, raw);
    } else if (d.mode === 'rotate') {
      const c = objCenter(o);
      let a = Math.atan2(raw.y - c.y, raw.x - c.x) * 180 / Math.PI + 90;
      if (!e.shiftKey) a = Math.round(a / 15) * 15;  // 15-degree steps unless Shift is held
      a = ((a % 360) + 360) % 360;
      if (isStair(o)) {
        const L = dist(o.start, o.end) / 2, r = (a - 90) * Math.PI / 180;
        o.start = { x: c.x + Math.cos(r) * L, y: c.y + Math.sin(r) * L }; o.end = { x: c.x - Math.cos(r) * L, y: c.y - Math.sin(r) * L };
      } else o.rotation = a;
    } else if (d.mode === 'resize') resize(d, raw);
    S.emit('plan');
  }

  // Corner handle: the dragged corner follows the cursor, the opposite corner stays fixed (6 inch minimum).
  function resize(d, raw) {
    const o = d.obj, orig = d.orig, stair = isStair(o);
    const ang = stair ? Math.atan2(orig.end.y - orig.start.y, orig.end.x - orig.start.x) - Math.PI / 2 : orig.rotation * Math.PI / 180;
    const cs = Math.cos(ang), sn = Math.sin(ang);
    const dx = raw.x - d.start.x, dy = raw.y - d.start.y;
    const lx = dx * cs + dy * sn, ly = -dx * sn + dy * cs;
    const sx = d.corner === 0 || d.corner === 3 ? -1 : 1, sy = d.corner === 0 || d.corner === 1 ? -1 : 1;
    const ow = orig.width, od = stair ? dist(orig.start, orig.end) : orig.depth;
    const nw = Math.max(MIN_SIZE, ow + sx * lx), nd = Math.max(MIN_SIZE, od + sy * ly);
    const ox = sx * (nw - ow) / 2, oy = sy * (nd - od) / 2;
    const c0 = stair ? { x: (orig.start.x + orig.end.x) / 2, y: (orig.start.y + orig.end.y) / 2 } : orig.position;
    const c = { x: c0.x + ox * cs - oy * sn, y: c0.y + ox * sn + oy * cs };
    o.width = nw;
    if (stair) {
      const ux = (orig.end.x - orig.start.x) / od, uy = (orig.end.y - orig.start.y) / od;
      o.start = { x: c.x - ux * nd / 2, y: c.y - uy * nd / 2 }; o.end = { x: c.x + ux * nd / 2, y: c.y + uy * nd / 2 };
    } else { o.depth = nd; o.position = c; }
  }

  svg.addEventListener('pointerdown', e => {
    svg.focus({ preventScroll: true });
    const { sx, sy } = pt(e), raw = toWorld(S, sx, sy);
    if (e.button === 1 || e.button === 2 || S.tool === 'pan' || spaceDown) {
      drag = { mode: 'pan', sx, sy, ox: S.view.ox, oy: S.view.oy };
    } else if (e.button === 0) {
      if (S.tool === 'select') startSelect(raw);
      else click(findSnapPoint(raw, S.plan.walls), raw, e);
    }
    if (drag) svg.setPointerCapture(e.pointerId);
    e.preventDefault();
  });
  svg.addEventListener('pointermove', e => {
    const { sx, sy } = pt(e), raw = toWorld(S, sx, sy);
    if (drag && drag.mode === 'pan') {
      S.view.ox = drag.ox + sx - drag.sx; S.view.oy = drag.oy + sy - drag.sy;
      return S.emit('view');
    }
    if (drag) return dragTo(raw, e);
    S.hover = S.tool === 'select' ? null : findSnapPoint(raw, S.plan.walls);
    const h = S.hover || raw;
    ui.cursor(`${formatDimension(h.x, S.unit)} x ${formatDimension(h.y, S.unit)}`);
    if (S.tool !== 'select') S.emit('view');
  });
  const end = e => {
    if (drag && drag.saved && drag.mode !== 'pan') S.emit('commit');
    drag = null;
    try { svg.releasePointerCapture(e.pointerId); } catch (_) { /* not captured */ }
  };
  svg.addEventListener('pointerup', end);
  svg.addEventListener('pointercancel', end);
  svg.addEventListener('pointerleave', () => { if (!drag && S.hover) { S.hover = null; S.emit('view'); } });
  svg.addEventListener('dblclick', () => { if (S.temp) { S.temp = null; status('Stopped'); S.emit('view'); } });
  svg.addEventListener('contextmenu', e => { e.preventDefault(); if (S.temp) { S.temp = null; S.emit('view'); } });
  svg.addEventListener('wheel', e => {
    e.preventDefault();
    const { sx, sy } = pt(e);
    zoomAt(S, e.deltaY < 0 ? 1.1 : 1 / 1.1, sx, sy);
    ui.status(`Zoom: ${Math.round(S.view.s / 2 * 100)}%`);
    S.emit('view');
  }, { passive: false });
  svg.addEventListener('keydown', e => { if (e.code === 'Space') { spaceDown = true; e.preventDefault(); } });
  svg.addEventListener('keyup', e => { if (e.code === 'Space') spaceDown = false; });
}
