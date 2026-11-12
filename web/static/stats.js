// Floor plan statistics: JS port of core/plan_stats.py (the desktop Statistics dialog), same keys and text.
import { dist, polygonArea, roomOutline, wallLength } from './geometry.js';
import { isDoor, isWindow } from './model.js';
import { fmt1 } from './units.js';

const wallMap = plan => new Map(plan.walls.map(w => [w.id, w]));

// Area in sq ft, or null (no walls / fewer than 3 outline points), as calculate_room_area.
export function roomArea(room, plan, byId = wallMap(plan)) {
  if (!room.wall_ids.length) return null;
  const { pts } = roomOutline(room, plan, undefined, byId);
  if (pts.length < 3) return null;
  return polygonArea(pts) / 144.0;
}

// Perimeter in ft: outline length, or the sum of the listed walls if they do not close (calculate_perimeter).
export function roomPerimeter(room, plan, byId = wallMap(plan)) {
  const { pts, closed } = roomOutline(room, plan, undefined, byId);
  let total = 0;
  if (!closed) for (const id of room.wall_ids) { const w = byId.get(id); if (w) total += wallLength(w); }
  else for (let i = 0; i < pts.length; i++) total += dist(pts[i], pts[(i + 1) % pts.length]);
  return total / 12.0;
}

export function totalWallLength(plan, type = null) {
  let t = 0;
  for (const w of plan.walls) if (type === null || w.wall_type === type) t += wallLength(w);
  return t / 12.0;
}

export function totalArea(plan, byId = wallMap(plan)) {
  let t = 0;
  for (const r of plan.rooms) { const a = roomArea(r, plan, byId); if (a) t += a; }
  return t;
}

// get_floor_plan_statistics
export function statistics(plan) {
  const byId = wallMap(plan);
  const stats = {
    walls: { count: plan.walls.length, total_length_ft: totalWallLength(plan),
      exterior_length_ft: totalWallLength(plan, 'exterior'), interior_length_ft: totalWallLength(plan, 'interior') },
    openings: { count: plan.openings.length, doors: plan.openings.filter(o => isDoor(o.opening_type)).length,
      windows: plan.openings.filter(o => isWindow(o.opening_type)).length,
      archways: plan.openings.filter(o => o.opening_type === 'archway').length },
    rooms: { count: plan.rooms.length, total_area_sqft: totalArea(plan, byId), individual: {} },
  };
  for (const r of plan.rooms) {
    const a = roomArea(r, plan, byId);
    if (a) stats.rooms.individual[r.name] = { area_sqft: a, perimeter_ft: roomPerimeter(r, plan, byId) };
  }
  if (plan.walls.length) {
    const xs = plan.walls.flatMap(w => [w.start.x, w.end.x]), ys = plan.walls.flatMap(w => [w.start.y, w.end.y]);
    const width_ft = (Math.max(...xs) - Math.min(...xs)) / 12.0, height_ft = (Math.max(...ys) - Math.min(...ys)) / 12.0;
    stats.dimensions = { width_ft, height_ft, bounding_box_area_sqft: width_ft * height_ft };
  }
  return stats;
}

// format_statistics
export function formatStatistics(s) {
  const L = [];
  L.push('=== Walls ===', `Total: ${s.walls.count}`, `Total Length: ${fmt1(s.walls.total_length_ft)} ft`);
  if (s.walls.exterior_length_ft > 0) L.push(`  Exterior: ${fmt1(s.walls.exterior_length_ft)} ft`);
  if (s.walls.interior_length_ft > 0) L.push(`  Interior: ${fmt1(s.walls.interior_length_ft)} ft`);
  L.push('\n=== Openings ===', `Total: ${s.openings.count}`, `  Doors: ${s.openings.doors}`,
    `  Windows: ${s.openings.windows}`);
  if (s.openings.archways > 0) L.push(`  Archways: ${s.openings.archways}`);
  L.push('\n=== Rooms ===', `Total: ${s.rooms.count}`, `Total Area: ${fmt1(s.rooms.total_area_sqft)} sq ft`);
  const ind = Object.entries(s.rooms.individual);
  if (ind.length) {
    L.push('\nIndividual Rooms:');
    for (const [name, d] of ind) L.push(`  ${name}:`, `    Area: ${fmt1(d.area_sqft)} sq ft`, `    Perimeter: ${fmt1(d.perimeter_ft)} ft`);
  }
  if (s.dimensions) {
    L.push('\n=== Dimensions ===', `Width: ${fmt1(s.dimensions.width_ft)} ft`, `Height: ${fmt1(s.dimensions.height_ft)} ft`,
      `Bounding Box: ${fmt1(s.dimensions.bounding_box_area_sqft)} sq ft`);
  }
  return L.join('\n');
}
