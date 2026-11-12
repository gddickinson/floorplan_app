"""
FloorPlan: the container of one floor (walls, openings, rooms, furniture, stairs, fixtures) and the .floorplan
JSON format (to_dict / from_dict / save_to_file / load_from_file). Split from core/geometry.py.
"""

import json
import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

from .elements import Opening, Point, Room, Wall
from .objects import Fixture, Furniture, Stair

logger = logging.getLogger(__name__)


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
