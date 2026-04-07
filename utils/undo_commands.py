"""
Undo Commands for Object Transformations

These commands support undo/redo for moving, resizing, and rotating objects.
"""

import logging
from dataclasses import dataclass
from typing import Union, Optional

from core import Point, Furniture, Fixture, Stair

logger = logging.getLogger(__name__)


@dataclass
class ObjectState:
    """Store the state of an object for undo/redo."""
    position: Point
    width: float
    depth: float
    rotation: float
    # For stairs: store start and end points
    start: Optional[Point] = None
    end: Optional[Point] = None
    
    @classmethod
    def from_object(cls, obj: Union[Furniture, Fixture, Stair]) -> 'ObjectState':
        """Create state from an object."""
        if isinstance(obj, Stair):
            # For stairs, store start and end points
            return cls(
                position=Point((obj.start.x + obj.end.x) / 2, (obj.start.y + obj.end.y) / 2),
                width=obj.width,
                depth=obj.length(),
                rotation=obj.rotation,
                start=Point(obj.start.x, obj.start.y),
                end=Point(obj.end.x, obj.end.y)
            )
        else:
            # For furniture and fixtures
            return cls(
                position=Point(obj.position.x, obj.position.y),
                width=obj.width,
                depth=obj.depth,
                rotation=obj.rotation
            )
    
    def apply_to_object(self, obj: Union[Furniture, Fixture, Stair]):
        """Apply this state to an object."""
        if isinstance(obj, Stair):
            # For stairs, restore start and end points
            if self.start and self.end:
                obj.start = Point(self.start.x, self.start.y)
                obj.end = Point(self.end.x, self.end.y)
            obj.width = self.width
            obj.rotation = self.rotation
        else:
            # For furniture and fixtures
            obj.position.x = self.position.x
            obj.position.y = self.position.y
            obj.width = self.width
            obj.depth = self.depth
            obj.rotation = self.rotation


class TransformObjectCommand:
    """
    Command for transforming (move/resize/rotate) an object.
    Compatible with the existing Command pattern.
    """
    
    def __init__(self, obj: Union[Furniture, Fixture, Stair],
                 old_state: ObjectState,
                 new_state: ObjectState,
                 description: str = "Transform Object"):
        """
        Initialize command.
        
        Args:
            obj: The object being transformed
            old_state: State before transformation
            new_state: State after transformation
            description: Human-readable description
        """
        self.obj = obj
        self.old_state = old_state
        self.new_state = new_state
        self._description = description
    
    def execute(self, floor_plan=None):
        """Apply the transformation."""
        self.new_state.apply_to_object(self.obj)
        logger.debug(f"Applied transformation: {self._description}")
    
    def undo(self, floor_plan=None):
        """Undo the transformation."""
        self.old_state.apply_to_object(self.obj)
        logger.debug(f"Undid transformation: {self._description}")
    
    def description(self):
        """Get command description for display."""
        return self._description


class AddObjectCommand:
    """
    Command for adding furniture, fixture, or stair.
    Compatible with the existing Command pattern.
    """
    
    def __init__(self, floor_plan, obj: Union[Furniture, Fixture, Stair]):
        """
        Initialize command.
        
        Args:
            floor_plan: The FloorPlan to add to
            obj: The object to add
        """
        self.floor_plan = floor_plan
        self.obj = obj
        
        # Determine object type
        if isinstance(obj, Furniture):
            self.obj_type = 'furniture'
            self._description = f"Add {obj.furniture_type.value.replace('_', ' ').title()}"
        elif isinstance(obj, Fixture):
            self.obj_type = 'fixture'
            self._description = f"Add {obj.fixture_type.value.replace('_', ' ').title()}"
        elif isinstance(obj, Stair):
            self.obj_type = 'stair'
            self._description = "Add Staircase"
        else:
            self.obj_type = 'unknown'
            self._description = "Add Object"
    
    def execute(self, floor_plan=None):
        """Add the object."""
        fp = floor_plan or self.floor_plan
        if self.obj_type == 'furniture':
            fp.add_furniture(self.obj)
        elif self.obj_type == 'fixture':
            fp.add_fixture(self.obj)
        elif self.obj_type == 'stair':
            fp.add_stair(self.obj)
        
        logger.info(f"Added {self.obj_type}: {self._description}")
    
    def undo(self, floor_plan=None):
        """Remove the object."""
        fp = floor_plan or self.floor_plan
        if self.obj_type == 'furniture' and self.obj in fp.furniture:
            fp.furniture.remove(self.obj)
        elif self.obj_type == 'fixture' and self.obj in fp.fixtures:
            fp.fixtures.remove(self.obj)
        elif self.obj_type == 'stair' and self.obj in fp.stairs:
            fp.stairs.remove(self.obj)
        
        logger.info(f"Removed {self.obj_type}: {self._description}")
    
    def description(self):
        """Get command description for display."""
        return self._description


class RemoveObjectCommand:
    """
    Command for removing furniture, fixture, or stair.
    Compatible with the existing Command pattern.
    """
    
    def __init__(self, floor_plan, obj: Union[Furniture, Fixture, Stair]):
        """
        Initialize command.
        
        Args:
            floor_plan: The FloorPlan to remove from
            obj: The object to remove
        """
        self.floor_plan = floor_plan
        self.obj = obj
        
        # Determine object type
        if isinstance(obj, Furniture):
            self.obj_type = 'furniture'
            self._description = f"Delete {obj.furniture_type.value.replace('_', ' ').title()}"
        elif isinstance(obj, Fixture):
            self.obj_type = 'fixture'
            self._description = f"Delete {obj.fixture_type.value.replace('_', ' ').title()}"
        elif isinstance(obj, Stair):
            self.obj_type = 'stair'
            self._description = "Delete Staircase"
        else:
            self.obj_type = 'unknown'
            self._description = "Delete Object"
    
    def execute(self, floor_plan=None):
        """Remove the object."""
        fp = floor_plan or self.floor_plan
        if self.obj_type == 'furniture' and self.obj in fp.furniture:
            fp.furniture.remove(self.obj)
        elif self.obj_type == 'fixture' and self.obj in fp.fixtures:
            fp.fixtures.remove(self.obj)
        elif self.obj_type == 'stair' and self.obj in fp.stairs:
            fp.stairs.remove(self.obj)
        
        logger.info(f"Removed {self.obj_type}: {self._description}")
    
    def undo(self, floor_plan=None):
        """Add the object back."""
        fp = floor_plan or self.floor_plan
        if self.obj_type == 'furniture':
            fp.add_furniture(self.obj)
        elif self.obj_type == 'fixture':
            fp.add_fixture(self.obj)
        elif self.obj_type == 'stair':
            fp.add_stair(self.obj)
        
        logger.info(f"Restored {self.obj_type}: {self._description}")
    
    def description(self):
        """Get command description for display."""
        return self._description
