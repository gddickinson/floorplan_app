"""New floors sit on top of (or under) the existing floors, using their real ceiling heights."""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core import Building, FloorPlan  # noqa: E402


def _building(ceiling=120.0):
    b = Building(name="B")
    b.floors[0].ceiling_height = ceiling
    return b


def test_first_floor_sits_on_ground_floor_ceiling():
    b = _building(120.0)
    f = b.create_new_floor(1)
    assert f.elevation == pytest.approx(120.0) and f.ceiling_height == pytest.approx(120.0)


def test_stack_with_different_heights():
    b = _building(120.0)
    b.create_new_floor(1).ceiling_height = 108.0
    f2 = b.create_new_floor(2)
    assert f2.elevation == pytest.approx(228.0) and f2.ceiling_height == pytest.approx(108.0)


def test_basement_goes_below_ground():
    b = _building(120.0)
    b.floors[0].elevation = 0.0
    f = b.create_new_floor(-1)
    assert f.elevation == pytest.approx(-120.0)


def test_copy_uses_stacked_elevation():
    b = _building(110.0)
    b.add_floor(FloorPlan(name="First", floor_level=1, elevation=110.0, ceiling_height=100.0))
    f = b.create_new_floor(2, copy_from=0)
    assert f.ceiling_height == pytest.approx(110.0)
    assert f.elevation == pytest.approx(210.0)


def test_gap_levels_assume_the_new_floor_height():
    b = _building(100.0)
    f = b.create_new_floor(3)
    assert f.elevation == pytest.approx(300.0)


def test_default_building_unchanged():
    assert Building().create_new_floor(1).elevation == pytest.approx(96.0)
