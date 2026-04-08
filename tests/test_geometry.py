"""Unit tests for core/geometry.py data models."""

import sys
import json
import tempfile
import os
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.geometry import (
    Point, Wall, WallType, WallStyle, Opening, OpeningType,
    Room, Furniture, FurnitureType, Fixture, FixtureType,
    Stair, StairType, FloorPlan, Building,
)


# --- Point ---

class TestPoint:
    def test_to_tuple(self):
        p = Point(3.0, 4.0)
        assert p.to_tuple() == (3.0, 4.0)

    def test_to_dict_from_dict_roundtrip(self):
        p = Point(1.5, -2.5)
        assert Point.from_dict(p.to_dict()) == p

    def test_distance_to(self):
        p1 = Point(0, 0)
        p2 = Point(3, 4)
        assert abs(p1.distance_to(p2) - 5.0) < 1e-9

    def test_distance_to_self(self):
        p = Point(7.0, 8.0)
        assert p.distance_to(p) == 0.0


# --- Wall ---

class TestWall:
    def test_length(self):
        w = Wall(start=Point(0, 0), end=Point(10, 0))
        assert abs(w.length() - 10.0) < 1e-9

    def test_midpoint(self):
        w = Wall(start=Point(0, 0), end=Point(10, 0))
        mid = w.midpoint()
        assert abs(mid.x - 5.0) < 1e-9
        assert abs(mid.y - 0.0) < 1e-9

    def test_auto_id(self):
        w = Wall(start=Point(0, 0), end=Point(1, 1))
        assert w.id is not None

    def test_serialization_roundtrip(self):
        w = Wall(start=Point(1, 2), end=Point(3, 4),
                 thickness=8.0, wall_type=WallType.EXTERIOR,
                 wall_style=WallStyle.BRICK, height=120.0)
        d = w.to_dict()
        w2 = Wall.from_dict(d)
        assert w2.start == w.start
        assert w2.end == w.end
        assert w2.thickness == w.thickness
        assert w2.wall_type == w.wall_type
        assert w2.wall_style == w.wall_style
        assert w2.height == w.height


# --- Opening ---

class TestOpening:
    def test_auto_id(self):
        o = Opening(wall_id="w1", position=0.5, width=36.0,
                    opening_type=OpeningType.DOOR)
        assert o.id is not None

    def test_serialization_roundtrip(self):
        o = Opening(wall_id="w1", position=0.3, width=48.0,
                    opening_type=OpeningType.WINDOW_CASEMENT,
                    height=48.0, sill_height=30.0)
        d = o.to_dict()
        o2 = Opening.from_dict(d)
        assert o2.wall_id == o.wall_id
        assert o2.opening_type == o.opening_type


# --- FloorPlan ---

class TestFloorPlan:
    def _make_plan(self):
        plan = FloorPlan(name="Test")
        w = Wall(start=Point(0, 0), end=Point(100, 0))
        plan.add_wall(w)
        return plan, w

    def test_add_remove_wall(self):
        plan, w = self._make_plan()
        assert len(plan.walls) == 1
        assert plan.remove_wall(w.id)
        assert len(plan.walls) == 0

    def test_remove_wall_cascades_openings(self):
        plan, w = self._make_plan()
        o = Opening(wall_id=w.id, position=0.5, width=36.0,
                    opening_type=OpeningType.DOOR)
        plan.add_opening(o)
        assert len(plan.openings) == 1
        plan.remove_wall(w.id)
        assert len(plan.openings) == 0

    def test_add_opening_invalid_wall_raises(self):
        plan = FloorPlan()
        o = Opening(wall_id="nonexistent", position=0.5, width=36.0,
                    opening_type=OpeningType.DOOR)
        with pytest.raises(ValueError):
            plan.add_opening(o)

    def test_get_bounds(self):
        plan = FloorPlan()
        plan.add_wall(Wall(start=Point(0, 0), end=Point(100, 50)))
        plan.add_wall(Wall(start=Point(-10, -20), end=Point(50, 30)))
        bounds = plan.get_bounds()
        assert bounds is not None
        assert bounds[0].x == -10
        assert bounds[0].y == -20
        assert bounds[1].x == 100
        assert bounds[1].y == 50

    def test_get_bounds_empty(self):
        plan = FloorPlan()
        assert plan.get_bounds() is None

    def test_save_load_roundtrip(self):
        plan = FloorPlan(name="Roundtrip Test")
        w = Wall(start=Point(0, 0), end=Point(100, 0))
        plan.add_wall(w)
        plan.add_room(Room(name="Living Room", wall_ids=[w.id]))

        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            path = f.name
        try:
            plan.save_to_file(path)
            loaded = FloorPlan.load_from_file(path)
            assert loaded.name == plan.name
            assert len(loaded.walls) == 1
            assert len(loaded.rooms) == 1
            assert loaded.rooms[0].name == "Living Room"
        finally:
            os.unlink(path)

    def test_to_dict_from_dict(self):
        plan = FloorPlan(name="Dict Test", scale=2.0, floor_level=1)
        w = Wall(start=Point(0, 0), end=Point(50, 0))
        plan.add_wall(w)
        d = plan.to_dict()
        plan2 = FloorPlan.from_dict(d)
        assert plan2.name == plan.name
        assert plan2.scale == plan.scale
        assert plan2.floor_level == plan.floor_level

    def test_furniture_crud(self):
        plan = FloorPlan()
        f = Furniture(position=Point(10, 10), width=60, depth=30,
                      furniture_type=FurnitureType.SOFA)
        fid = plan.add_furniture(f)
        assert plan.get_furniture(fid) is f
        assert plan.remove_furniture(fid)
        assert plan.get_furniture(fid) is None

    def test_fixture_crud(self):
        plan = FloorPlan()
        f = Fixture(position=Point(5, 5), width=20, depth=20,
                    fixture_type=FixtureType.TOILET)
        fid = plan.add_fixture(f)
        assert plan.get_fixture(fid) is f
        assert plan.remove_fixture(fid)
        assert plan.get_fixture(fid) is None

    def test_stair_crud(self):
        plan = FloorPlan()
        s = Stair(start=Point(0, 0), end=Point(0, 100), width=36,
                  stair_type=StairType.STRAIGHT)
        sid = plan.add_stair(s)
        assert plan.get_stair(sid) is s
        assert plan.remove_stair(sid)
        assert plan.get_stair(sid) is None


# --- Building ---

class TestBuilding:
    def test_default_has_ground_floor(self):
        b = Building(name="Test")
        assert 0 in b.floors

    def test_add_remove_floor(self):
        b = Building(name="Test")
        fp = FloorPlan(name="Second Floor", floor_level=1)
        b.add_floor(fp)
        assert b.get_floor(1) is fp
        assert b.remove_floor(1)
        assert b.get_floor(1) is None

    def test_create_new_floor_copy(self):
        b = Building(name="Test")
        ground = b.get_floor(0)
        ground.add_wall(Wall(start=Point(0, 0), end=Point(100, 0)))
        second = b.create_new_floor(1, copy_from=0)
        assert len(second.walls) == 1
        assert second.floor_level == 1

    def test_serialization_roundtrip(self):
        b = Building(name="Test Building")
        b.create_new_floor(1, name="First Floor")
        d = b.to_dict()
        b2 = Building.from_dict(d)
        assert b2.name == b.name
        assert b2.get_floor_count() == b.get_floor_count()
