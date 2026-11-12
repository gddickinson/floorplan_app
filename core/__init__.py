"""
Core module for floor plan application.

Provides the fundamental geometry and data structures for creating
and manipulating architectural floor plans. Everything in core/ is free of GUI imports
(the web interface in web/ uses it without PyQt6).

Modules:
- geometry.py: re-exports the model classes below (kept for existing imports)
- elements.py: Point, Wall, Opening, Room (+ wall/opening enums)
- objects.py: Furniture, Fixture, Stair (+ type enums, stair_rotation)
- floor_plan.py: FloorPlan (.floorplan JSON format)
- building.py: Building (multi-story, create_new_floor, stacked_elevation)
- level.py: Level (multi-story helper)
- room_geometry.py: room_polygon (walls joined into the room outline), polygon_area, point_in_polygon
- snapping.py: grid / wall-endpoint snapping, wall hit-testing, opening position along a wall
- plan_stats.py: room areas and perimeters, wall lengths, opening counts (Statistics dialog)
- units.py: format_dimension (feet-inches labels), unit conversion
- config.py: AppConfig constants
- catalog.py: standard furniture / fixture / stair sizes (Object Library)
- demo_plans.py: the README "Demo House" and the test floor, built in code
"""

from .geometry import (
    Point,
    Wall,
    WallType,
    WallStyle,
    Opening,
    OpeningType,
    Room,
    Furniture,
    FurnitureType,
    Stair,
    StairType,
    Fixture,
    FixtureType,
    FloorPlan,
    Building
)

__all__ = [
    'Point',
    'Wall',
    'WallType',
    'WallStyle',
    'Opening',
    'OpeningType',
    'Room',
    'Furniture',
    'FurnitureType',
    'Stair',
    'StairType',
    'Fixture',
    'FixtureType',
    'FloorPlan',
    'Building'
]

