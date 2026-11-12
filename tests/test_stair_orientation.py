"""Stairs have one orientation: the run from start to end (as drawn). `rotation` follows it, and setting
rotation turns the run, so the desktop selection box, the drawing and the saved file agree."""
import math
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core import FloorPlan, Point, Stair, StairType  # noqa: E402


@pytest.mark.parametrize("end,rot", [((0, 120), 0.0), ((-120, 0), 90.0), ((0, -120), 180.0), ((120, 0), 270.0),
                                     ((100, 100), 315.0)])
def test_rotation_follows_run(end, rot):
    s = Stair(Point(0, 0), Point(*end), 36, rotation=12.0)  # a stale stored rotation is ignored
    assert s.rotation == pytest.approx(rot)
    assert s.to_dict()["rotation"] == pytest.approx(rot)


def test_setting_rotation_turns_the_run_about_its_centre():
    s = Stair(Point(0, 0), Point(0, 120), 36)
    s.rotation = 270.0
    assert (s.start.x, s.start.y) == pytest.approx((-60, 60)) and (s.end.x, s.end.y) == pytest.approx((60, 60))
    assert s.length() == pytest.approx(120)


def test_file_round_trip_uses_the_run():
    d = Stair(Point(0, 0), Point(120, 0), 36, StairType.L_SHAPED).to_dict()
    d["rotation"] = 45.0  # file written by an older version
    s = Stair.from_dict(d)
    assert s.rotation == pytest.approx(270.0) and (s.end.x, s.end.y) == (120, 0)
    plan = FloorPlan.from_dict({"stairs": [d]})
    assert plan.to_dict()["stairs"][0]["rotation"] == pytest.approx(270.0)


def test_zero_length_stair_keeps_stored_rotation():
    assert Stair(Point(5, 5), Point(5, 5), 36, rotation=30.0).rotation == 30.0


def test_desktop_selection_box_covers_the_drawn_stair():
    pytest.importorskip("PyQt6")
    from gui.object_selection import SelectableObject
    s = Stair(Point(0, 0), Point(120, 0), 36)        # horizontal run
    obj = SelectableObject(s)
    assert obj.contains_point(Point(100, 10))        # on the treads
    assert not obj.contains_point(Point(60, 40))     # beside the run
    obj.rotation = 0.0                                # turning it in the desktop handler turns the drawing
    assert abs(s.start.x - s.end.x) < 1e-9 and math.isclose(s.length(), 120)
