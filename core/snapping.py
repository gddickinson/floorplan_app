"""
Snapping and hit-testing on the plan (no GUI dependencies; used by gui/canvas*.py and ported to the web editor).

All lengths are inches in plan (world) coordinates; y grows downwards as on screen.
"""

from typing import Iterable, Optional

from .geometry import Point, Wall

GRID_SIZE = 12.0       # inches (1 foot grid)
SNAP_TOLERANCE = 6.0   # inches: a click this close to a wall endpoint snaps to it
OPENING_MIN_T = 0.1    # openings are kept between 10 % and 90 % along their wall
OPENING_MAX_T = 0.9


def snap_to_grid(point: Point, grid_size: float = GRID_SIZE) -> Point:
    """Snap a point to the nearest grid intersection."""
    return Point(round(point.x / grid_size) * grid_size, round(point.y / grid_size) * grid_size)


def find_snap_point(point: Point, walls: Iterable[Wall], grid_size: float = GRID_SIZE,
                    tolerance: float = SNAP_TOLERANCE) -> Point:
    """Best snap point: the first wall endpoint within `tolerance`, else the nearest grid intersection."""
    for wall in walls:
        for endpoint in (wall.start, wall.end):
            if point.distance_to(endpoint) < tolerance:
                return endpoint
    return snap_to_grid(point, grid_size)


def point_near_line(point: Point, line_start: Point, line_end: Point, tolerance: float) -> bool:
    """True if `point` is within `tolerance` of the segment line_start-line_end."""
    dx = line_end.x - line_start.x
    dy = line_end.y - line_start.y
    line_length = (dx ** 2 + dy ** 2) ** 0.5
    if line_length < 0.1:
        return point.distance_to(line_start) < tolerance
    t = ((point.x - line_start.x) * dx + (point.y - line_start.y) * dy) / (line_length ** 2)
    t = max(0, min(1, t))
    nearest = Point(line_start.x + t * dx, line_start.y + t * dy)
    return point.distance_to(nearest) < tolerance


def wall_at_point(point: Point, walls: Iterable[Wall], tolerance: float) -> Optional[Wall]:
    """First wall whose centre line passes within `tolerance` of `point`."""
    for wall in walls:
        if point_near_line(point, wall.start, wall.end, tolerance):
            return wall
    return None


def opening_position(wall: Wall, point: Point) -> float:
    """Fraction along `wall` (clamped to 0.1..0.9) of the projection of `point`: where a new door/window goes."""
    dx = wall.end.x - wall.start.x
    dy = wall.end.y - wall.start.y
    t = ((point.x - wall.start.x) * dx + (point.y - wall.start.y) * dy) / (wall.length() ** 2)
    return max(OPENING_MIN_T, min(OPENING_MAX_T, t))


def opening_center(wall: Wall, position: float) -> Point:
    """Plan coordinates of an opening's centre at `position` (0..1) along `wall`."""
    return Point(wall.start.x + (wall.end.x - wall.start.x) * position,
                 wall.start.y + (wall.end.y - wall.start.y) * position)
