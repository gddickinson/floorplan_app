"""Room outline and area: walls listed in any order (as clicked in Create Room mode) give the true room polygon."""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core import FloorPlan, Point, Room, Wall  # noqa: E402
from utils.measurements import calculate_room_area  # noqa: E402


def _square_plan(order):
    """10 ft x 10 ft room; `order` lists which walls (top, right, bottom, left) the user clicked, in click order."""
    plan = FloorPlan()
    walls = {
        "top": Wall(Point(0, 0), Point(120, 0), id="top"),
        "right": Wall(Point(120, 0), Point(120, 120), id="right"),
        "bottom": Wall(Point(120, 120), Point(0, 120), id="bottom"),
        "left": Wall(Point(0, 120), Point(0, 0), id="left"),
    }
    for w in walls.values():
        plan.add_wall(w)
    room = Room("Room", wall_ids=list(order))
    plan.add_room(room)
    return plan, room


@pytest.mark.parametrize("order", [
    ["top", "right", "bottom", "left"],
    ["top", "bottom", "right", "left"],      # opposite walls clicked one after the other
    ["left", "top", "bottom", "right"],
    ["bottom", "top", "left", "right"],
])
def test_area_independent_of_click_order(order):
    plan, room = _square_plan(order)
    assert calculate_room_area(room, plan) == pytest.approx(100.0)


def test_reversed_wall_direction():
    plan = FloorPlan()
    for w in [Wall(Point(0, 0), Point(120, 0), id="a"), Wall(Point(0, 96), Point(120, 96), id="b"),
              Wall(Point(120, 96), Point(120, 0), id="c"), Wall(Point(0, 0), Point(0, 96), id="d")]:
        plan.add_wall(w)
    room = Room("R", wall_ids=["a", "b", "c", "d"])
    assert calculate_room_area(room, plan) == pytest.approx(80.0)


def test_t_junction_wall_longer_than_room():
    """A wall shared with a bigger neighbour that runs past the room corner (demo house kitchen)."""
    plan = FloorPlan()
    for w in [Wall(Point(0, 120), Point(0, 0), id="long"),    # runs 0..120, room only uses 0..96
              Wall(Point(0, 96), Point(144, 96), id="b"), Wall(Point(144, 0), Point(144, 96), id="c"),
              Wall(Point(0, 0), Point(144, 0), id="a")]:
        plan.add_wall(w)
    room = Room("R", wall_ids=["long", "b", "c", "a"])
    assert calculate_room_area(room, plan) == pytest.approx(12 * 8)


def test_shared_wall_running_past_both_corners():
    """Two rooms on one long wall; for the lower room the long wall overshoots at both of its corners."""
    plan = FloorPlan()
    for w in [Wall(Point(300, 300), Point(300, 540), id="long"), Wall(Point(300, 300), Point(420, 300), id="a1"),
              Wall(Point(420, 300), Point(420, 400), id="a2"), Wall(Point(420, 400), Point(300, 400), id="mid"),
              Wall(Point(420, 400), Point(420, 500), id="b2"), Wall(Point(300, 500), Point(420, 500), id="b3")]:
        plan.add_wall(w)
    upper = Room("U", wall_ids=["long", "mid", "a2", "a1"])
    lower = Room("L", wall_ids=["b3", "long", "mid", "b2"])
    starts_on_long = Room("L2", wall_ids=["long", "b3", "b2", "mid"])
    for room in (upper, lower, starts_on_long):
        assert calculate_room_area(room, plan) == pytest.approx(120 * 100 / 144)


def test_perimeter_follows_room_outline():
    """A wall shared with a bigger neighbour only counts up to the room corner (12x8 ft room: 40 ft)."""
    from utils.measurements import calculate_perimeter
    plan = FloorPlan()
    for w in [Wall(Point(0, 120), Point(0, 0), id="long"), Wall(Point(0, 96), Point(144, 96), id="b"),
              Wall(Point(144, 0), Point(144, 96), id="c"), Wall(Point(0, 0), Point(144, 0), id="a")]:
        plan.add_wall(w)
    room = Room("R", wall_ids=["long", "b", "c", "a"])
    assert calculate_perimeter(room, plan) == pytest.approx(40.0)
