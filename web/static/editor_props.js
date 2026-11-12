// Properties panel (selected wall / opening / room / object, or the plan itself) and the Statistics panel.
// Numeric fields are inches, as in the desktop properties panel; labels show the feet-inches form.
import { esc } from './core.js';
import { ENUMS, isWindow, defaultName, removeWall } from './model.js';
import { roomPolygon, wallLength, dist } from './geometry.js';
import { roomArea, roomPerimeter, statistics, formatStatistics } from './stats.js';
import { formatDimension, fmt1 } from './units.js';
import { findSel, LIST } from './editor_state.js';

const title = s => s.replace(/_/g, ' ');
const opts = (list, v) => list.map(x => `<option value="${x}"${x === v ? ' selected' : ''}>${esc(title(x))}</option>`).join('');
let uid = 0;
function field(label, key, value, type = 'number', extra = '') {
  const id = `pf-${++uid}`;
  return `<label for="${id}">${esc(label)}</label><input id="${id}" data-k="${key}" type="${type}" value="${esc(value)}" ${type === 'number' ? 'step="any"' : ''} ${extra}>`;
}
function select(label, key, list, value) {
  const id = `pf-${++uid}`;
  return `<label for="${id}">${esc(label)}</label><select id="${id}" data-k="${key}">${opts(list, value)}</select>`;
}
const pair = (a, b) => `<div class="pair"><div>${a}</div><div>${b}</div></div>`;
const info = (k, v) => `<div class="kv"><span>${esc(k)}</span><b>${esc(v)}</b></div>`;

function formFor(S, sel, o) {
  const u = S.unit;
  switch (sel.kind) {
    case 'wall': return `<h3>Wall</h3>${info('Length', formatDimension(wallLength(o), u))}
      ${pair(field('Start x (in)', 'start.x', o.start.x), field('Start y (in)', 'start.y', o.start.y))}
      ${pair(field('End x (in)', 'end.x', o.end.x), field('End y (in)', 'end.y', o.end.y))}
      ${pair(field('Thickness (in)', 'thickness', o.thickness, 'number', 'min="0.5"'), field('Height (in)', 'height', o.height, 'number', 'min="1"'))}
      ${select('Type', 'wall_type', ENUMS.wall_type, o.wall_type)}${select('Style', 'wall_style', ENUMS.wall_style, o.wall_style)}`;
    case 'opening': return `<h3>Opening</h3>${select('Type', 'opening_type', ENUMS.opening_type, o.opening_type)}
      ${pair(field('Width (in)', 'width', o.width, 'number', 'min="1"'), field('Height (in)', 'height', o.height, 'number', 'min="1"'))}
      ${pair(field('Position (0-1)', 'position', o.position, 'number', 'min="0" max="1" step="0.01"'),
        isWindow(o.opening_type) ? field('Sill height (in)', 'sill_height', o.sill_height, 'number', 'min="0"') : '')}`;
    case 'room': {
      const a = roomArea(o, S.plan), per = roomPerimeter(o, S.plan);
      return `<h3>Room</h3>${field('Name', 'name', o.name, 'text')}${field('Colour', 'color', o.color || '#f0f0f0', 'color')}
      ${info('Area', a ? `${fmt1(a)} sq ft` : '–')}${info('Perimeter', `${fmt1(per)} ft`)}${info('Walls', o.wall_ids.length)}
      ${info('Outline corners', roomPolygon(o, S.plan).length)}`;
    }
    case 'stair': return `<h3>Stair</h3>${select('Type', 'stair_type', ENUMS.stair_type, o.stair_type)}
      ${info('Length', formatDimension(dist(o.start, o.end), u))}
      ${pair(field('Width (in)', 'width', o.width, 'number', 'min="6"'), field('Steps', 'num_steps', o.num_steps, 'number', 'min="1" step="1"'))}
      ${pair(field('Start x (in)', 'start.x', o.start.x), field('Start y (in)', 'start.y', o.start.y))}
      ${pair(field('End x (in)', 'end.x', o.end.x), field('End y (in)', 'end.y', o.end.y))}`;
    default: {
      const tk = sel.kind === 'furniture' ? 'furniture_type' : 'fixture_type';
      return `<h3>${sel.kind === 'furniture' ? 'Furniture' : 'Fixture'}</h3>${field('Name', 'name', o.name, 'text')}
      ${select('Type', tk, ENUMS[tk], o[tk])}
      ${pair(field('Centre x (in)', 'position.x', o.position.x), field('Centre y (in)', 'position.y', o.position.y))}
      ${pair(field('Width (in)', 'width', o.width, 'number', 'min="6"'), field('Depth (in)', 'depth', o.depth, 'number', 'min="6"'))}
      ${field('Rotation (degrees)', 'rotation', o.rotation, 'number', 'step="15"')}`;
    }
  }
}

function planForm(S) {
  const p = S.plan;
  return `<h3>Plan</h3>${field('Name', 'name', p.name, 'text')}
    ${pair(field('Ceiling height (in)', 'ceiling_height', p.ceiling_height, 'number', 'min="1"'), field('Floor level', 'floor_level', p.floor_level, 'number', 'step="1"'))}
    ${field('Elevation (in)', 'elevation', p.elevation)}
    <p class="small mute">Select something on the plan to edit it. ${p.walls.length} walls, ${p.openings.length} openings,
    ${p.rooms.length} rooms, ${p.furniture.length + p.fixtures.length + p.stairs.length} objects.</p>`;
}

function setPath(o, key, v) {
  const parts = key.split('.');
  if (parts.length === 2) o[parts[0]] = { ...o[parts[0]], [parts[1]]: v }; else o[key] = v;
}

export function renderProps(S, host) {
  const sel = S.sel, o = findSel(S);
  host.innerHTML = (o ? formFor(S, sel, o) + `<div class="bar"><button class="alt danger" id="p-del">Delete</button></div>` : planForm(S));
  host.querySelectorAll('[data-k]').forEach(inp => inp.addEventListener('change', () => {
    const target = o || S.plan, key = inp.dataset.k;
    let v = inp.type === 'number' ? parseFloat(inp.value) : inp.value;
    if (inp.type === 'number' && !Number.isFinite(v)) { inp.value = key.split('.').reduce((a, k) => a[k], target); return; }
    if (inp.min !== '' && inp.type === 'number') v = Math.max(+inp.min, v);
    if (inp.max !== '' && inp.type === 'number') v = Math.min(+inp.max, v);
    if (key === 'num_steps' || key === 'floor_level') v = Math.round(v);
    S.checkpoint();
    if (key === 'furniture_type' || key === 'fixture_type') {
      if (target.name === defaultName(target[key])) target.name = defaultName(v);  // keep default names in step
    }
    setPath(target, key, v);
    S.emit('plan');
  }));
  const del = host.querySelector('#p-del');
  if (del) del.addEventListener('click', () => deleteSelected(S));
}

export function deleteSelected(S) {
  if (!S.sel || !findSel(S)) return;
  S.checkpoint();
  const { kind, id } = S.sel;
  if (kind === 'wall') removeWall(S.plan, id);
  else S.plan[LIST[kind]] = S.plan[LIST[kind]].filter(x => x.id !== id);
  S.sel = null;
  S.emit('plan');
}

export function renderStats(S, host) {
  host.textContent = formatStatistics(statistics(S.plan));
}
