"""
Core module for floor plan application.

Provides the fundamental geometry and data structures for creating
and manipulating architectural floor plans.
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

