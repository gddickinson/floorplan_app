"""
Room outline geometry (no GUI dependencies).

A Room stores only the ids of its walls, in whatever order the user clicked them, and each wall may point either way
or run past the room corner (a T-junction with a neighbouring room). `room_polygon` walks the walls by shared
endpoints / T-junctions and puts a vertex where consecutive walls meet (the intersection of their centre lines),
so area, hit-testing and drawing all use the true outline. The web editor (web/static/geometry.js) ports this file.
"""

import math
from typing import List, Optional, Sequence, Tuple

from .geometry import FloorPlan, Point, Room, Wall

JOIN_TOLERANCE = 1.0  # inches: an endpoint this close to another wall is joined to it


def point_segment_distance(p: Point, a: Point, b: Point) -> float:
    """Distance from p to the segment a-b."""
    dx, dy = b.x - a.x, b.y - a.y
    len_sq = dx * dx + dy * dy
    if len_sq < 1e-12:
        return p.distance_to(a)
    t = max(0.0, min(1.0, ((p.x - a.x) * dx + (p.y - a.y) * dy) / len_sq))
    return math.hypot(p.x - (a.x + t * dx), p.y - (a.y + t * dy))


def line_intersection(w1: Wall, w2: Wall) -> Optional[Point]:
    """Intersection of the (infinite) centre lines of two walls, or None if they are parallel."""
    x1, y1, x2, y2 = w1.start.x, w1.start.y, w1.end.x, w1.end.y
    x3, y3, x4, y4 = w2.start.x, w2.start.y, w2.end.x, w2.end.y
    den = (x1 - x2) * (y3 - y4) - (y1 - y2) * (x3 - x4)
    l1 = math.hypot(x2 - x1, y2 - y1)
    l2 = math.hypot(x4 - x3, y4 - y3)
    if l1 < 1e-9 or l2 < 1e-9 or abs(den) < 1e-9 * l1 * l2:
        return None
    a = x1 * y2 - y1 * x2
    b = x3 * y4 - y3 * x4
    return Point((a * (x3 - x4) - (x1 - x2) * b) / den, (a * (y3 - y4) - (y1 - y2) * b) / den)


def _legacy_polygon(walls: Sequence[Wall]) -> List[Point]:
    """Wall endpoints in listed order without duplicates (fallback for walls that do not form a closed chain)."""
    pts, seen = [], set()
    for w in walls:
        for p in (w.start, w.end):
            key = (round(p.x, 2), round(p.y, 2))
            if key not in seen:
                seen.add(key)
                pts.append(p)
    return pts


def _segment_intersection(w1: Wall, w2: Wall) -> Optional[Point]:
    """Crossing point of two wall segments (centre lines), or None."""
    p = line_intersection(w1, w2)
    if p is None:
        return None
    if point_segment_distance(p, w1.start, w1.end) > 1e-6 or point_segment_distance(p, w2.start, w2.end) > 1e-6:
        return None
    return p


def _contacts(wall: Wall, others: Sequence[Wall], tol: float) -> List[Point]:
    """Points where any of `others` touches `wall` (endpoint on the other wall, or a crossing)."""
    pts = []
    for o in others:
        for e in (o.start, o.end):
            if point_segment_distance(e, wall.start, wall.end) <= tol:
                pts.append(e)
        for e in (wall.start, wall.end):
            if point_segment_distance(e, o.start, o.end) <= tol:
                pts.append(e)
        x = _segment_intersection(wall, o)
        if x is not None:
            pts.append(x)
    return pts


def _next_tip(wall: Wall, junction: Point, targets: Sequence[Wall], tol: float) -> Point:
    """Where the outline leaves `wall` after entering it at `junction`: the nearest other contact with a
    remaining room wall, or the far endpoint if nothing else touches it."""
    best, best_d = None, 0.0
    for p in _contacts(wall, targets, tol):
        d = p.distance_to(junction)
        if d > tol and (best is None or d < best_d):
            best, best_d = p, d
    if best is not None:
        return best
    return wall.start if wall.start.distance_to(junction) >= wall.end.distance_to(junction) else wall.end


def _chain(walls: List[Wall], tol: float) -> Optional[List[Tuple[Wall, Point]]]:
    """Order walls into a closed loop. Returns [(wall, junction point with the next wall)] or None."""
    def touches(p, w):
        return point_segment_distance(p, w.start, w.end) <= tol

    first = walls[0]
    rest = walls[1:]
    # Walk away from the end of the first wall that touches another wall.
    start = first.start if any(touches(first.end, w) for w in rest) else first.end
    tip = _next_tip(first, start, rest, tol)
    order: List[Tuple[Wall, Point]] = []
    current = first
    remaining = list(rest)
    while remaining:
        cands = [w for w in remaining if touches(tip, w)]
        if not cands:
            return None
        nxt = min(cands, key=lambda w: min(tip.distance_to(w.start), tip.distance_to(w.end)))
        order.append((current, tip))
        remaining.remove(nxt)
        current, tip = nxt, _next_tip(nxt, tip, remaining or [first], tol)
    if not touches(tip, first):
        return None
    order.append((current, tip))
    return order


def room_outline(room: Room, floor_plan: FloorPlan, tol: float = JOIN_TOLERANCE) -> Tuple[List[Point], bool]:
    """(vertices, closed): the room outline in walking order, and whether the walls joined into a closed loop
    (if not, the vertices are the wall endpoints in listed order, as before)."""
    walls = [w for w in (floor_plan.get_wall(i) for i in room.wall_ids) if w is not None]
    if len(walls) < 3:
        return _legacy_polygon(walls), False
    order = _chain(walls, tol)
    if order is None:
        return _legacy_polygon(walls), False
    pts: List[Point] = []
    n = len(order)
    for i in range(n):
        wall, junction = order[i]
        nxt = order[(i + 1) % n][0]
        p = line_intersection(wall, nxt)
        if p is None or p.distance_to(junction) > max(tol, 0.5 * wall.thickness + nxt.thickness):
            p = junction
        if not pts or p.distance_to(pts[-1]) > 1e-9:
            pts.append(p)
    if len(pts) > 1 and pts[0].distance_to(pts[-1]) <= 1e-9:
        pts.pop()
    # Start at the vertex where the first listed wall's chain begins, so output is stable.
    return pts[-1:] + pts[:-1], True


def room_polygon(room: Room, floor_plan: FloorPlan, tol: float = JOIN_TOLERANCE) -> List[Point]:
    """Vertices of the room outline (wall centre lines), in walking order."""
    return room_outline(room, floor_plan, tol)[0]


def polygon_area(points: Sequence[Point]) -> float:
    """Shoelace area (square inches) of a simple polygon."""
    n = len(points)
    if n < 3:
        return 0.0
    s = 0.0
    for i in range(n):
        j = (i + 1) % n
        s += points[i].x * points[j].y - points[j].x * points[i].y
    return abs(s) / 2.0


def point_in_polygon(p: Point, points: Sequence[Point]) -> bool:
    """Even-odd ray casting test."""
    inside = False
    n = len(points)
    j = n - 1
    for i in range(n):
        a, b = points[i], points[j]
        if (a.y > p.y) != (b.y > p.y):
            x = (b.x - a.x) * (p.y - a.y) / (b.y - a.y) + a.x
            if p.x < x:
                inside = not inside
        j = i
    return inside


def polygon_label_point(points: Sequence[Point]) -> Optional[Point]:
    """Mean of the vertices (where the desktop canvas centres the room name)."""
    if not points:
        return None
    return Point(sum(p.x for p in points) / len(points), sum(p.y for p in points) / len(points))
