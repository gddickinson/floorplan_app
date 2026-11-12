// The floor plan model: a JS port of core/geometry.py's FloorPlan JSON format (the desktop .floorplan file).
// Plans are plain objects with the exact keys of FloorPlan.to_dict(); fromDict fills the same defaults as the
// Python from_dict and rejects what Python would reject (missing required keys, unknown enum values), and toDict
// writes keys in the Python order, so files move between the desktop app and the web editor unchanged.
// Units: inches (lengths), degrees (rotation); y grows downwards as on screen.

export const ENUMS = {
  wall_type: ['exterior', 'interior', 'load_bearing', 'partition', 'curtain', 'glass', 'retaining'],
  wall_style: ['solid', 'brick', 'concrete', 'glass', 'curtain', 'wood_frame', 'metal_stud', 'stone'],
  opening_type: ['door', 'window', 'archway', 'door_single', 'door_double', 'door_french', 'door_sliding',
    'door_pocket', 'door_bifold', 'door_dutch', 'door_garage', 'window_single', 'window_double', 'window_bay',
    'window_bow', 'window_casement', 'window_awning', 'window_slider', 'window_picture', 'window_skylight'],
  furniture_type: ['bed_single', 'bed_double', 'bed_queen', 'bed_king', 'sofa', 'loveseat', 'chair', 'armchair',
    'table_dining', 'table_coffee', 'table_side', 'desk', 'dresser', 'nightstand', 'bookshelf', 'cabinet',
    'wardrobe', 'tv_stand'],
  fixture_type: ['toilet', 'sink', 'sink_double', 'bathtub', 'shower', 'shower_corner', 'vanity', 'refrigerator',
    'stove', 'oven', 'dishwasher', 'microwave', 'sink_kitchen', 'washer', 'dryer', 'water_heater', 'furnace',
    'ac_unit'],
  stair_type: ['straight', 'l_shaped', 'u_shaped', 'winder', 'spiral', 'curved'],
};

export const isDoor = t => t === 'door' || t.startsWith('door_');        // OpeningType.is_door
export const isWindow = t => t === 'window' || t.startsWith('window_');  // OpeningType.is_window

// Python str.title(): upper-case a letter that follows a non-letter, lower-case the rest.
export function pyTitle(s) {
  return s.toLowerCase().replace(/(^|[^a-z])([a-z])/g, (m, a, b) => a + b.toUpperCase());
}
export const defaultName = type => pyTitle(type.replace(/_/g, ' '));

export function newId() {
  if (globalThis.crypto?.randomUUID) return crypto.randomUUID();
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, c => {
    const r = Math.random() * 16 | 0; return (c === 'x' ? r : (r & 3) | 8).toString(16);
  });
}

function need(d, key, what) {
  if (d == null || typeof d !== 'object' || !(key in d)) throw new Error(`${what}: missing "${key}"`);
  return d[key];
}
function num(v, what) {
  if (typeof v !== 'number' || !Number.isFinite(v)) throw new Error(`${what}: not a number (${JSON.stringify(v)})`);
  return v;
}
function enumv(kind, v) {
  if (!ENUMS[kind].includes(v)) throw new Error(`'${v}' is not a valid ${kind}`);
  return v;
}
const get = (d, k, dflt) => (d && k in d ? d[k] : dflt);
const pt = (d, what) => ({ x: num(need(d, 'x', what), what), y: num(need(d, 'y', what), what) });
const id = d => get(d, 'id', null) ?? newId();

export const wallFromDict = d => ({
  id: id(d), start: pt(need(d, 'start', 'wall'), 'wall start'), end: pt(need(d, 'end', 'wall'), 'wall end'),
  thickness: num(need(d, 'thickness', 'wall'), 'wall thickness'), wall_type: enumv('wall_type', need(d, 'wall_type', 'wall')),
  wall_style: enumv('wall_style', get(d, 'wall_style', 'solid')), height: num(get(d, 'height', 96.0), 'wall height'),
});
export const openingFromDict = d => ({
  id: id(d), wall_id: need(d, 'wall_id', 'opening'), position: num(need(d, 'position', 'opening'), 'position'),
  width: num(need(d, 'width', 'opening'), 'opening width'),
  opening_type: enumv('opening_type', need(d, 'opening_type', 'opening')),
  height: num(get(d, 'height', 80.0), 'opening height'), sill_height: num(get(d, 'sill_height', 36.0), 'sill height'),
});
export const roomFromDict = d => ({
  id: id(d), name: need(d, 'name', 'room'), wall_ids: [...get(d, 'wall_ids', [])], color: get(d, 'color', null),
});
function itemFromDict(d, kind) {
  const type = enumv(kind, need(d, kind, kind));
  return { id: id(d), position: pt(need(d, 'position', kind), kind), width: num(need(d, 'width', kind), kind),
    depth: num(need(d, 'depth', kind), kind), [kind]: type, rotation: num(get(d, 'rotation', 0.0), kind),
    name: get(d, 'name', null) ?? defaultName(type) };
}
export const furnitureFromDict = d => itemFromDict(d, 'furniture_type');
export const fixtureFromDict = d => itemFromDict(d, 'fixture_type');
export const stairFromDict = d => ({
  id: id(d), start: pt(need(d, 'start', 'stair'), 'stair start'), end: pt(need(d, 'end', 'stair'), 'stair end'),
  width: num(need(d, 'width', 'stair'), 'stair width'), stair_type: enumv('stair_type', get(d, 'stair_type', 'straight')),
  num_steps: num(get(d, 'num_steps', 12), 'num_steps'), rotation: num(get(d, 'rotation', 0.0), 'stair rotation'),
});

