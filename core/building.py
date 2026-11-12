"""
Building: a multi-story set of FloorPlans keyed by level, with floor creation and JSON (de)serialisation.
Split from core/geometry.py, which re-exports every name.
"""

import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .floor_plan import FloorPlan

logger = logging.getLogger(__name__)


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
        else:
            # Create empty floor with the ceiling height of the nearest existing floor
            ref = self._nearest_floor(level)
            new_floor = FloorPlan(
                name=name,
                floor_level=level,
                ceiling_height=ref.ceiling_height if ref else 96.0,
            )
        new_floor.elevation = self.stacked_elevation(level, new_floor.ceiling_height)

        self.add_floor(new_floor)
        return new_floor
    
    def _nearest_floor(self, level: int) -> Optional[FloorPlan]:
        """Existing floor closest to `level` (the one below wins a tie), or None."""
        others = [lv for lv in self.floors if lv != level]
        if not others:
            return None
        return self.floors[min(others, key=lambda lv: (abs(lv - level), lv > level))]

    def stacked_elevation(self, level: int, ceiling_height: float) -> float:
        """Elevation of a floor at `level` stacked on (or under) the nearest existing floor using the real
        ceiling heights; levels in between are assumed to be `ceiling_height` tall. The model has no floor
        slab thickness, so floors stack ceiling to floor."""
        ref = self._nearest_floor(level)
        if ref is None:
            return level * ceiling_height
        if ref.floor_level < level:
            return ref.elevation + ref.ceiling_height + (level - ref.floor_level - 1) * ceiling_height
        return ref.elevation - (ref.floor_level - level) * ceiling_height

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
