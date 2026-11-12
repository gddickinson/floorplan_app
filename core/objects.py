"""
Placeable objects: Furniture, Fixture and Stair (+ their type enums and stair_rotation).
Split from core/geometry.py, which re-exports every name.
"""

import math
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, Optional

from .elements import Point


class FurnitureType(Enum):
    """Types of furniture."""
    BED_SINGLE = "bed_single"
    BED_DOUBLE = "bed_double"
    BED_QUEEN = "bed_queen"
    BED_KING = "bed_king"
    SOFA = "sofa"
    LOVESEAT = "loveseat"
    CHAIR = "chair"
    ARMCHAIR = "armchair"
    TABLE_DINING = "table_dining"
    TABLE_COFFEE = "table_coffee"
    TABLE_SIDE = "table_side"
    DESK = "desk"
    DRESSER = "dresser"
    NIGHTSTAND = "nightstand"
    BOOKSHELF = "bookshelf"
    CABINET = "cabinet"
    WARDROBE = "wardrobe"
    TV_STAND = "tv_stand"


@dataclass
class Furniture:
    """Represents a furniture item in the floor plan."""
    position: Point
    width: float  # inches
    depth: float  # inches
    furniture_type: FurnitureType
    rotation: float = 0.0  # degrees (0-360)
    name: Optional[str] = None
    id: Optional[str] = None
    
    def __post_init__(self):
        if self.id is None:
            import uuid
            self.id = str(uuid.uuid4())
        if self.name is None:
            self.name = self.furniture_type.value.replace("_", " ").title()
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "id": self.id,
            "position": self.position.to_dict(),
            "width": self.width,
            "depth": self.depth,
            "furniture_type": self.furniture_type.value,
            "rotation": self.rotation,
            "name": self.name
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Furniture':
        """Deserialize from dictionary."""
        return cls(
            position=Point.from_dict(data["position"]),
            width=data["width"],
            depth=data["depth"],
            furniture_type=FurnitureType(data["furniture_type"]),
            rotation=data.get("rotation", 0.0),
            name=data.get("name"),
            id=data.get("id")
        )


class StairType(Enum):
    """Types of stairs."""
    STRAIGHT = "straight"
    L_SHAPED = "l_shaped"
    U_SHAPED = "u_shaped"
    WINDER = "winder"
    SPIRAL = "spiral"
    CURVED = "curved"


def stair_rotation(start: Point, end: Point, fallback: float = 0.0) -> float:
    """Rotation (degrees, 0-360) of a stair whose run goes from start to end: 0 = running down the screen
    (+y), as for furniture rotated about its centre. A zero-length stair keeps `fallback`."""
    dx, dy = end.x - start.x, end.y - start.y
    if dx * dx + dy * dy < 1e-18:
        return fallback
    deg = math.atan2(dy, dx) * (180.0 / math.pi) - 90.0
    if deg < 0:
        deg += 360.0
    if deg >= 360.0:
        deg -= 360.0
    return deg


@dataclass(init=False)
class Stair:
    """Represents a staircase in the floor plan.

    The run from `start` to `end` is the stair's only orientation: `rotation` is derived from it (see
    stair_rotation) and setting `rotation` turns the run about its centre, so drawing, selection and the saved
    file always agree. A `rotation` passed in (e.g. from an older file) is used only for a zero-length stair.
    """
    start: Point
    end: Point
    width: float  # inches
    stair_type: StairType = StairType.STRAIGHT
    num_steps: int = 12
    id: Optional[str] = None

    def __init__(self, start: Point, end: Point, width: float,
                 stair_type: StairType = StairType.STRAIGHT, num_steps: int = 12,
                 rotation: float = 0.0, id: Optional[str] = None):
        self.start = start
        self.end = end
        self.width = width
        self.stair_type = stair_type
        self.num_steps = num_steps
        self._fallback_rotation = rotation % 360.0
        self.id = id
        if self.id is None:
            import uuid
            self.id = str(uuid.uuid4())

    @property
    def rotation(self) -> float:
        """Degrees, derived from the run start -> end."""
        return stair_rotation(self.start, self.end, self._fallback_rotation)

    @rotation.setter
    def rotation(self, value: float):
        """Turn the run about its centre so that `rotation` becomes `value`."""
        value = value % 360.0
        delta = math.radians(value - self.rotation)
        self._fallback_rotation = value
        if abs(delta) < 1e-12 or self.length() < 1e-9:
            return
        cx = (self.start.x + self.end.x) / 2
        cy = (self.start.y + self.end.y) / 2
        c, s = math.cos(delta), math.sin(delta)

        def turn(p: Point) -> Point:
            dx, dy = p.x - cx, p.y - cy
            return Point(cx + dx * c - dy * s, cy + dx * s + dy * c)
        self.start, self.end = turn(self.start), turn(self.end)

    def length(self) -> float:
        """Calculate stair length in inches."""
        return self.start.distance_to(self.end)
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "id": self.id,
            "start": self.start.to_dict(),
            "end": self.end.to_dict(),
            "width": self.width,
            "stair_type": self.stair_type.value,
            "num_steps": self.num_steps,
            "rotation": self.rotation
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Stair':
        """Deserialize from dictionary."""
        return cls(
            start=Point.from_dict(data["start"]),
            end=Point.from_dict(data["end"]),
            width=data["width"],
            stair_type=StairType(data.get("stair_type", "straight")),
            num_steps=data.get("num_steps", 12),
            rotation=data.get("rotation", 0.0),
            id=data.get("id")
        )


class FixtureType(Enum):
    """Types of fixtures and appliances."""
    # Bathroom fixtures
    TOILET = "toilet"
    SINK = "sink"
    SINK_DOUBLE = "sink_double"
    BATHTUB = "bathtub"
    SHOWER = "shower"
    SHOWER_CORNER = "shower_corner"
    VANITY = "vanity"
    
    # Kitchen appliances
    REFRIGERATOR = "refrigerator"
    STOVE = "stove"
    OVEN = "oven"
    DISHWASHER = "dishwasher"
    MICROWAVE = "microwave"
    SINK_KITCHEN = "sink_kitchen"
    
    # Laundry
    WASHER = "washer"
    DRYER = "dryer"
    
    # HVAC
    WATER_HEATER = "water_heater"
    FURNACE = "furnace"
    AC_UNIT = "ac_unit"


@dataclass
class Fixture:
    """Represents a fixture or appliance in the floor plan."""
    position: Point
    width: float  # inches
    depth: float  # inches
    fixture_type: FixtureType
    rotation: float = 0.0  # degrees
    name: Optional[str] = None
    id: Optional[str] = None
    
    def __post_init__(self):
        if self.id is None:
            import uuid
            self.id = str(uuid.uuid4())
        if self.name is None:
            self.name = self.fixture_type.value.replace("_", " ").title()
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "id": self.id,
            "position": self.position.to_dict(),
            "width": self.width,
            "depth": self.depth,
            "fixture_type": self.fixture_type.value,
            "rotation": self.rotation,
            "name": self.name
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Fixture':
        """Deserialize from dictionary."""
        return cls(
            position=Point.from_dict(data["position"]),
            width=data["width"],
            depth=data["depth"],
            fixture_type=FixtureType(data["fixture_type"]),
            rotation=data.get("rotation", 0.0),
            name=data.get("name"),
            id=data.get("id")
        )
