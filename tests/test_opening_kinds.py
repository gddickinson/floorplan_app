"""Doors and windows of every specific type (french door, bay window, ...) are counted and treated as doors/windows."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core import FloorPlan, Opening, OpeningType, Point, Wall  # noqa: E402
from utils.measurements import get_floor_plan_statistics  # noqa: E402


def test_kind_properties():
    doors = [t for t in OpeningType if t.is_door]
    windows = [t for t in OpeningType if t.is_window]
    assert OpeningType.DOOR_FRENCH in doors and OpeningType.DOOR in doors and len(doors) == 9
    assert OpeningType.WINDOW_BAY in windows and OpeningType.WINDOW in windows and len(windows) == 10
    assert not OpeningType.ARCHWAY.is_door and not OpeningType.ARCHWAY.is_window


def test_statistics_count_specific_types():
    plan = FloorPlan()
    w = Wall(Point(0, 0), Point(240, 0))
    plan.add_wall(w)
    for t in (OpeningType.DOOR_FRENCH, OpeningType.DOOR_SINGLE, OpeningType.WINDOW_BAY, OpeningType.WINDOW,
              OpeningType.ARCHWAY):
        plan.add_opening(Opening(w.id, 0.5, 36, t))
    stats = get_floor_plan_statistics(plan)["openings"]
    assert (stats["count"], stats["doors"], stats["windows"], stats["archways"]) == (5, 2, 2, 1)
