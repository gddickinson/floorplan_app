"""
Copy/paste functionality for floor plan objects.

Provides clipboard-like functionality for duplicating walls, openings,
furniture, fixtures, stairs, and rooms.
"""

import logging
from typing import Optional, Any, List
from copy import deepcopy
import uuid

from core import (
    Wall, Opening, Room, Furniture, Fixture, Stair, Point
)

logger = logging.getLogger(__name__)


class Clipboard:
    """
    Clipboard for copying and pasting floor plan objects.
    
    Supports copying single or multiple objects and pasting them
    at new locations with optional offset.
    """
    
    def __init__(self):
        self.objects: List[Any] = []
        self.object_types: List[str] = []
        logger.info("Clipboard initialized")
    
    def copy(self, obj: Any):
        """
        Copy an object to the clipboard.
        
        Args:
            obj: Object to copy (Wall, Opening, Room, Furniture, etc.)
        """
        self.objects = [obj]
        self.object_types = [self._get_object_type(obj)]
        logger.info(f"Copied {self.object_types[0]}: {getattr(obj, 'id', 'unknown')}")
    
    def copy_multiple(self, objects: List[Any]):
        """
        Copy multiple objects to the clipboard.
        
        Args:
            objects: List of objects to copy
        """
        self.objects = objects
        self.object_types = [self._get_object_type(obj) for obj in objects]
        logger.info(f"Copied {len(objects)} objects")
    
    def paste(self, offset: Point = Point(0, 0)) -> List[Any]:
        """
        Paste objects from clipboard with optional offset.
        
        Args:
            offset: Offset to apply to pasted objects
            
        Returns:
            List of new objects
        """
        if not self.objects:
            logger.warning("Nothing to paste")
            return []
        
        new_objects = []
        
        for obj, obj_type in zip(self.objects, self.object_types):
            new_obj = self._duplicate_object(obj, offset)
            new_objects.append(new_obj)
        
        logger.info(f"Pasted {len(new_objects)} objects")
        return new_objects
    
    def _get_object_type(self, obj: Any) -> str:
        """Get the type name of an object."""
        if isinstance(obj, Wall):
            return "wall"
        elif isinstance(obj, Opening):
            return "opening"
        elif isinstance(obj, Room):
            return "room"
        elif isinstance(obj, Furniture):
            return "furniture"
        elif isinstance(obj, Fixture):
            return "fixture"
        elif isinstance(obj, Stair):
            return "stair"
        else:
            return "unknown"
    
    def _duplicate_object(self, obj: Any, offset: Point) -> Any:
        """
        Duplicate an object with new ID and offset position.
        
        Args:
            obj: Object to duplicate
            offset: Offset to apply
            
        Returns:
            New object
        """
        # Deep copy the object
        new_obj = deepcopy(obj)
        
        # Generate new ID
        new_obj.id = str(uuid.uuid4())
        
        # Apply offset based on object type
        if isinstance(new_obj, Wall):
            new_obj.start.x += offset.x
            new_obj.start.y += offset.y
            new_obj.end.x += offset.x
            new_obj.end.y += offset.y
        
        elif isinstance(new_obj, (Furniture, Fixture)):
            new_obj.position.x += offset.x
            new_obj.position.y += offset.y
        
        elif isinstance(new_obj, Stair):
            new_obj.start.x += offset.x
            new_obj.start.y += offset.y
            new_obj.end.x += offset.x
            new_obj.end.y += offset.y
        
        elif isinstance(new_obj, Opening):
            # Openings reference walls, so we can't directly paste them
            # They need special handling
            pass
        
        elif isinstance(new_obj, Room):
            # Rooms reference walls by ID, so we can't directly paste them
            # They need special handling
            new_obj.name = f"{new_obj.name} (Copy)"
        
        return new_obj
    
    def has_content(self) -> bool:
        """Check if clipboard has content."""
        return len(self.objects) > 0
    
    def clear(self):
        """Clear the clipboard."""
        self.objects.clear()
        self.object_types.clear()
        logger.info("Clipboard cleared")
    
    def get_count(self) -> int:
        """Get number of objects in clipboard."""
        return len(self.objects)
    
    def get_description(self) -> str:
        """Get description of clipboard contents."""
        if not self.objects:
            return "Empty"
        
        if len(self.objects) == 1:
            return f"1 {self.object_types[0]}"
        
        # Count by type
        type_counts = {}
        for obj_type in self.object_types:
            type_counts[obj_type] = type_counts.get(obj_type, 0) + 1
        
        parts = [f"{count} {obj_type}{'s' if count > 1 else ''}" 
                for obj_type, count in type_counts.items()]
        
        return ", ".join(parts)


# Global clipboard instance
_clipboard = Clipboard()


def get_clipboard() -> Clipboard:
    """Get the global clipboard instance."""
    return _clipboard

