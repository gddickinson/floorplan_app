// Editor state shared by the editor modules: the plan, selection, tool, view transform, undo history, autosave.
import { clonePlan, fromDict, toDict } from './model.js';
import { extent } from './geometry.js';

export const MIN_SCALE = 0.5, MAX_SCALE = 10.0, DEFAULT_SCALE = 2.0;  // pixels per inch (AppConfig)
const SAVE_KEY = 'floorplan.autosave';

export function createState(plan) {
  const S = {
    plan, sel: null,              // sel: {kind: 'wall'|'opening'|'room'|'furniture'|'fixture'|'stair', id}
    tool: 'select', openingType: 'door_single', libItem: null,
    view: { s: DEFAULT_SCALE, ox: 0, oy: 0, w: 800, h: 600 },
    showGrid: true, showDims: true, showAreas: true, unit: 'ft',
    roomPick: [], temp: null, hover: null, measurements: [],
    undo: [], redo: [], listeners: [], dirty: false,
  };
  S.snapshot = () => JSON.stringify(toDict(S.plan));
  // Record the current plan for undo before a change.
  S.checkpoint = () => { S.undo.push(S.snapshot()); if (S.undo.length > 200) S.undo.shift(); S.redo = []; };
  S.emit = (what = 'plan') => {
    if (what === 'plan') { S.dirty = true; autosave(S); }
    for (const fn of S.listeners) fn(what);
  };
  S.on = fn => S.listeners.push(fn);
  S.restore = text => {
    S.plan = fromDict(JSON.parse(text));
    if (S.sel && !findSel(S)) S.sel = null;
    S.emit('plan');
  };
  S.doUndo = () => { if (!S.undo.length) return; S.redo.push(S.snapshot()); S.restore(S.undo.pop()); };
  S.doRedo = () => { if (!S.redo.length) return; S.undo.push(S.snapshot()); S.restore(S.redo.pop()); };
  S.load = (p, keepHistory = false) => {
    if (keepHistory) S.checkpoint(); else { S.undo = []; S.redo = []; }
    S.plan = p; S.sel = null; S.roomPick = []; S.temp = null; S.measurements = [];
    fitView(S); S.emit('plan'); S.dirty = false;
  };
  return S;
}

export const LIST = { wall: 'walls', opening: 'openings', room: 'rooms', furniture: 'furniture', fixture: 'fixtures',
  stair: 'stairs' };
export function findSel(S, sel = S.sel) {
  if (!sel) return null;
  return S.plan[LIST[sel.kind]].find(o => o.id === sel.id) || null;
}

// FloorPlanCanvas.fit_to_view: 1.2 x the extent, 90 % of the view, scale clamped to 0.5..10 px per inch.
export function fitView(S) {
  const e = extent(S.plan), v = S.view;
  const wIn = (e.maxX - e.minX) * 1.2, hIn = (e.maxY - e.minY) * 1.2;
  if (wIn > 0 && hIn > 0) v.s = Math.max(MIN_SCALE, Math.min(MAX_SCALE, Math.min(v.w * 0.9 / wIn, v.h * 0.9 / hIn)));
  else v.s = DEFAULT_SCALE;
  v.ox = v.w / 2 - (e.minX + e.maxX) / 2 * v.s;
  v.oy = v.h / 2 - (e.minY + e.maxY) / 2 * v.s;
}

export function zoomAt(S, factor, sx, sy) {
  const v = S.view, ns = Math.max(MIN_SCALE, Math.min(MAX_SCALE, v.s * factor));
  const wx = (sx - v.ox) / v.s, wy = (sy - v.oy) / v.s;
  v.s = ns; v.ox = sx - wx * ns; v.oy = sy - wy * ns;
}
export const toWorld = (S, sx, sy) => ({ x: (sx - S.view.ox) / S.view.s, y: (sy - S.view.oy) / S.view.s });

function autosave(S) {
  try { localStorage.setItem(SAVE_KEY, JSON.stringify(toDict(S.plan))); } catch (e) { /* private mode: ignore */ }
}
export function loadAutosave() {
  try { const t = localStorage.getItem(SAVE_KEY); return t ? fromDict(JSON.parse(t)) : null; } catch (e) { return null; }
}
export const copyPlan = clonePlan;
