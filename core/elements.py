"""
Plan elements: Point, walls (Wall + WallType/WallStyle/WallMaterial), openings (Opening + OpeningType) and Room.
Split from core/geometry.py, which re-exports every name.
"""

import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


@dataclass
class Point:
    """Represents a 2D point in the floor plan."""
    x: float
    y: float
    
    def to_tuple(self) -> Tuple[float, float]:
        """Convert to tuple representation."""
        return (self.x, self.y)
    
    def to_dict(self) -> Dict[str, float]:
        """Serialize to dictionary."""
        return {"x": self.x, "y": self.y}
    
    @classmethod
    def from_dict(cls, data: Dict[str, float]) -> 'Point':
        """Deserialize from dictionary."""
        return cls(x=data["x"], y=data["y"])
    
    def distance_to(self, other: 'Point') -> float:
        """Calculate Euclidean distance to another point."""
        return ((self.x - other.x)**2 + (self.y - other.y)**2)**0.5
    
    def __repr__(self) -> str:
        return f"Point({self.x:.1f}, {self.y:.1f})"


class WallType(Enum):
    """Types of walls in the floor plan."""
    EXTERIOR = "exterior"
    INTERIOR = "interior"
    LOAD_BEARING = "load_bearing"
    PARTITION = "partition"
    CURTAIN = "curtain"
    GLASS = "glass"
    RETAINING = "retaining"


class WallMaterial(Enum):
    """Materials for walls."""
    WOOD_FRAME = "wood_frame"
    STEEL_FRAME = "steel_frame"
    CONCRETE = "concrete"
    BRICK = "brick"
    STONE = "stone"
    GLASS = "glass"
    DRYWALL = "drywall"
    CMU = "cmu"  # Concrete Masonry Unit
    TIMBER = "timber"


class WallStyle(Enum):
    """Visual styles and materials for walls."""
    SOLID = "solid"
    BRICK = "brick"
    CONCRETE = "concrete"
    GLASS = "glass"
    CURTAIN = "curtain"
    WOOD_FRAME = "wood_frame"
    METAL_STUD = "metal_stud"
    STONE = "stone"


@dataclass
class Wall:
    """Represents a wall segment in the floor plan."""
    start: Point
    end: Point
    thickness: float = 6.0  # inches, typical interior wall
    wall_type: WallType = WallType.INTERIOR
    wall_style: WallStyle = WallStyle.SOLID
    height: float = 96.0  # inches (8 feet default ceiling height)
    id: Optional[str] = None
    
    def __post_init__(self):
        if self.id is None:
            import uuid
            self.id = str(uuid.uuid4())
    
    def length(self) -> float:
        """Calculate wall length in inches."""
        return self.start.distance_to(self.end)
    
    def midpoint(self) -> Point:
        """Calculate the midpoint of the wall."""
        return Point(
            (self.start.x + self.end.x) / 2,
            (self.start.y + self.end.y) / 2
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "id": self.id,
            "start": self.start.to_dict(),
            "end": self.end.to_dict(),
            "thickness": self.thickness,
            "wall_type": self.wall_type.value,
            "wall_style": self.wall_style.value,
            "height": self.height
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Wall':
        """Deserialize from dictionary."""
        return cls(
            start=Point.from_dict(data["start"]),
            end=Point.from_dict(data["end"]),
            thickness=data["thickness"],
            wall_type=WallType(data["wall_type"]),
            wall_style=WallStyle(data.get("wall_style", "solid")),
            height=data.get("height", 96.0),
            id=data.get("id")
        )
    
    def __repr__(self) -> str:
        return f"Wall({self.start} -> {self.end}, {self.length():.1f}\")"


class OpeningType(Enum):
    """Types of openings in walls."""
    # Standard openings
    DOOR = "door"
    WINDOW = "window"
    ARCHWAY = "archway"
    
    # Door types
    DOOR_SINGLE = "door_single"
    DOOR_DOUBLE = "door_double"
    DOOR_FRENCH = "door_french"
    DOOR_SLIDING = "door_sliding"
    DOOR_POCKET = "door_pocket"
    DOOR_BIFOLD = "door_bifold"
    DOOR_DUTCH = "door_dutch"
    DOOR_GARAGE = "door_garage"
    
    # Window types
    WINDOW_SINGLE = "window_single"
    WINDOW_DOUBLE = "window_double"
    WINDOW_BAY = "window_bay"
    WINDOW_BOW = "window_bow"
    WINDOW_CASEMENT = "window_casement"
    WINDOW_AWNING = "window_awning"
    WINDOW_SLIDER = "window_slider"
    WINDOW_PICTURE = "window_picture"
    WINDOW_SKYLIGHT = "window_skylight"

    @property
    def is_door(self) -> bool:
        """True for the generic door and every specific door type."""
        return self.value == "door" or self.value.startswith("door_")

    @property
    def is_window(self) -> bool:
        """True for the generic window and every specific window type."""
        return self.value == "window" or self.value.startswith("window_")


@dataclass
class Opening:
    """Represents an opening (door/window) in a wall."""
    wall_id: str
    position: float  # Position along wall (0.0 to 1.0)
    width: float  # inches
    opening_type: OpeningType
    height: float = 80.0  # inches (for doors, typically 6'8")
    sill_height: float = 36.0  # inches from floor (for windows)
    id: Optional[str] = None
    
    def __post_init__(self):
        if self.id is None:
            import uuid
            self.id = str(uuid.uuid4())
        
        if not 0.0 <= self.position <= 1.0:
            logger.warning(f"Opening position {self.position} outside valid range [0, 1]")
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "id": self.id,
            "wall_id": self.wall_id,
            "position": self.position,
            "width": self.width,
            "opening_type": self.opening_type.value,
            "height": self.height,
            "sill_height": self.sill_height
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Opening':
        """Deserialize from dictionary."""
        return cls(
            wall_id=data["wall_id"],
            position=data["position"],
            width=data["width"],
            opening_type=OpeningType(data["opening_type"]),
            height=data.get("height", 80.0),
            sill_height=data.get("sill_height", 36.0),
            id=data.get("id")
        )


@dataclass
class Room:
    """Represents a room in the floor plan."""
    name: str
    wall_ids: List[str] = field(default_factory=list)
    color: Optional[str] = None  # Hex color for visualization
    id: Optional[str] = None
    
    def __post_init__(self):
        if self.id is None:
            import uuid
            self.id = str(uuid.uuid4())
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "wall_ids": self.wall_ids,
            "color": self.color
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Room':
        """Deserialize from dictionary."""
        return cls(
            name=data["name"],
            wall_ids=data.get("wall_ids", []),
            color=data.get("color"),
            id=data.get("id")
        )
