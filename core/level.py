"""
Level/Floor support for multi-story buildings.

Provides the Level class for organizing floor plans into multiple stories.
"""

import logging
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
import uuid

logger = logging.getLogger(__name__)


@dataclass
class Level:
    """
    Represents a single level/floor in a multi-story building.
    
    Each level has its own set of walls, openings, rooms, furniture, etc.
    Levels stack vertically with configurable heights.
    """
    name: str = "Level 1"
    elevation: float = 0.0  # Height above ground in inches
    height: float = 108.0  # Floor-to-ceiling height in inches (9 feet default)
    walls: List[Any] = field(default_factory=list)
    openings: List[Any] = field(default_factory=list)
    rooms: List[Any] = field(default_factory=list)
    furniture: List[Any] = field(default_factory=list)
    stairs: List[Any] = field(default_factory=list)
    fixtures: List[Any] = field(default_factory=list)
    id: Optional[str] = None
    
    def __post_init__(self):
        if self.id is None:
            self.id = str(uuid.uuid4())
        logger.info(f"Created level: {self.name} at {self.elevation}\" elevation")
    
    def add_wall(self, wall) -> str:
        """Add a wall to this level."""
        self.walls.append(wall)
        return wall.id
    
    def remove_wall(self, wall_id: str) -> bool:
        """Remove a wall by ID."""
        for i, wall in enumerate(self.walls):
            if wall.id == wall_id:
                self.walls.pop(i)
                # Also remove associated openings
                self.openings = [o for o in self.openings if o.wall_id != wall_id]
                return True
        return False
    
    def get_wall(self, wall_id: str):
        """Get a wall by ID."""
        for wall in self.walls:
            if wall.id == wall_id:
                return wall
        return None
    
    def add_opening(self, opening) -> str:
        """Add an opening to this level."""
        self.openings.append(opening)
        return opening.id
    
    def remove_opening(self, opening_id: str) -> bool:
        """Remove an opening by ID."""
        for i, opening in enumerate(self.openings):
            if opening.id == opening_id:
                self.openings.pop(i)
                return True
        return False
    
    def add_room(self, room) -> str:
        """Add a room to this level."""
        self.rooms.append(room)
        return room.id
    
    def remove_room(self, room_id: str) -> bool:
        """Remove a room by ID."""
        for i, room in enumerate(self.rooms):
            if room.id == room_id:
                self.rooms.pop(i)
                return True
        return False
    
    def add_furniture(self, furniture) -> str:
        """Add furniture to this level."""
        self.furniture.append(furniture)
        return furniture.id
    
    def remove_furniture(self, furniture_id: str) -> bool:
        """Remove furniture by ID."""
        for i, item in enumerate(self.furniture):
            if item.id == furniture_id:
                self.furniture.pop(i)
                return True
        return False
    
    def get_furniture(self, furniture_id: str):
        """Get furniture by ID."""
        for item in self.furniture:
            if item.id == furniture_id:
                return item
        return None
    
    def add_stair(self, stair) -> str:
        """Add a staircase to this level."""
        self.stairs.append(stair)
        return stair.id
    
    def remove_stair(self, stair_id: str) -> bool:
        """Remove a staircase by ID."""
        for i, stair in enumerate(self.stairs):
            if stair.id == stair_id:
                self.stairs.pop(i)
                return True
        return False
    
    def get_stair(self, stair_id: str):
        """Get a staircase by ID."""
        for stair in self.stairs:
            if stair.id == stair_id:
                return stair
        return None
    
    def add_fixture(self, fixture) -> str:
        """Add a fixture to this level."""
        self.fixtures.append(fixture)
        return fixture.id
    
    def remove_fixture(self, fixture_id: str) -> bool:
        """Remove a fixture by ID."""
        for i, fixture in enumerate(self.fixtures):
            if fixture.id == fixture_id:
                self.fixtures.pop(i)
                return True
        return False
    
    def get_fixture(self, fixture_id: str):
        """Get a fixture by ID."""
        for fixture in self.fixtures:
            if fixture.id == fixture_id:
                return fixture
        return None
    
    def get_bounds(self):
        """Get bounding box of all elements in this level."""
        if not self.walls:
            return None
        
        from core import Point
        
        min_x = min(min(w.start.x, w.end.x) for w in self.walls)
        max_x = max(max(w.start.x, w.end.x) for w in self.walls)
        min_y = min(min(w.start.y, w.end.y) for w in self.walls)
        max_y = max(max(w.start.y, w.end.y) for w in self.walls)
        
        return (Point(min_x, min_y), Point(max_x, max_y))
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "elevation": self.elevation,
            "height": self.height,
            "walls": [w.to_dict() for w in self.walls],
            "openings": [o.to_dict() for o in self.openings],
            "rooms": [r.to_dict() for r in self.rooms],
            "furniture": [f.to_dict() for f in self.furniture],
            "stairs": [s.to_dict() for s in self.stairs],
            "fixtures": [f.to_dict() for f in self.fixtures]
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Level':
        """Deserialize from dictionary."""
        from core import Wall, Opening, Room, Furniture, Stair, Fixture
        
        level = cls(
            name=data.get("name", "Level 1"),
            elevation=data.get("elevation", 0.0),
            height=data.get("height", 108.0),
            id=data.get("id")
        )
        
        # Load walls
        for wall_data in data.get("walls", []):
            level.walls.append(Wall.from_dict(wall_data))
        
        # Load openings
        for opening_data in data.get("openings", []):
            level.openings.append(Opening.from_dict(opening_data))
        
        # Load rooms
        for room_data in data.get("rooms", []):
            level.rooms.append(Room.from_dict(room_data))
        
        # Load furniture
        for furniture_data in data.get("furniture", []):
            level.furniture.append(Furniture.from_dict(furniture_data))
        
        # Load stairs
        for stair_data in data.get("stairs", []):
            level.stairs.append(Stair.from_dict(stair_data))
        
        # Load fixtures
        for fixture_data in data.get("fixtures", []):
            level.fixtures.append(Fixture.from_dict(fixture_data))
        
        logger.info(f"Loaded level: {level.name} ({len(level.walls)} walls, "
                   f"{len(level.openings)} openings, {len(level.rooms)} rooms)")
        
        return level
    
    def __repr__(self) -> str:
        return (f"Level('{self.name}': {len(self.walls)} walls, "
                f"{len(self.openings)} openings, {len(self.rooms)} rooms, "
                f"elevation={self.elevation}\")")

