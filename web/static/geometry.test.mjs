// node web/static/geometry.test.mjs: the JS model and geometry agree with the Python core on
// tests/fixtures/geometry_fixture.json (written by scripts/make_geometry_fixture.py).
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { fromDict, toDict, toFileText, defaultName, pyTitle } from './model.js';
import { findSnapPoint, roomPolygon, pointInPolygon, pointNearLine, openingPosition, bounds, footprint, containsPoint }
  from './geometry.js';
import { statistics, formatStatistics, roomArea, roomPerimeter } from './stats.js';
import { formatDimension, fmt1, pyRound } from './units.js';

const fx = JSON.parse(readFileSync(new URL('../../tests/fixtures/geometry_fixture.json', import.meta.url)));
let n = 0, maxDiff = 0;
function close(a, b, what) {
  if (typeof a === 'number' && typeof b === 'number') {
    const d = Math.abs(a - b);
    maxDiff = Math.max(maxDiff, d);
    assert.ok(d <= 1e-9 * Math.max(1, Math.abs(b)), `${what}: ${a} vs ${b}`);
  } else if (Array.isArray(b)) {
    assert.equal(a.length, b.length, `${what}: length`);
    b.forEach((v, i) => close(a[i], v, `${what}[${i}]`));
  } else if (b && typeof b === 'object') {
    assert.deepEqual(Object.keys(a), Object.keys(b), `${what}: keys`);
    for (const k of Object.keys(b)) close(a[k], b[k], `${what}.${k}`);
  } else assert.equal(a, b, what);
  n++;
}

for (const c of fx.cases) {
  const plan = fromDict(c.dict);
  close(toDict(plan), c.dict, `${c.name} round trip`);
  close(JSON.parse(toFileText(plan)), c.dict, `${c.name} file text`);
  for (const r of c.rooms) {
    const room = plan.rooms.find(x => x.id === r.id);
    close(roomPolygon(room, plan).map(p => [p.x, p.y]), r.polygon, `${c.name} ${r.id} polygon`);
    close(roomArea(room, plan), r.area_sqft, `${c.name} ${r.id} area`);
    close(roomPerimeter(room, plan), r.perimeter_ft, `${c.name} ${r.id} perimeter`);
  }
  const st = statistics(plan);
  close(st, c.stats, `${c.name} stats`);
  assert.equal(formatStatistics(st), c.stats_text, `${c.name} stats text`);
  const b = bounds(plan);
  close(b ? [b.minX, b.minY, b.maxX, b.maxY] : null, c.bounds, `${c.name} bounds`);
  c.probes.forEach(([x, y], i) => {
    const p = { x, y };
    const s = findSnapPoint(p, plan.walls);
    close([s.x, s.y], c.snap[i], `${c.name} snap ${x},${y}`);
    close(plan.rooms.filter(r => pointInPolygon(p, roomPolygon(r, plan))).map(r => r.id), c.inside[i], `${c.name} inside ${x},${y}`);
    close(plan.walls.filter(w => pointNearLine(p, w.start, w.end, 10)).map(w => w.id), c.near_walls[i], `${c.name} near ${x},${y}`);
  });
  for (const [wid, ts] of Object.entries(c.opening_position)) {
    const w = plan.walls.find(x => x.id === wid);
    close(c.probes.slice(0, 12).map(([x, y]) => openingPosition(w, { x, y })), ts, `${c.name} opening ${wid}`);
  }
}
for (const [v, u, text] of fx.format_dimension) { assert.equal(formatDimension(v, u), text, `format_dimension(${v}, ${u})`); n++; }

// Python behaviours checked by hand
assert.equal(pyRound(0.5), 0); assert.equal(pyRound(1.5), 2); assert.equal(pyRound(-2.5), -2); assert.equal(pyRound(2.6), 3);
assert.equal(fmt1(126.25), '126.2'); assert.equal(fmt1(126.75), '126.8'); assert.equal(fmt1(-0.0), '-0.0');
assert.equal(pyTitle('tv stand'), 'Tv Stand'); assert.equal(defaultName('sink_kitchen'), 'Sink Kitchen');
assert.throws(() => fromDict({ walls: [{ start: { x: 0, y: 0 }, end: { x: 1, y: 0 }, thickness: 6, wall_type: 'bogus' }] }));
assert.throws(() => fromDict({ walls: [{ start: { x: 0, y: 0 }, end: { x: 1, y: 0 }, wall_type: 'interior' }] }));
// defaults filled as FloorPlan.from_dict
const d = toDict(fromDict({ furniture: [{ position: { x: 1, y: 2 }, width: 3, depth: 4, furniture_type: 'tv_stand' }] }));
assert.equal(d.name, 'Untitled Floor Plan'); assert.equal(d.furniture[0].name, 'Tv Stand'); assert.equal(d.furniture[0].rotation, 0);
assert.equal(d.ceiling_height, 96);
// footprints: a 90-degree sofa is 36 wide and 84 deep on screen; a stair runs from start to end
const sofa = { position: { x: 0, y: 0 }, width: 84, depth: 36, rotation: 90, furniture_type: 'sofa' };
assert.ok(containsPoint(sofa, { x: 0, y: 40 }) && !containsPoint(sofa, { x: 40, y: 0 }));
const stair = { start: { x: 0, y: 0 }, end: { x: 120, y: 0 }, width: 36, stair_type: 'straight', rotation: 0, num_steps: 12 };
assert.ok(containsPoint(stair, { x: 100, y: 10 }) && !containsPoint(stair, { x: 60, y: 30 }));
assert.equal(footprint(stair).length, 4);

console.log(`ok: ${fx.cases.length} plans, ${n} comparisons, max |js - py| = ${maxDiff.toExponential(2)}`);
