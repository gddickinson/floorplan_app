"""
Example floor plans built by the repo's own code (no GUI dependencies).

- create_demo_house(): the "Demo House" used for the README screenshots (moved from scripts/generate_screenshots.py).
- create_test_floor(): the 10 ft x 10 ft four-wall "Test Floor" of tests/test_file_load.py.
"""

from .geometry import (
    Point, Wall, WallType, WallStyle, Opening, OpeningType,
    Room, FloorPlan, Furniture, FurnitureType, Fixture, FixtureType,
)


def ft(feet):
    """Convert feet to inches."""
    return feet * 12


def create_demo_house():
    """Create a demo house floor plan for screenshots."""
    plan = FloorPlan(name="Demo House")

    # Living Room (20' x 15')
    w1 = Wall(Point(0, 0), Point(ft(20), 0), 6, WallType.EXTERIOR, WallStyle.BRICK)
    w2 = Wall(Point(ft(20), 0), Point(ft(20), ft(15)), 6, WallType.INTERIOR)
    w3 = Wall(Point(ft(20), ft(15)), Point(0, ft(15)), 6, WallType.EXTERIOR, WallStyle.BRICK)
    w4 = Wall(Point(0, ft(15)), Point(0, 0), 6, WallType.EXTERIOR, WallStyle.BRICK)
    for w in [w1, w2, w3, w4]:
        plan.add_wall(w)

    plan.add_opening(Opening(w1.id, 0.5, 72, OpeningType.DOOR_FRENCH, height=84))
    plan.add_opening(Opening(w3.id, 0.5, 72, OpeningType.WINDOW_BAY, sill_height=36))
    plan.add_opening(Opening(w4.id, 0.4, 48, OpeningType.WINDOW_CASEMENT, sill_height=36))

    living = Room(
        name="Living Room", wall_ids=[w1.id, w2.id, w3.id, w4.id], color="#FFE4B5"
    )
    plan.add_room(living)

    plan.add_furniture(Furniture(Point(ft(10), ft(8)), 84, 36, FurnitureType.SOFA, rotation=90))
    plan.add_furniture(Furniture(Point(ft(14), ft(5)), 36, 36, FurnitureType.ARMCHAIR))
    plan.add_furniture(Furniture(Point(ft(10), ft(5)), 48, 24, FurnitureType.TABLE_COFFEE))
    plan.add_furniture(Furniture(Point(ft(16), ft(13)), 60, 18, FurnitureType.TV_STAND, rotation=270))

    # Kitchen (15' x 12')
    w5 = Wall(Point(ft(20), 0), Point(ft(35), 0), 6, WallType.EXTERIOR, WallStyle.BRICK)
    w6 = Wall(Point(ft(35), 0), Point(ft(35), ft(12)), 6, WallType.EXTERIOR, WallStyle.BRICK)
    w7 = Wall(Point(ft(35), ft(12)), Point(ft(20), ft(12)), 6, WallType.INTERIOR)
    for w in [w5, w6, w7]:
        plan.add_wall(w)

    plan.add_opening(Opening(w5.id, 0.5, 60, OpeningType.WINDOW_DOUBLE, sill_height=36))
    plan.add_opening(Opening(w7.id, 0.3, 36, OpeningType.DOOR_SINGLE))

    kitchen = Room(name="Kitchen", wall_ids=[w5.id, w6.id, w7.id, w2.id], color="#F0E68C")
    plan.add_room(kitchen)

    plan.add_fixture(Fixture(Point(ft(22), ft(2)), 36, 30, FixtureType.REFRIGERATOR))
    plan.add_fixture(Fixture(Point(ft(27), ft(2)), 30, 24, FixtureType.STOVE))
    plan.add_fixture(Fixture(Point(ft(31), ft(2)), 24, 24, FixtureType.DISHWASHER))
    plan.add_fixture(Fixture(Point(ft(29), ft(2)), 33, 22, FixtureType.SINK_KITCHEN, rotation=270))

    # Bedroom (15' x 12')
    w8 = Wall(Point(ft(20), ft(12)), Point(ft(20), ft(15)), 6, WallType.INTERIOR)
    w9 = Wall(Point(ft(20), ft(15)), Point(ft(35), ft(15)), 6, WallType.EXTERIOR, WallStyle.BRICK)
    w10 = Wall(Point(ft(35), ft(15)), Point(ft(35), ft(12)), 6, WallType.EXTERIOR, WallStyle.BRICK)
    for w in [w8, w9, w10]:
        plan.add_wall(w)

    plan.add_opening(Opening(w9.id, 0.5, 48, OpeningType.WINDOW_DOUBLE, sill_height=36))

    bedroom = Room(name="Bedroom", wall_ids=[w7.id, w8.id, w9.id, w10.id], color="#FFB6C1")
    plan.add_room(bedroom)

    plan.add_furniture(Furniture(Point(ft(27), ft(13.5)), 60, 80, FurnitureType.BED_QUEEN))
    plan.add_furniture(Furniture(Point(ft(23), ft(13)), 24, 18, FurnitureType.NIGHTSTAND))
    plan.add_furniture(Furniture(Point(ft(32), ft(13)), 24, 18, FurnitureType.NIGHTSTAND))

    # Bathroom (8' x 7')
    w11 = Wall(Point(ft(35), ft(12)), Point(ft(43), ft(12)), 6, WallType.EXTERIOR, WallStyle.BRICK)
    w12 = Wall(Point(ft(43), ft(12)), Point(ft(43), ft(5)), 6, WallType.EXTERIOR, WallStyle.BRICK)
    w13 = Wall(Point(ft(43), ft(5)), Point(ft(35), ft(5)), 6, WallType.INTERIOR)
    for w in [w11, w12, w13]:
        plan.add_wall(w)

    plan.add_opening(Opening(w13.id, 0.5, 30, OpeningType.DOOR_POCKET))
    plan.add_opening(Opening(w12.id, 0.5, 36, OpeningType.WINDOW_AWNING, sill_height=60))

    bathroom = Room(
        name="Bathroom", wall_ids=[w6.id, w11.id, w12.id, w13.id], color="#B0E0E6"
    )
    plan.add_room(bathroom)

    plan.add_fixture(Fixture(Point(ft(37), ft(7)), 20, 30, FixtureType.TOILET, rotation=90))
    plan.add_fixture(Fixture(Point(ft(41), ft(7)), 36, 22, FixtureType.SINK, rotation=270))
    plan.add_fixture(Fixture(Point(ft(39), ft(11)), 60, 32, FixtureType.BATHTUB))

    return plan


def create_test_floor():
    """The four-wall test floor plan of tests/test_file_load.py (10 ft x 10 ft, no room defined)."""
    plan = FloorPlan(name="Test Floor", floor_level=0)
    plan.add_wall(Wall(Point(0, 0), Point(120, 0), 6))
    plan.add_wall(Wall(Point(120, 0), Point(120, 120), 6))
    plan.add_wall(Wall(Point(120, 120), Point(0, 120), 6))
    plan.add_wall(Wall(Point(0, 120), Point(0, 0), 6))
    return plan