export function fromDict(d) {
  if (d == null || typeof d !== 'object' || Array.isArray(d)) throw new Error('not a floor plan (expected a JSON object)');
  if ('floors' in d && !('walls' in d)) throw new Error('this is a multi-floor Building file; open one floor plan');
  return {
    name: get(d, 'name', 'Untitled Floor Plan'), scale: get(d, 'scale', 1.0), floor_level: get(d, 'floor_level', 0),
    elevation: get(d, 'elevation', 0.0), ceiling_height: get(d, 'ceiling_height', 96.0),
    walls: get(d, 'walls', []).map(wallFromDict), openings: get(d, 'openings', []).map(openingFromDict),
    rooms: get(d, 'rooms', []).map(roomFromDict), furniture: get(d, 'furniture', []).map(furnitureFromDict),
    stairs: get(d, 'stairs', []).map(stairFromDict), fixtures: get(d, 'fixtures', []).map(fixtureFromDict),
    metadata: get(d, 'metadata', {}),
  };
}

const P = p => ({ x: p.x, y: p.y });
const item = (o, kind) => ({ id: o.id, position: P(o.position), width: o.width, depth: o.depth, [kind]: o[kind],
  rotation: o.rotation, name: o.name });

// FloorPlan.to_dict(), key for key.
export function toDict(p) {
  return {
    name: p.name, scale: p.scale, floor_level: p.floor_level, elevation: p.elevation, ceiling_height: p.ceiling_height,
    walls: p.walls.map(w => ({ id: w.id, start: P(w.start), end: P(w.end), thickness: w.thickness,
      wall_type: w.wall_type, wall_style: w.wall_style, height: w.height })),
    openings: p.openings.map(o => ({ id: o.id, wall_id: o.wall_id, position: o.position, width: o.width,
      opening_type: o.opening_type, height: o.height, sill_height: o.sill_height })),
    rooms: p.rooms.map(r => ({ id: r.id, name: r.name, wall_ids: [...r.wall_ids], color: r.color })),
    furniture: p.furniture.map(f => item(f, 'furniture_type')),
    stairs: p.stairs.map(s => ({ id: s.id, start: P(s.start), end: P(s.end), width: s.width, stair_type: s.stair_type,
      num_steps: s.num_steps, rotation: s.rotation })),
    fixtures: p.fixtures.map(f => item(f, 'fixture_type')),
    metadata: p.metadata,
  };
}

// The .floorplan file text, as FloorPlan.save_to_file writes it (json.dump indent=2).
export const toFileText = p => JSON.stringify(toDict(p), null, 2);
export const emptyPlan = (name = 'Untitled Floor Plan') => fromDict({ name });
export const clonePlan = p => fromDict(JSON.parse(JSON.stringify(toDict(p))));

// Constructors with the desktop defaults (Wall(), Opening(), ... in core/geometry.py).
export const makeWall = (start, end, o = {}) => wallFromDict({ start, end, thickness: 6.0, wall_type: 'interior', ...o });
export const makeOpening = (wall_id, position, width, opening_type, o = {}) =>
  openingFromDict({ wall_id, position, width, opening_type, ...o });
export const makeFurniture = (position, width, depth, type, o = {}) =>
  furnitureFromDict({ position, width, depth, furniture_type: type, ...o });
export const makeFixture = (position, width, depth, type, o = {}) =>
  fixtureFromDict({ position, width, depth, fixture_type: type, ...o });
export const makeStair = (start, end, width, type, o = {}) => stairFromDict({ start, end, width, stair_type: type, ...o });

// Removing a wall also removes its openings (FloorPlan.remove_wall); rooms keep the dangling id as in Python.
export function removeWall(p, wallId) {
  p.walls = p.walls.filter(w => w.id !== wallId);
  p.openings = p.openings.filter(o => o.wall_id !== wallId);
}
