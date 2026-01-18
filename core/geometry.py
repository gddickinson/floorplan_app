"""
Core geometry classes for the floor plan application.

This module defines the fundamental building blocks for creating floor plans:
- Point: Basic 2D coordinate
- Wall: Linear wall segment
- Door: Opening in a wall
- Window: Window in a wall
- Room: Enclosed space defined by walls
- FloorPlan: Container for all floor plan elements
"""

import json
import logging
from dataclasses import dataclass, field
from typing import List, Tuple, Optional, Dict, Any
from enum import Enum

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


@dataclass
class Stair:
    """Represents a staircase in the floor plan."""
    start: Point
    end: Point
    width: float  # inches
    stair_type: StairType = StairType.STRAIGHT
    num_steps: int = 12
    rotation: float = 0.0  # degrees
    id: Optional[str] = None
    
    def __post_init__(self):
        if self.id is None:
            import uuid
            self.id = str(uuid.uuid4())
    
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


@dataclass
class FloorPlan:
    """
    Container for all floor plan elements.
    
    This is the main data structure that holds walls, openings, rooms,
    furniture, stairs, fixtures, and provides methods for manipulation and serialization.
    """
    name: str = "Untitled Floor Plan"
    walls: List[Wall] = field(default_factory=list)
    openings: List[Opening] = field(default_factory=list)
    rooms: List[Room] = field(default_factory=list)
    furniture: List[Furniture] = field(default_factory=list)
    stairs: List[Stair] = field(default_factory=list)
    fixtures: List[Fixture] = field(default_factory=list)
    scale: float = 1.0  # pixels per inch
    floor_level: int = 0  # Floor number (0=ground, 1=first, -1=basement, etc.)
    elevation: float = 0.0  # Height above ground level in inches
    ceiling_height: float = 96.0  # Default ceiling height in inches (8 feet)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def add_wall(self, wall: Wall) -> str:
        """Add a wall to the floor plan."""
        self.walls.append(wall)
        logger.info(f"Added wall: {wall.id} ({wall.length():.1f} inches)")
        return wall.id
    
    def remove_wall(self, wall_id: str) -> bool:
        """Remove a wall by ID."""
        for i, wall in enumerate(self.walls):
            if wall.id == wall_id:
                self.walls.pop(i)
                # Also remove any openings in this wall
                self.openings = [o for o in self.openings if o.wall_id != wall_id]
                logger.info(f"Removed wall: {wall_id}")
                return True
        logger.warning(f"Wall not found: {wall_id}")
        return False
    
    def get_wall(self, wall_id: str) -> Optional[Wall]:
        """Get a wall by ID."""
        for wall in self.walls:
            if wall.id == wall_id:
                return wall
        return None
    
    def add_opening(self, opening: Opening) -> str:
        """Add an opening to the floor plan."""
        if not self.get_wall(opening.wall_id):
            logger.error(f"Cannot add opening: wall {opening.wall_id} not found")
            raise ValueError(f"Wall {opening.wall_id} not found")
        
        self.openings.append(opening)
        logger.info(f"Added {opening.opening_type.value}: {opening.id}")
        return opening.id
    
    def remove_opening(self, opening_id: str) -> bool:
        """Remove an opening by ID."""
        for i, opening in enumerate(self.openings):
            if opening.id == opening_id:
                self.openings.pop(i)
                logger.info(f"Removed opening: {opening_id}")
                return True
        logger.warning(f"Opening not found: {opening_id}")
        return False
    
    def add_room(self, room: Room) -> str:
        """Add a room to the floor plan."""
        self.rooms.append(room)
        logger.info(f"Added room: {room.name} ({room.id})")
        return room.id
    
    def remove_room(self, room_id: str) -> bool:
        """Remove a room by ID."""
        for i, room in enumerate(self.rooms):
            if room.id == room_id:
                self.rooms.pop(i)
                logger.info(f"Removed room: {room_id}")
                return True
        logger.warning(f"Room not found: {room_id}")
        return False
    
    def add_furniture(self, furniture: Furniture) -> str:
        """Add furniture to the floor plan."""
        self.furniture.append(furniture)
        logger.info(f"Added furniture: {furniture.name} ({furniture.id})")
        return furniture.id
    
    def remove_furniture(self, furniture_id: str) -> bool:
        """Remove furniture by ID."""
        for i, item in enumerate(self.furniture):
            if item.id == furniture_id:
                self.furniture.pop(i)
                logger.info(f"Removed furniture: {furniture_id}")
                return True
        logger.warning(f"Furniture not found: {furniture_id}")
        return False
    
    def get_furniture(self, furniture_id: str) -> Optional[Furniture]:
        """Get furniture by ID."""
        for item in self.furniture:
            if item.id == furniture_id:
                return item
        return None
    
    def add_stair(self, stair: Stair) -> str:
        """Add a staircase to the floor plan."""
        self.stairs.append(stair)
        logger.info(f"Added stair: {stair.stair_type.value} ({stair.id})")
        return stair.id
    
    def remove_stair(self, stair_id: str) -> bool:
        """Remove a staircase by ID."""
        for i, stair in enumerate(self.stairs):
            if stair.id == stair_id:
                self.stairs.pop(i)
                logger.info(f"Removed stair: {stair_id}")
                return True
        logger.warning(f"Stair not found: {stair_id}")
        return False
    
    def get_stair(self, stair_id: str) -> Optional[Stair]:
        """Get a staircase by ID."""
        for stair in self.stairs:
            if stair.id == stair_id:
                return stair
        return None
    
    def add_fixture(self, fixture: Fixture) -> str:
        """Add a fixture to the floor plan."""
        self.fixtures.append(fixture)
        logger.info(f"Added fixture: {fixture.name} ({fixture.id})")
        return fixture.id
    
    def remove_fixture(self, fixture_id: str) -> bool:
        """Remove a fixture by ID."""
        for i, fixture in enumerate(self.fixtures):
            if fixture.id == fixture_id:
                self.fixtures.pop(i)
                logger.info(f"Removed fixture: {fixture_id}")
                return True
        logger.warning(f"Fixture not found: {fixture_id}")
        return False
    
    def get_fixture(self, fixture_id: str) -> Optional[Fixture]:
        """Get a fixture by ID."""
        for fixture in self.fixtures:
            if fixture.id == fixture_id:
                return fixture
        return None
    
    def get_bounds(self) -> Optional[Tuple[Point, Point]]:
        """
        Get the bounding box of the floor plan.
        
        Returns:
            Tuple of (min_point, max_point) or None if no walls
        """
        if not self.walls:
            return None
        
        all_x = [p.x for wall in self.walls for p in [wall.start, wall.end]]
        all_y = [p.y for wall in self.walls for p in [wall.start, wall.end]]
        
        return (
            Point(min(all_x), min(all_y)),
            Point(max(all_x), max(all_y))
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize the entire floor plan to dictionary."""
        return {
            "name": self.name,
            "scale": self.scale,
            "floor_level": self.floor_level,
            "elevation": self.elevation,
            "ceiling_height": self.ceiling_height,
            "walls": [w.to_dict() for w in self.walls],
            "openings": [o.to_dict() for o in self.openings],
            "rooms": [r.to_dict() for r in self.rooms],
            "furniture": [f.to_dict() for f in self.furniture],
            "stairs": [s.to_dict() for s in self.stairs],
            "fixtures": [f.to_dict() for f in self.fixtures],
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'FloorPlan':
        """Deserialize floor plan from dictionary."""
        plan = cls(
            name=data.get("name", "Untitled Floor Plan"),
            scale=data.get("scale", 1.0),
            floor_level=data.get("floor_level", 0),
            elevation=data.get("elevation", 0.0),
            ceiling_height=data.get("ceiling_height", 96.0),
            metadata=data.get("metadata", {})
        )
        
        # Load walls
        for wall_data in data.get("walls", []):
            plan.walls.append(Wall.from_dict(wall_data))
        
        # Load openings
        for opening_data in data.get("openings", []):
            plan.openings.append(Opening.from_dict(opening_data))
        
        # Load rooms
        for room_data in data.get("rooms", []):
            plan.rooms.append(Room.from_dict(room_data))
        
        # Load furniture
        for furniture_data in data.get("furniture", []):
            plan.furniture.append(Furniture.from_dict(furniture_data))
        
        # Load stairs
        for stair_data in data.get("stairs", []):
            plan.stairs.append(Stair.from_dict(stair_data))
        
        # Load fixtures
        for fixture_data in data.get("fixtures", []):
            plan.fixtures.append(Fixture.from_dict(fixture_data))
        
        logger.info(f"Loaded floor plan: {plan.name} (Level {plan.floor_level}, "
                   f"{len(plan.walls)} walls, {len(plan.openings)} openings, "
                   f"{len(plan.rooms)} rooms, {len(plan.furniture)} furniture, "
                   f"{len(plan.stairs)} stairs, {len(plan.fixtures)} fixtures)")
        
        return plan
    
    def save_to_file(self, filepath: str) -> None:
        """Save floor plan to JSON file."""
        with open(filepath, 'w') as f:
            json.dump(self.to_dict(), f, indent=2)
        logger.info(f"Saved floor plan to: {filepath}")
    
    @classmethod
    def load_from_file(cls, filepath: str) -> 'FloorPlan':
        """Load floor plan from JSON file."""
        with open(filepath, 'r') as f:
            data = json.load(f)
        logger.info(f"Loading floor plan from: {filepath}")
        return cls.from_dict(data)
    
    def __repr__(self) -> str:
        return (f"FloorPlan('{self.name}': Level {self.floor_level}, "
                f"{len(self.walls)} walls, {len(self.openings)} openings, "
                f"{len(self.rooms)} rooms, {len(self.furniture)} furniture, "
                f"{len(self.stairs)} stairs, {len(self.fixtures)} fixtures)")


@dataclass
class Building:
    """
    Container for a multi-story building with multiple floor plans.
    
    Manages multiple FloorPlan instances representing different levels
    of a building, with methods for navigation and 3D visualization.
    """
    name: str = "Untitled Building"
    floors: Dict[int, FloorPlan] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        # Ensure floors dict exists
        if not self.floors:
            # Create default ground floor
            self.floors = {0: FloorPlan(name="Ground Floor", floor_level=0)}
    
    def add_floor(self, floor_plan: FloorPlan) -> int:
        """Add a floor plan to the building."""
        level = floor_plan.floor_level
        self.floors[level] = floor_plan
        logger.info(f"Added floor level {level}: {floor_plan.name}")
        return level
    
    def remove_floor(self, level: int) -> bool:
        """Remove a floor by level number."""
        if level in self.floors:
            del self.floors[level]
            logger.info(f"Removed floor level {level}")
            return True
        logger.warning(f"Floor level {level} not found")
        return False
    
    def get_floor(self, level: int) -> Optional[FloorPlan]:
        """Get floor plan by level number."""
        return self.floors.get(level)
    
    def get_floor_levels(self) -> List[int]:
        """Get sorted list of floor levels."""
        return sorted(self.floors.keys())
    
    def get_floor_count(self) -> int:
        """Get total number of floors."""
        return len(self.floors)
    
    def create_new_floor(self, level: int, name: str = None,
                        copy_from: Optional[int] = None) -> FloorPlan:
        """
        Create a new floor plan.
        
        Args:
            level: Floor level number
            name: Floor name (auto-generated if None)
            copy_from: Optional floor level to copy layout from
            
        Returns:
            New FloorPlan instance
        """
        if name is None:
            name = self._generate_floor_name(level)
        
        if copy_from is not None and copy_from in self.floors:
            # Copy from existing floor
            import copy
            source_floor = self.floors[copy_from]
            new_floor = copy.deepcopy(source_floor)
            new_floor.name = name
            new_floor.floor_level = level
            new_floor.elevation = level * source_floor.ceiling_height
        else:
            # Create empty floor
            new_floor = FloorPlan(
                name=name,
                floor_level=level,
                elevation=level * 96.0  # 8 feet per level
            )
        
        self.add_floor(new_floor)
        return new_floor
    
    def _generate_floor_name(self, level: int) -> str:
        """Generate a floor name based on level."""
        if level == 0:
            return "Ground Floor"
        elif level < 0:
            if level == -1:
                return "Basement"
            else:
                return f"Basement {abs(level)}"
        else:
            ordinal = ["", "First", "Second", "Third", "Fourth", "Fifth",
                      "Sixth", "Seventh", "Eighth", "Ninth", "Tenth"]
            if level < len(ordinal):
                return f"{ordinal[level]} Floor"
            else:
                return f"Floor {level}"
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize building to dictionary."""
        return {
            "name": self.name,
            "floors": {
                str(level): floor.to_dict() 
                for level, floor in self.floors.items()
            },
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Building':
        """Deserialize building from dictionary."""
        building = cls(
            name=data.get("name", "Untitled Building"),
            metadata=data.get("metadata", {})
        )
        
        # Load floors
        building.floors = {}
        for level_str, floor_data in data.get("floors", {}).items():
            level = int(level_str)
            floor_plan = FloorPlan.from_dict(floor_data)
            building.floors[level] = floor_plan
        
        logger.info(f"Loaded building: {building.name} ({len(building.floors)} floors)")
        return building
    
    def save_to_file(self, filepath: str):
        """Save building to JSON file."""
        import json
        from pathlib import Path
        
        data = self.to_dict()
        
        path = Path(filepath)
        with open(path, 'w') as f:
            json.dump(data, f, indent=2)
        
        logger.info(f"Saved building to {filepath}")
    
    @classmethod
    def load_from_file(cls, filepath: str) -> 'Building':
        """Load building from JSON file."""
        import json
        from pathlib import Path
        
        path = Path(filepath)
        with open(path, 'r') as f:
            data = json.load(f)
        
        building = cls.from_dict(data)
        logger.info(f"Loaded building from {filepath}")
        return building
    
    def __repr__(self) -> str:
        levels = self.get_floor_levels()
        return (f"Building('{self.name}': {len(self.floors)} floors, "
                f"Levels {min(levels)} to {max(levels)})")
