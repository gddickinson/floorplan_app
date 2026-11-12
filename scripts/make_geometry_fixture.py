"""Write tests/fixtures/geometry_fixture.json: what the Python core computes for a set of plans, so the JS port
(web/static/geometry.js, model.js) can be held to it by web/static/geometry.test.mjs.

Plans: the two examples served by the web app (web/catalog.py) plus synthetic cases (rooms clicked out of order, an
L-shaped room, rotated walls, T-junctions). For each: the .floorplan dict after a from_dict/to_dict round trip, room
outlines, areas and perimeters, the Statistics dict and text, bounds, snapping, point-in-room and opening placement.

Run: python scripts/make_geometry_fixture.py
"""
import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from core import FloorPlan, Opening, OpeningType, Point, Room, Wall, WallType  # noqa: E402
from core.plan_stats import calculate_perimeter, calculate_room_area, format_statistics, \
    get_floor_plan_statistics  # noqa: E402
from core.room_geometry import point_in_polygon, room_polygon  # noqa: E402
from core.snapping import find_snap_point, opening_position, point_near_line  # noqa: E402
from core.units import format_dimension  # noqa: E402
from web.catalog import EXAMPLES, example_plan  # noqa: E402

OUT = ROOT / "tests" / "fixtures" / "geometry_fixture.json"


def _synthetic():
    """Rooms whose walls are listed out of order, reversed, rotated, L-shaped and T-joined."""
    plan = FloorPlan(name="Synthetic cases", ceiling_height=108.0, metadata={"source": "make_geometry_fixture"})
    W = {}

    def wall(i, x1, y1, x2, y2, **kw):
        W[i] = Wall(Point(x1, y1), Point(x2, y2), id=i, **kw)
        plan.add_wall(W[i])

    # L-shaped room, walls listed shuffled and some reversed
    wall("l1", 0, 0, 240, 0, wall_type=WallType.EXTERIOR)
    wall("l2", 240, 120, 240, 0)
    wall("l3", 240, 120, 120, 120)
    wall("l4", 120, 120, 120, 216)
    wall("l5", 0, 216, 120, 216)
    wall("l6", 0, 216, 0, 0, thickness=8.0)
    plan.add_room(Room("L room", ["l4", "l1", "l6", "l3", "l5", "l2"], color="#FFE4B5", id="r_l"))
    # rotated square (45 degrees), walls listed in alternate order
    c, h = (500.0, 100.0), 60.0
    pts = [(c[0] + h * math.cos(a), c[1] + h * math.sin(a)) for a in (0, math.pi / 2, math.pi, 3 * math.pi / 2)]
    for k in range(4):
        wall(f"d{k}", *pts[k], *pts[(k + 1) % 4])
    plan.add_room(Room("Diamond", ["d0", "d2", "d1", "d3"], id="r_d"))
    # two rooms sharing a long wall that runs past both (T-junctions)
    wall("t_long", 300, 300, 300, 540)
    wall("t_a1", 300, 300, 420, 300)
    wall("t_a2", 420, 300, 420, 400)
    wall("t_mid", 420, 400, 300, 400)
    wall("t_b2", 420, 400, 420, 500)
    wall("t_b3", 300, 500, 420, 500)
    plan.add_room(Room("T upper", ["t_long", "t_mid", "t_a2", "t_a1"], id="r_t1"))
    plan.add_room(Room("T lower", ["t_b3", "t_long", "t_mid", "t_b2"], color="#B0E0E6", id="r_t2"))
    # walls that do not close: falls back to the endpoints in listed order
    wall("o1", 600, 300, 700, 300)
    wall("o2", 700, 300, 700, 380)
    wall("o3", 650, 420, 600, 400)
    plan.add_room(Room("Open", ["o1", "o2", "o3"], id="r_o"))
    for i, (w, pos, t) in enumerate([("l1", 0.5, OpeningType.DOOR_FRENCH), ("l2", 0.3, OpeningType.WINDOW_BAY),
                                     ("d0", 0.5, OpeningType.ARCHWAY), ("t_mid", 0.4, OpeningType.DOOR)]):
        plan.add_opening(Opening(w, pos, 36.0, t, id=f"op{i}"))
    return plan


def _probe_points():
    pts = []
    for i in range(60):  # deterministic scatter over the plans' extent, incl. negatives and non-grid values
        pts.append(((i * 37.3) % 760 - 40.0, (i * 53.9) % 600 - 30.0))
    return pts + [(243.0, 2.0), (419.0, 141.0), (5.9, 0.0), (-6.0, -6.0), (18.0, 18.0)]


def plan_case(name, plan):
    d = FloorPlan.from_dict(json.loads(json.dumps(plan.to_dict()))).to_dict()
    rooms = []
    for r in plan.rooms:
        poly = room_polygon(r, plan)
        rooms.append({"id": r.id, "polygon": [[p.x, p.y] for p in poly],
                      "area_sqft": calculate_room_area(r, plan), "perimeter_ft": calculate_perimeter(r, plan)})
    stats = get_floor_plan_statistics(plan)
    probes = _probe_points()
    snap = [find_snap_point(Point(x, y), plan.walls).to_tuple() for x, y in probes]
    inside = [[r.id for r in plan.rooms if point_in_polygon(Point(x, y), room_polygon(r, plan))] for x, y in probes]
    near = [[w.id for w in plan.walls if point_near_line(Point(x, y), w.start, w.end, 10.0)] for x, y in probes]
    place = {w.id: [opening_position(w, Point(x, y)) for x, y in probes[:12]] for w in plan.walls[:6]}
    b = plan.get_bounds()
    return {"name": name, "dict": d, "rooms": rooms, "stats": stats, "stats_text": format_statistics(stats),
            "bounds": [b[0].x, b[0].y, b[1].x, b[1].y] if b else None, "probes": probes, "snap": snap,
            "inside": inside, "near_walls": near, "opening_position": place}


def build():
    cases = [plan_case(n, example_plan(n)) for n in EXAMPLES] + [plan_case("synthetic", _synthetic())]
    values = [0, 0.04, 5.5, 11.94, 11.96, 12, 23.97, 30, 35.95, 120, 126, 126.25, 126.75, 1000.05, -0.04, -5.5,
              -6, -24, -30, -126, 0.25, 0.75, 3.14159, 59.999]
    dims = [[v, u, format_dimension(v, u)] for v in values for u in ("ft", "in", "auto")]
    return {"cases": cases, "format_dimension": dims}


def main():
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(build(), indent=1))
    print(f"wrote {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
